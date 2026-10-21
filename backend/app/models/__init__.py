from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class SandboxStatus(str, enum.Enum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    TERMINATED = "terminated"


class PolicyAction(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action: Mapped[PolicyAction] = mapped_column(
        SQLEnum(PolicyAction), nullable=False, default=PolicyAction.DENY
    )
    # Network policy fields
    destination_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    destination_port: Mapped[Optional[int]] = mapped_column(nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Process policy fields
    command_pattern: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Metadata
    priority: Mapped[int] = mapped_column(default=0)
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_policy_rules_enabled_priority", "enabled", "priority"),
    )


class Sandbox(Base):
    __tablename__ = "sandboxes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sandbox_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    status: Mapped[SandboxStatus] = mapped_column(
        SQLEnum(SandboxStatus), default=SandboxStatus.CREATING, nullable=False
    )
    policy_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("policy_rules.id"), nullable=True
    )
    config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON config
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    policy: Mapped[Optional["PolicyRule"]] = relationship("PolicyRule", lazy="selectin")

    __table_args__ = (
        Index("ix_sandboxes_status", "status"),
    )


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sandbox_id: Mapped[int] = mapped_column(ForeignKey("sandboxes.id"), nullable=False)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    args: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    span_id: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    sandbox: Mapped["Sandbox"] = relationship("Sandbox", lazy="selectin")

    __table_args__ = (
        Index("ix_executions_sandbox_started", "sandbox_id", "started_at"),
        Index("ix_executions_trace_id", "trace_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sandbox_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    policy_id: Mapped[Optional[int]] = mapped_column(ForeignKey("policy_rules.id"), nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    trace_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    policy: Mapped[Optional["PolicyRule"]] = relationship("PolicyRule", lazy="selectin")

    __table_args__ = (
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_sandbox_timestamp", "sandbox_id", "timestamp"),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    roles: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # JSON array
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)