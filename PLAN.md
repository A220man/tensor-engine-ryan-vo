# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

project-skeleton

## Roadmap

### project-skeleton — Project skeleton with FastAPI backend and React frontend

Status: done

Acceptance:
- Backend FastAPI app runs with health endpoint
- Frontend Vite+React+TS builds and serves
- Docker compose with backend, frontend, Keycloak
- Basic CI workflow runs backend/frontend tests
- README with install/run/test steps

Implementation: `backend/app/main.py`, `backend/app/api/routes.py`, `backend/app/api/schemas.py`, `backend/app/services/sandbox.py`, `backend/app/services/policy.py`, `backend/app/models/__init__.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/security.py`, `backend/app/core/telemetry.py`, `frontend/src/App.tsx`, `frontend/src/components/SandboxList.tsx`, `frontend/src/components/SandboxDetail.tsx`, `frontend/src/components/PolicyList.tsx`, `frontend/src/components/AuditLog.tsx`, `frontend/src/components/CreateSandboxModal.tsx`, `frontend/src/api/client.ts`, `frontend/src/types/api.ts`, `docker-compose.yaml`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_health.py`, `backend/tests/test_sandboxes.py`, `backend/tests/test_policies.py`, `backend/tests/test_executions.py`, `backend/tests/test_audit.py`, `backend/tests/test_policy_service.py`, `backend/tests/test_sandbox_service.py`, `backend/tests/conftest.py`, `frontend/src/App.test.tsx`, `frontend/src/test-setup.ts`

### agent-sandbox-execution — Agent sandbox execution workflow

Status: in_progress

Acceptance:
- Create sandbox with policy
- Execute code in sandbox
- Retrieve execution results/logs
- Sandbox lifecycle management

Implementation: `backend/app/services/sandbox.py`, `backend/app/api/routes.py`, `backend/app/models/__init__.py`, `backend/app/api/schemas.py`

Tests: `backend/tests/test_sandbox_service.py`, `backend/tests/test_sandboxes.py`, `backend/tests/test_executions.py`

### policy-evaluation — Policy evaluation and enforcement

Status: planned

Acceptance:
- Define network/egress policies
- Evaluate connection requests against policies
- Audit log of policy decisions

### observability-tracing — Observability with trace correlation

Status: planned

Acceptance:
- OTel trace export from supervisor
- OCSF events with trace.uid correlation
- Trace profile schema vendored

### auth-oidc-keycloak — OIDC authentication with Keycloak

Status: planned

Acceptance:
- Keycloak realm import
- Backend session management with HttpOnly cookies
- Frontend PKCE login flow
- Role-based access control

