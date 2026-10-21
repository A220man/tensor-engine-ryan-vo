# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-21

### Added
- Sandbox lifecycle management (create, start, stop, terminate)
- Policy engine with network egress and process execution rules
- Command execution with policy evaluation (allow/deny)
- Audit logging with trace correlation (trace_id, span_id)
- OIDC authentication via Keycloak (admin/operator/analyst roles)
- OpenTelemetry instrumentation for FastAPI and SQLAlchemy
- Docker Compose deployment with Keycloak, PostgreSQL, OTel Collector
- CI/CD pipeline (GitHub Actions) with backend and frontend tests
- React + TypeScript + Vite frontend with sandbox/policy/audit UIs
- Health check endpoint
- Comprehensive test suite (12+ backend tests, 3+ frontend tests)

### Security
- Default-deny network policy posture
- HttpOnly SameSite=Strict session cookies
- CSRF protection on state-changing operations
- PKCE for OIDC authorization code flow
- Demo mode restricted to localhost

### Documentation
- README with architecture diagram, API reference, deployment guide
- MIT LICENSE
- CHANGELOG
- .env.example with all configuration options