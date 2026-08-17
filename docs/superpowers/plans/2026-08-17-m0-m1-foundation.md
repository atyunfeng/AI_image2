# M0-M1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the M0 benchmark framework and an M1 end-to-end commerce image workbench slice that can create a SKU, upload references, configure an encrypted model provider, run a durable mock generation, review one output, and export it with full provenance.

**Architecture:** Use a pnpm monorepo with a Next.js web app and one Python package that serves both the FastAPI process and the background worker. PostgreSQL is authoritative for domain and job state, Redis only wakes workers, and MinIO provides an S3-compatible asset store. Provider code sits behind capability contracts so real APIs and ComfyUI can be added without changing workflow code.

**Tech Stack:** Node.js 24, pnpm 11, Next.js 16, React 19, TypeScript 5.9, Python 3.13 managed by uv, FastAPI 0.128, Pydantic 2.13, SQLAlchemy 2.0, PostgreSQL 17, Redis 8, MinIO/S3, pytest 8, Vitest, Playwright, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-08-17-ecommerce-ai-image-platform-design.md`

## Global Constraints

- This plan covers M0 and M1 only; M2-M5 require separate implementation plans.
- Strict product mode is the default and generated views without matching references are not exportable.
- PostgreSQL stores authoritative task state; Redis is a delivery hint, never the only task record.
- API keys use server-side AES-GCM encryption and never return to the browser after creation.
- Every generated or edited asset is immutable and records parentage, hashes, provider, model, parameters, cost, and review history.
- ComfyUI is an optional provider and must not own catalog, permission, workflow, review, or asset state.
- Product specifications and promotion copy use deterministic text layers; M1 does not ask image models to render authoritative copy.
- Use targeted tests per task; run the full M0-M1 verification only in the final integration task.
- Real product benchmark data and real provider keys are external inputs. Do not fabricate them; the benchmark validator must report exactly what is missing.
- Maintain `THIRD_PARTY.md` before copying upstream source code; M0-M1 uses project APIs and ideas but does not vendor upstream source.

## File and Responsibility Map

```text
/
├── apps/web/                         # Next.js operator UI only
│   ├── src/app/                      # Routes and server-rendered shells
│   ├── src/components/               # Focused reusable UI components
│   ├── src/features/                 # Auth, catalog, models, batches, review
│   └── src/lib/                      # API client and browser session helpers
├── backend/
│   ├── pyproject.toml                # Python package and tool configuration
│   ├── alembic/                      # Database migrations
│   ├── src/aiimage/
│   │   ├── api/                      # FastAPI composition and HTTP routers
│   │   ├── auth/                     # Passwords, JWT, RBAC
│   │   ├── catalog/                  # SKU, references, truth anchors
│   │   ├── assets/                   # S3 storage and immutable asset metadata
│   │   ├── models/                   # Provider configuration and model capabilities
│   │   ├── providers/                # Provider contracts and mock provider
│   │   ├── workflow/                 # Batch compiler, state machine, leases, queue hints
│   │   ├── review/                   # Review decisions and export eligibility
│   │   ├── export/                   # Manifest and ZIP export
│   │   ├── benchmark/                # M0 manifest validation and result aggregation
│   │   ├── audit/                    # Security-sensitive event recording
│   │   └── worker/                   # Durable step executor
│   └── tests/                        # Unit, API, worker, recovery, and contract tests
├── benchmarks/                       # User-supplied manifest and product asset convention
├── infra/                            # Container support files
├── scripts/                          # Repeatable local verification commands
├── docker-compose.yml                # PostgreSQL, Redis, MinIO, API, worker, web
├── .env.example                      # Safe local defaults and required secret names
└── THIRD_PARTY.md                    # Upstream provenance register
```

---

### Task 1: Repository and Runtime Foundation

**Files:**
- Create: `.gitignore`
- Create: `.editorconfig`
- Create: `.env.example`
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `.python-version`
- Create: `apps/web/**`
- Create: `backend/pyproject.toml`
- Create: `backend/src/aiimage/__init__.py`
- Create: `backend/tests/test_package.py`
- Create: `docker-compose.yml`
- Create: `THIRD_PARTY.md`

**Interfaces:**
- Consumes: Approved design and this implementation plan.
- Produces: `pnpm test`, `uv run --project backend pytest`, Docker service names `postgres`, `redis`, `minio`, and a Git feature branch named `feat/m0-m1-foundation`.

- [ ] **Step 1: Initialize Git without losing the approved documents**

Run:

```bash
git init -b main
git add docs
git commit -m "docs: add approved ai image platform design"
git switch -c feat/m0-m1-foundation
```

Expected: `git status --short --branch` reports `## feat/m0-m1-foundation` with no changes.

- [ ] **Step 2: Write the failing backend package smoke test**

```python
# backend/tests/test_package.py
from aiimage import __version__


def test_package_version() -> None:
    assert __version__ == "0.1.0"
```

- [ ] **Step 3: Create the root workspace and Python package**

```json
// package.json
{
  "name": "aiimage-platform",
  "private": true,
  "packageManager": "pnpm@11.19.0",
  "scripts": {
    "dev:web": "pnpm --dir apps/web dev",
    "test:web": "pnpm --dir apps/web test",
    "test:e2e": "pnpm --dir apps/web test:e2e",
    "lint:web": "pnpm --dir apps/web lint"
  }
}
```

```toml
# backend/pyproject.toml
[project]
name = "aiimage"
version = "0.1.0"
requires-python = ">=3.13,<3.14"
dependencies = [
  "fastapi==0.128.8",
  "pydantic==2.13.4",
  "pydantic-settings>=2.10,<3",
  "sqlalchemy[asyncio]==2.0.52",
  "asyncpg>=0.30,<1",
  "alembic>=1.16,<2",
  "redis>=6,<7",
  "boto3>=1.40,<2",
  "cryptography>=45,<46",
  "argon2-cffi>=25,<26",
  "pyjwt>=2.10,<3",
  "httpx>=0.28,<1",
  "python-multipart>=0.0.20,<1",
  "pillow>=11,<12"
]

[dependency-groups]
dev = ["pytest==8.4.2", "pytest-asyncio>=1,<2", "ruff>=0.12,<1"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py313"
```

```python
# backend/src/aiimage/__init__.py
__version__ = "0.1.0"
```

Create the web app with the exact versions resolved into `pnpm-lock.yaml`:

```bash
pnpm dlx create-next-app@16.3.1 apps/web --ts --tailwind --eslint --app --src-dir --use-pnpm --import-alias '@/*' --yes
pnpm --dir apps/web add react@19.2.8 react-dom@19.2.8 zod@4 @tanstack/react-query@5
pnpm --dir apps/web add -D typescript@5.9.3 vitest @testing-library/react @testing-library/jest-dom @playwright/test@1.62.1
uv python pin 3.13
uv sync --project backend --dev
```

Add `"test": "vitest run"` and `"test:e2e": "playwright test"` to `apps/web/package.json`. Set `pnpm-workspace.yaml` to include `apps/*`.

- [ ] **Step 4: Add infrastructure with safe local values**

```dotenv
# .env.example
AIIMAGE_ENV=development
AIIMAGE_DATABASE_URL=postgresql+asyncpg://aiimage:aiimage@localhost:5432/aiimage
AIIMAGE_REDIS_URL=redis://localhost:6379/0
AIIMAGE_S3_ENDPOINT=http://localhost:9000
AIIMAGE_S3_BUCKET=aiimage-assets
AIIMAGE_S3_ACCESS_KEY=aiimage
AIIMAGE_S3_SECRET_KEY=local-development-secret
AIIMAGE_SECRET_KEY_BASE64=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
AIIMAGE_JWT_SECRET=local-development-jwt-secret-change-before-deploy
AIIMAGE_BOOTSTRAP_ADMIN_EMAIL=admin@aiimage.local
AIIMAGE_BOOTSTRAP_ADMIN_PASSWORD=LocalOnly-ChangeMe-2026
```

`docker-compose.yml` must pin PostgreSQL and Redis majors, expose PostgreSQL `5432`, Redis `6379`, MinIO API `9000`, MinIO console `9001`, API `8000`, and web `3000`. Its infrastructure portion starts with:

```yaml
services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: aiimage
      POSTGRES_USER: aiimage
      POSTGRES_PASSWORD: aiimage
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aiimage -d aiimage"]
      interval: 2s
      timeout: 2s
      retries: 20
    volumes: ["postgres-data:/var/lib/postgresql/data"]
  redis:
    image: redis:8-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 2s
      timeout: 2s
      retries: 20
    volumes: ["redis-data:/data"]
  minio:
    image: minio/minio:RELEASE.2025-04-22T22-12-26Z@sha256:a1ea29fa28355559ef137d71fc570e508a214ec84ff8083e39bc5428980b015e
    command: server /data --console-address :9001
    environment:
      MINIO_ROOT_USER: aiimage
      MINIO_ROOT_PASSWORD: local-development-secret
    ports: ["9000:9000", "9001:9001"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 2s
      timeout: 2s
      retries: 20
    volumes: ["minio-data:/data"]
volumes:
  postgres-data:
  redis-data:
  minio-data:
```

- [ ] **Step 5: Verify and commit the foundation**

Run:

```bash
uv run --project backend pytest backend/tests/test_package.py -v
pnpm --dir apps/web lint
docker compose config --quiet
```

Expected: one backend test passes, Next.js lint exits 0, and Compose configuration is valid.

```bash
git add .
git commit -m "chore: scaffold ai image platform workspace"
```

---

### Task 2: Configuration, Database, and Health API

**Files:**
- Create: `backend/src/aiimage/config.py`
- Create: `backend/src/aiimage/db.py`
- Create: `backend/src/aiimage/api/main.py`
- Create: `backend/src/aiimage/api/dependencies.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/tests/api/test_health.py`
- Create: `backend/tests/conftest.py`

**Interfaces:**
- Consumes: Environment variables defined in `.env.example`.
- Produces: `Settings`, `get_session()`, `create_app()`, and `GET /api/v1/health` returning `{"status":"ok"}`.

- [ ] **Step 1: Write a failing health test**

```python
from fastapi.testclient import TestClient

from aiimage.api.main import create_app


def test_health() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the test and confirm import failure**

Run: `uv run --project backend pytest backend/tests/api/test_health.py -v`

Expected: FAIL because `aiimage.api.main` does not exist.

- [ ] **Step 3: Implement settings, session ownership, and app composition**

```python
# backend/src/aiimage/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIIMAGE_", env_file=".env", extra="ignore")
    env: str = "development"
    database_url: str
    redis_url: str
    s3_endpoint: str
    s3_bucket: str
    s3_access_key: str
    s3_secret_key: str
    secret_key_base64: str
    jwt_secret: str
    bootstrap_admin_email: str
    bootstrap_admin_password: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

```python
# backend/src/aiimage/api/main.py
from fastapi import APIRouter, FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="AI Image Platform", version="0.1.0")
    router = APIRouter(prefix="/api/v1")

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    return app


app = create_app()
```

Add an async SQLAlchemy engine, an `async_sessionmaker`, a `Base` declarative class, and a FastAPI dependency that yields one `AsyncSession` and rolls back on exceptions. Configure Alembic to import `Base.metadata`.

- [ ] **Step 4: Verify API and migration bootstrap**

Run:

```bash
docker compose up -d postgres redis minio --wait
uv run --project backend pytest backend/tests/api/test_health.py -v
uv run --project backend alembic -c backend/alembic.ini current
```

Expected: health test passes; Alembic connects and reports no revisions without raising.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add backend configuration and health api"
```

---

### Task 3: Authentication, RBAC, and Audit Events

**Files:**
- Create: `backend/src/aiimage/auth/models.py`
- Create: `backend/src/aiimage/auth/schemas.py`
- Create: `backend/src/aiimage/auth/service.py`
- Create: `backend/src/aiimage/auth/router.py`
- Create: `backend/src/aiimage/auth/dependencies.py`
- Create: `backend/src/aiimage/audit/models.py`
- Create: `backend/src/aiimage/audit/service.py`
- Create: `backend/alembic/versions/0001_identity_audit.py`
- Create: `backend/tests/auth/test_auth_api.py`
- Modify: `backend/src/aiimage/api/main.py`

**Interfaces:**
- Consumes: `AsyncSession`, `Settings.jwt_secret`, and bootstrap admin settings.
- Produces: `Role`, `User`, `AuditEvent`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `require_roles(*roles)`.

- [ ] **Step 1: Write failing login and authorization tests**

```python
def test_login_returns_bearer_token(client, bootstrap_admin) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@aiimage.local", "password": "LocalOnly-ChangeMe-2026"},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_me_rejects_anonymous(client) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
```

- [ ] **Step 2: Verify the endpoints do not exist**

Run: `uv run --project backend pytest backend/tests/auth/test_auth_api.py -v`

Expected: FAIL with 404 responses.

- [ ] **Step 3: Implement explicit role and token contracts**

```python
class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    DESIGNER = "designer"
    REVIEWER = "reviewer"


class TokenPayload(BaseModel):
    sub: UUID
    roles: set[Role]
    exp: datetime
```

Hash passwords with Argon2id. Sign access tokens with HS256 for 8 hours. `require_roles()` must read the authenticated user from a dependency and return 403 when the user's role set has no intersection with the required roles. Login success and failure, user creation, role changes, and bootstrap admin creation must write `AuditEvent` rows without password or token values.

- [ ] **Step 4: Run migrations and targeted tests**

Run:

```bash
uv run --project backend alembic -c backend/alembic.ini upgrade head
uv run --project backend pytest backend/tests/auth -v
```

Expected: migrations succeed; authentication tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add authentication roles and audit events"
```

---

### Task 4: Immutable Assets and Product Catalog

**Files:**
- Create: `backend/src/aiimage/assets/models.py`
- Create: `backend/src/aiimage/assets/storage.py`
- Create: `backend/src/aiimage/assets/service.py`
- Create: `backend/src/aiimage/catalog/models.py`
- Create: `backend/src/aiimage/catalog/schemas.py`
- Create: `backend/src/aiimage/catalog/service.py`
- Create: `backend/src/aiimage/catalog/router.py`
- Create: `backend/alembic/versions/0002_assets_catalog.py`
- Create: `backend/tests/catalog/test_catalog_api.py`
- Create: `backend/tests/assets/test_storage.py`
- Modify: `backend/src/aiimage/api/main.py`

**Interfaces:**
- Consumes: Authenticated `User`, `AsyncSession`, and S3 settings.
- Produces: `Asset`, `Product`, `ProductReference`, `TruthAnchor`, `ObjectStore.put()`, SKU CRUD endpoints, and reference upload endpoint.

- [ ] **Step 1: Write failing catalog and immutability tests**

```python
def test_create_product_and_upload_reference(admin_client, png_bytes) -> None:
    product = admin_client.post(
        "/api/v1/products",
        json={"sku": "DRESS-001", "name": "Floral dress", "category": "apparel"},
    ).json()
    response = admin_client.post(
        f"/api/v1/products/{product['id']}/references",
        files={"file": ("front.png", png_bytes, "image/png")},
        data={"view": "front"},
    )
    assert response.status_code == 201
    assert response.json()["sha256"]


def test_asset_content_is_not_updated(session, stored_asset) -> None:
    with pytest.raises(ImmutableAssetError):
        stored_asset.replace_content(b"new")
```

- [ ] **Step 2: Verify failures**

Run: `uv run --project backend pytest backend/tests/catalog backend/tests/assets -v`

Expected: FAIL because catalog and asset modules do not exist.

- [ ] **Step 3: Implement models and storage boundary**

```python
class ReferenceView(str, Enum):
    FRONT = "front"
    SIDE = "side"
    BACK = "back"
    DETAIL = "detail"
    LOGO = "logo"


@dataclass(frozen=True)
class StoredObject:
    object_key: str
    sha256: str
    size_bytes: int
    mime_type: str


class ObjectStore(Protocol):
    async def put(self, *, content: bytes, mime_type: str) -> StoredObject:
        raise NotImplementedError

    async def get(self, *, object_key: str) -> bytes:
        raise NotImplementedError
```

The concrete S3 store computes SHA-256 before upload, keys objects as `sha256/<first-two>/<hash>`, rejects unsupported MIME types, and never overwrites an existing hash key. Product SKU values are unique and case-normalized. Truth anchors are versioned JSON documents with an author and creation timestamp.

- [ ] **Step 4: Run migration and targeted tests**

Run:

```bash
uv run --project backend alembic -c backend/alembic.ini upgrade head
uv run --project backend pytest backend/tests/catalog backend/tests/assets -v
```

Expected: all asset and catalog tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add immutable assets and product catalog"
```

---

### Task 5: Encrypted Model Registry and Provider Contract

**Files:**
- Create: `backend/src/aiimage/models/domain.py`
- Create: `backend/src/aiimage/models/models.py`
- Create: `backend/src/aiimage/models/schemas.py`
- Create: `backend/src/aiimage/models/secrets.py`
- Create: `backend/src/aiimage/models/service.py`
- Create: `backend/src/aiimage/models/router.py`
- Create: `backend/src/aiimage/providers/base.py`
- Create: `backend/src/aiimage/providers/mock.py`
- Create: `backend/src/aiimage/providers/generic_http.py`
- Create: `backend/src/aiimage/providers/registry.py`
- Create: `backend/alembic/versions/0003_model_registry.py`
- Create: `backend/tests/models/test_model_registry.py`
- Create: `backend/tests/providers/test_provider_contract.py`
- Modify: `backend/src/aiimage/api/main.py`

**Interfaces:**
- Consumes: AES key from `Settings.secret_key_base64`, S3 asset service, and admin RBAC.
- Produces: `Capability`, `GenerationRequest`, `GenerationResult`, `ProviderAdapter`, model configuration endpoints, and `ProviderRegistry.get(model_config)`.

- [ ] **Step 1: Write failing secret and provider contract tests**

```python
def test_api_key_is_write_only(admin_client) -> None:
    response = admin_client.post(
        "/api/v1/models",
        json={
            "name": "Mock Image",
            "provider": "mock",
            "model_id": "mock-v1",
            "api_key": "secret-provider-key",
            "capabilities": ["reference_to_image"],
        },
    )
    assert response.status_code == 201
    assert "secret-provider-key" not in response.text
    assert response.json()["key_suffix"] == "-key"


@pytest.mark.asyncio
async def test_mock_provider_is_deterministic(mock_provider, generation_request) -> None:
    first = await mock_provider.generate(generation_request)
    second = await mock_provider.generate(generation_request)
    assert first.content_sha256 == second.content_sha256
```

- [ ] **Step 2: Verify failures**

Run: `uv run --project backend pytest backend/tests/models backend/tests/providers -v`

Expected: FAIL because registry types are undefined.

- [ ] **Step 3: Implement stable provider interfaces**

```python
class Capability(str, Enum):
    TEXT_TO_IMAGE = "text_to_image"
    REFERENCE_TO_IMAGE = "reference_to_image"
    MULTI_REFERENCE_TO_IMAGE = "multi_reference_to_image"
    INPAINT = "inpaint"
    OUTPAINT = "outpaint"
    VIRTUAL_TRY_ON = "virtual_try_on"
    REMOVE_BACKGROUND = "remove_background"
    SEGMENT = "segment"
    UPSCALE = "upscale"
    VISION_ANALYZE = "vision_analyze"
    QUALITY_INSPECT = "quality_inspect"


class GenerationRequest(BaseModel):
    idempotency_key: str
    capability: Capability
    prompt: str
    reference_asset_ids: list[UUID]
    width: int
    height: int
    parameters: dict[str, JsonValue]


class GenerationResult(BaseModel):
    content: bytes
    mime_type: Literal["image/png", "image/jpeg", "image/webp"]
    content_sha256: str
    provider_request_id: str
    estimated_cost_minor: int


class ProviderAdapter(Protocol):
    async def test_connection(self) -> None:
        raise NotImplementedError

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        raise NotImplementedError
```

Encrypt keys with a fresh 12-byte nonce per save using AES-GCM and authenticated data `provider:model_id`. Responses expose only `has_key` and the last four characters. The mock provider renders a deterministic labeled PNG from the request hash; it must not call external services.

The generic HTTP adapter sends `Authorization: Bearer <decrypted-key>` and posts `{model, prompt, width, height, reference_images, parameters}` to the configured Base URL plus `/generate`. It accepts only `{image_base64, request_id, cost_minor}` and rejects non-image MIME types, oversized decoded payloads, missing request IDs, and malformed base64. Test it with `httpx.MockTransport`; no network call belongs in the default suite.

- [ ] **Step 4: Migrate and verify**

Run:

```bash
uv run --project backend alembic -c backend/alembic.ini upgrade head
uv run --project backend pytest backend/tests/models backend/tests/providers -v
```

Expected: model secrets never appear in responses, mock contract tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add encrypted model registry and provider contract"
```

---

### Task 6: Durable Batch State Machine and Queue Hints

**Files:**
- Create: `backend/src/aiimage/workflow/models.py`
- Create: `backend/src/aiimage/workflow/schemas.py`
- Create: `backend/src/aiimage/workflow/state.py`
- Create: `backend/src/aiimage/workflow/service.py`
- Create: `backend/src/aiimage/workflow/queue.py`
- Create: `backend/src/aiimage/workflow/router.py`
- Create: `backend/alembic/versions/0004_workflow.py`
- Create: `backend/tests/workflow/test_state_machine.py`
- Create: `backend/tests/workflow/test_batch_api.py`
- Modify: `backend/src/aiimage/api/main.py`

**Interfaces:**
- Consumes: Product, model configuration, product references, Redis URL, and authenticated operator.
- Produces: `BatchStatus`, `StepStatus`, `transition_batch()`, `QueueHints.publish(step_id)`, and batch create/list/detail/retry endpoints.

- [ ] **Step 1: Write failing state transition tests**

```python
@pytest.mark.parametrize(
    ("source", "target"),
    [
        (BatchStatus.DRAFT, BatchStatus.READY),
        (BatchStatus.READY, BatchStatus.QUEUED),
        (BatchStatus.QUEUED, BatchStatus.RUNNING),
        (BatchStatus.RUNNING, BatchStatus.QA_PENDING),
    ],
)
def test_valid_batch_transitions(source, target) -> None:
    assert transition_batch(source, target) is target


def test_approved_cannot_return_to_running() -> None:
    with pytest.raises(InvalidTransition):
        transition_batch(BatchStatus.APPROVED, BatchStatus.RUNNING)
```

- [ ] **Step 2: Verify failure**

Run: `uv run --project backend pytest backend/tests/workflow/test_state_machine.py -v`

Expected: FAIL because workflow status types are undefined.

- [ ] **Step 3: Implement states, idempotency, and creation transaction**

Define the exact batch states from the spec plus `FAILED`, `CANCELED`, and `RETRY_QUEUED`. A generation step has a unique `idempotency_key`, `lease_owner`, `lease_expires_at`, attempt count, input snapshot JSON, provider request ID, output asset ID, and error classification.

`CreateBatchRequest` includes `requested_view: ReferenceView` and `mode: Literal["strict", "creative"]` with `strict` as the default. `create_batch()` must validate that the model supports `reference_to_image`; in strict mode it rejects side or back views without a matching product reference. It snapshots selected references and truth anchor version, inserts batch and step in one transaction, transitions through READY to QUEUED, commits, then pushes the step UUID to Redis. If Redis is unavailable, return 201 because PostgreSQL already owns the queued step; the worker recovery scan will find it.

- [ ] **Step 4: Run migration and targeted workflow tests**

Run:

```bash
uv run --project backend alembic -c backend/alembic.ini upgrade head
uv run --project backend pytest backend/tests/workflow -v
```

Expected: valid transitions pass, invalid transitions raise, and batch creation survives a simulated Redis publish failure.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add durable generation workflow"
```

---

### Task 7: Worker Execution, Leases, and Recovery

**Files:**
- Create: `backend/src/aiimage/worker/main.py`
- Create: `backend/src/aiimage/worker/executor.py`
- Create: `backend/src/aiimage/worker/recovery.py`
- Create: `backend/tests/worker/test_executor.py`
- Create: `backend/tests/worker/test_recovery.py`

**Interfaces:**
- Consumes: Queued `GenerationStep`, `ProviderRegistry`, asset service, queue hints, and SQLAlchemy session factory.
- Produces: `execute_step(step_id, worker_id)`, `recover_expired_leases(now)`, stored output assets, and terminal step/batch states.

- [ ] **Step 1: Write failing execution and duplicate-delivery tests**

```python
@pytest.mark.asyncio
async def test_worker_stores_output_and_advances_batch(worker_context, queued_step) -> None:
    await execute_step(queued_step.id, worker_id="test-worker", context=worker_context)
    await worker_context.session.refresh(queued_step)
    assert queued_step.status is StepStatus.SUCCEEDED
    assert queued_step.output_asset_id is not None


@pytest.mark.asyncio
async def test_duplicate_delivery_does_not_call_provider_twice(worker_context, succeeded_step) -> None:
    await execute_step(succeeded_step.id, worker_id="test-worker", context=worker_context)
    assert worker_context.mock_provider.generate_calls == 0
```

- [ ] **Step 2: Verify failures**

Run: `uv run --project backend pytest backend/tests/worker -v`

Expected: FAIL because executor functions do not exist.

- [ ] **Step 3: Implement lease-first execution**

Acquire the step with a SQLAlchemy `with_for_update(skip_locked=True)` query. Only `QUEUED`, `RETRY_QUEUED`, or an expired `RUNNING` step can be leased. Set a five-minute lease and commit before calling the provider. Persist provider request ID, output hash, immutable asset, cost, and terminal status in a second transaction. A duplicate delivery for `SUCCEEDED`, `FAILED`, or `CANCELED` returns without calling the provider.

After a provider result is stored, run M1 structural QA: decode the image, verify declared MIME type, verify width and height are positive, and recheck SHA-256. Transition the batch from `RUNNING` to `QA_PENDING`, then to `REVIEW_PENDING` when structural QA passes. A structural failure sets the step and batch to `FAILED` with a stable error classification.

Recovery scans PostgreSQL every 30 seconds. For expired mock work it safely requeues. Real asynchronous providers added later must implement a status query before any retry to avoid duplicate cost.

- [ ] **Step 4: Run targeted worker and recovery tests**

Run: `uv run --project backend pytest backend/tests/worker -v`

Expected: worker execution, duplicate delivery, expired lease, and Redis-loss recovery tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: execute and recover generation steps"
```

---

### Task 8: Review Decisions and Provenance Export

**Files:**
- Create: `backend/src/aiimage/review/models.py`
- Create: `backend/src/aiimage/review/schemas.py`
- Create: `backend/src/aiimage/review/service.py`
- Create: `backend/src/aiimage/review/router.py`
- Create: `backend/src/aiimage/export/service.py`
- Create: `backend/src/aiimage/export/router.py`
- Create: `backend/alembic/versions/0005_review.py`
- Create: `backend/tests/review/test_review_api.py`
- Create: `backend/tests/export/test_export.py`
- Modify: `backend/src/aiimage/api/main.py`

**Interfaces:**
- Consumes: Succeeded output assets, reviewer RBAC, batch input snapshot, and object store.
- Produces: `ReviewDecision`, approve/reject endpoints, `ExportManifest`, and `GET /api/v1/batches/{id}/export.zip`.

- [ ] **Step 1: Write failing review and export-gate tests**

```python
def test_rejected_batch_cannot_export(reviewer_client, rejected_batch) -> None:
    response = reviewer_client.get(f"/api/v1/batches/{rejected_batch.id}/export.zip")
    assert response.status_code == 409


def test_approved_export_contains_manifest(reviewer_client, approved_batch) -> None:
    response = reviewer_client.get(f"/api/v1/batches/{approved_batch.id}/export.zip")
    assert response.status_code == 200
    with ZipFile(BytesIO(response.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    assert manifest["batch_id"] == str(approved_batch.id)
    assert manifest["assets"][0]["sha256"]
```

- [ ] **Step 2: Verify failure**

Run: `uv run --project backend pytest backend/tests/review backend/tests/export -v`

Expected: FAIL because review and export routes do not exist.

- [ ] **Step 3: Implement immutable review history and export manifest**

Review decisions are append-only. Approve requires a succeeded output asset. Reject requires one of `product_drift`, `color_error`, `text_error`, `model_anatomy`, `platform_rule`, or `other`; `other` requires a note. Export only the latest approved asset version and include product ID/SKU, input asset hashes, truth anchor version, provider, model, parameters, cost, reviewer, decision time, and output hash in `manifest.json`.

- [ ] **Step 4: Run migrations and tests**

Run:

```bash
uv run --project backend alembic -c backend/alembic.ini upgrade head
uv run --project backend pytest backend/tests/review backend/tests/export -v
```

Expected: review gates and provenance export tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add review decisions and provenance export"
```

---

### Task 9: Web Authentication and Operator Shell

**Files:**
- Create: `apps/web/src/lib/api-client.ts`
- Create: `apps/web/src/lib/session.ts`
- Create: `apps/web/src/features/auth/login-form.tsx`
- Create: `apps/web/src/components/app-shell.tsx`
- Create: `apps/web/src/app/login/page.tsx`
- Create: `apps/web/src/app/(authenticated)/layout.tsx`
- Create: `apps/web/src/app/(authenticated)/page.tsx`
- Create: `apps/web/src/features/auth/login-form.test.tsx`

**Interfaces:**
- Consumes: `POST /api/v1/auth/login`, `GET /api/v1/auth/me`.
- Produces: `apiFetch<T>()`, HTTP-only session cookie handling, login page, protected shell, and dashboard route.

- [ ] **Step 1: Write a failing login form test**

```tsx
it("submits email and password and redirects to the dashboard", async () => {
  render(<LoginForm login={loginSpy} />);
  await userEvent.type(screen.getByLabelText("邮箱"), "admin@aiimage.local");
  await userEvent.type(screen.getByLabelText("密码"), "LocalOnly-ChangeMe-2026");
  await userEvent.click(screen.getByRole("button", { name: "登录" }));
  expect(loginSpy).toHaveBeenCalledWith({
    email: "admin@aiimage.local",
    password: "LocalOnly-ChangeMe-2026",
  });
});
```

- [ ] **Step 2: Run and confirm failure**

Run: `pnpm --dir apps/web test -- login-form.test.tsx`

Expected: FAIL because `LoginForm` does not exist.

- [ ] **Step 3: Implement secure browser session and shell**

Use a Next.js server action to call the backend login endpoint and set the bearer token in an HTTP-only, same-site strict cookie. Browser components call Next.js route handlers, not the FastAPI origin directly. The authenticated layout validates `/auth/me` server-side and redirects anonymous users to `/login`.

The shell navigation contains only Dashboard, Products, Models, Batches, and Review for M1. Do not add disabled M2-M5 navigation.

- [ ] **Step 4: Verify web unit tests and lint**

Run:

```bash
pnpm --dir apps/web test -- login-form.test.tsx
pnpm --dir apps/web lint
```

Expected: login test and lint pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web
git commit -m "feat: add authenticated operator shell"
```

---

### Task 10: Product and Model Management UI

**Files:**
- Create: `apps/web/src/features/products/product-form.tsx`
- Create: `apps/web/src/features/products/reference-upload.tsx`
- Create: `apps/web/src/features/products/product-list.tsx`
- Create: `apps/web/src/features/models/model-form.tsx`
- Create: `apps/web/src/features/models/model-list.tsx`
- Create: `apps/web/src/app/(authenticated)/products/page.tsx`
- Create: `apps/web/src/app/(authenticated)/products/new/page.tsx`
- Create: `apps/web/src/app/(authenticated)/products/[id]/page.tsx`
- Create: `apps/web/src/app/(authenticated)/models/page.tsx`
- Create: `apps/web/src/features/products/product-form.test.tsx`
- Create: `apps/web/src/features/models/model-form.test.tsx`

**Interfaces:**
- Consumes: Product and model configuration APIs from Tasks 4 and 5.
- Produces: SKU creation, reference upload, product detail, model creation, masked-key display, and connection-test actions.

- [ ] **Step 1: Write failing validation tests**

```tsx
it("requires SKU, name, and category", async () => {
  render(<ProductForm onSubmit={submitSpy} />);
  await userEvent.click(screen.getByRole("button", { name: "创建商品" }));
  expect(screen.getByText("请输入SKU")).toBeVisible();
  expect(submitSpy).not.toHaveBeenCalled();
});


it("never renders the saved provider key", () => {
  render(<ModelList models={[modelWithMaskedKey]} />);
  expect(screen.queryByText("secret-provider-key")).not.toBeInTheDocument();
  expect(screen.getByText("••••-key")).toBeVisible();
});
```

- [ ] **Step 2: Confirm tests fail**

Run: `pnpm --dir apps/web test -- product-form.test.tsx model-form.test.tsx`

Expected: FAIL because forms do not exist.

- [ ] **Step 3: Implement focused forms and API mutations**

Use Zod schemas matching backend fields exactly. Reference upload requires a view selector and previews only the local object URL until the API returns an immutable asset. The model form clears the API key input after a successful save and displays only `key_suffix`. Connection-test results show success, authentication failure, timeout, or provider error without raw response bodies.

- [ ] **Step 4: Verify targeted UI tests and lint**

Run:

```bash
pnpm --dir apps/web test -- product-form.test.tsx model-form.test.tsx
pnpm --dir apps/web lint
```

Expected: form tests and lint pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web
git commit -m "feat: add product and model management ui"
```

---

### Task 11: Batch, Review, and Export UI

**Files:**
- Create: `apps/web/src/features/batches/batch-form.tsx`
- Create: `apps/web/src/features/batches/batch-status.tsx`
- Create: `apps/web/src/features/batches/batch-list.tsx`
- Create: `apps/web/src/features/review/review-panel.tsx`
- Create: `apps/web/src/app/(authenticated)/batches/page.tsx`
- Create: `apps/web/src/app/(authenticated)/batches/new/page.tsx`
- Create: `apps/web/src/app/(authenticated)/batches/[id]/page.tsx`
- Create: `apps/web/src/app/(authenticated)/review/page.tsx`
- Create: `apps/web/src/features/review/review-panel.test.tsx`

**Interfaces:**
- Consumes: Batch, review, and export APIs from Tasks 6-8.
- Produces: Start generation, poll batch status, preview output, approve/reject, retry, and download export actions.

- [ ] **Step 1: Write a failing export-gate UI test**

```tsx
it("disables export until the latest output is approved", () => {
  render(<ReviewPanel batch={reviewPendingBatch} onDecision={decisionSpy} />);
  expect(screen.getByRole("button", { name: "导出" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "通过" })).toBeEnabled();
});
```

- [ ] **Step 2: Confirm failure**

Run: `pnpm --dir apps/web test -- review-panel.test.tsx`

Expected: FAIL because `ReviewPanel` does not exist.

- [ ] **Step 3: Implement the M1 generation workbench**

The batch form selects one product, one `reference_to_image` model, one or more product references, prompt, width, and height. Status polling stops on `REVIEW_PENDING`, `APPROVED`, `REJECTED`, `FAILED`, or `CANCELED`. The review panel displays input references beside output, provider/model/cost/provenance, standardized rejection reasons, and retry. Export appears only for `APPROVED` batches.

- [ ] **Step 4: Verify unit tests and lint**

Run:

```bash
pnpm --dir apps/web test -- review-panel.test.tsx
pnpm --dir apps/web lint
```

Expected: review UI test and lint pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web
git commit -m "feat: add generation review and export ui"
```

---

### Task 12: M0 Benchmark Manifest and Capability Report

**Files:**
- Create: `benchmarks/README.md`
- Create: `benchmarks/manifest.schema.json`
- Create: `backend/src/aiimage/benchmark/models.py`
- Create: `backend/src/aiimage/benchmark/validator.py`
- Create: `backend/src/aiimage/benchmark/runner.py`
- Create: `backend/src/aiimage/benchmark/report.py`
- Create: `backend/src/aiimage/benchmark/cli.py`
- Create: `backend/tests/benchmark/fixtures/valid_manifest.json`
- Create: `backend/tests/benchmark/test_validator.py`
- Create: `backend/tests/benchmark/test_report.py`

**Interfaces:**
- Consumes: User-supplied product images, product references, configured provider adapters, and M0 category requirements.
- Produces: `aiimage-benchmark validate`, `aiimage-benchmark run`, JSONL per-attempt results, and `capability-report.json`.

- [ ] **Step 1: Write failing manifest validation tests**

```python
def test_manifest_requires_ten_skus_per_category(valid_manifest) -> None:
    valid_manifest["products"] = valid_manifest["products"][:29]
    with pytest.raises(BenchmarkValidationError, match="hats requires 10 products; found 9"):
        validate_manifest(valid_manifest)


def test_strict_back_view_requires_back_reference(valid_product) -> None:
    valid_product["requested_views"] = ["front", "back"]
    valid_product["references"] = [{"view": "front", "path": "front.png"}]
    with pytest.raises(BenchmarkValidationError, match="back reference is required"):
        validate_product(valid_product)
```

- [ ] **Step 2: Confirm failure**

Run: `uv run --project backend pytest backend/tests/benchmark -v`

Expected: FAIL because benchmark modules do not exist.

- [ ] **Step 3: Implement manifest and report contracts**

```python
class BenchmarkCategory(str, Enum):
    APPAREL = "apparel"
    SHOES = "shoes"
    HATS = "hats"


class BenchmarkProduct(BaseModel):
    sku: str
    category: BenchmarkCategory
    references: list[BenchmarkReference]
    truth_anchors: dict[str, JsonValue]
    requested_views: list[ReferenceView]


class CapabilityReport(BaseModel):
    provider: str
    model_id: str
    total_attempts: int
    successful_attempts: int
    total_cost_minor: int
    median_latency_ms: int
    results_path: Path
```

The validator requires exactly 30 or more products with at least ten in each category, verifies referenced files exist, validates SHA-256 if supplied, and enforces strict-view references. `run` writes one JSONL record after every attempt so interruption does not lose completed results. It never invents missing assets or keys.

- [ ] **Step 4: Verify benchmark tests and CLI help**

Run:

```bash
uv run --project backend pytest backend/tests/benchmark -v
uv run --project backend aiimage-benchmark --help
```

Expected: tests pass and CLI lists `validate`, `run`, and `report`.

- [ ] **Step 5: Commit**

```bash
git add benchmarks backend
git commit -m "feat: add model capability benchmark framework"
```

---

### Task 13: End-to-End Verification, Security Scan, and Main Merge

**Files:**
- Create: `apps/web/e2e/m1-flow.spec.ts`
- Create: `backend/tests/security/test_secret_redaction.py`
- Create: `backend/tests/recovery/test_redis_outage.py`
- Create: `scripts/verify-m0-m1.sh`
- Create: `README.md`
- Modify: `docker-compose.yml`
- Modify: `THIRD_PARTY.md`

**Interfaces:**
- Consumes: All M0-M1 APIs, UI routes, Compose services, and test commands.
- Produces: One reproducible local verification command, a documented demo login, recovery evidence, and merged `main` when all checks pass.

- [ ] **Step 1: Write the failing browser flow**

```ts
test("operator creates, generates, approves, and exports one SKU", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("邮箱").fill("admin@aiimage.local");
  await page.getByLabel("密码").fill("LocalOnly-ChangeMe-2026");
  await page.getByRole("button", { name: "登录" }).click();
  await page.getByRole("link", { name: "商品" }).click();
  await page.getByRole("link", { name: "新建商品" }).click();
  await page.getByLabel("SKU").fill("E2E-DRESS-001");
  await page.getByLabel("商品名称").fill("E2E Dress");
  await page.getByLabel("品类").selectOption("apparel");
  await page.getByRole("button", { name: "创建商品" }).click();
  await expect(page.getByText("E2E-DRESS-001")).toBeVisible();
});
```

Extend the same test with fixture reference upload, mock model creation, batch start, status wait, approval, ZIP download, and `manifest.json` assertion.

- [ ] **Step 2: Add targeted security and recovery tests**

```python
def test_secret_never_appears_in_api_or_logs(admin_client, caplog) -> None:
    secret = "provider-secret-that-must-not-leak"
    response = create_model(admin_client, api_key=secret)
    assert secret not in response.text
    assert secret not in caplog.text


@pytest.mark.asyncio
async def test_queued_step_survives_redis_outage(batch_service, recovery_worker) -> None:
    batch = await batch_service.create(redis_available=False)
    assert batch.status is BatchStatus.QUEUED
    await recovery_worker.scan_once()
    assert await recovery_worker.was_executed(batch.id)
```

- [ ] **Step 3: Implement the single verification script**

```bash
#!/usr/bin/env bash
set -euo pipefail

docker compose config --quiet
docker compose up -d postgres redis minio --wait
trap 'docker compose down' EXIT
uv run --project backend ruff check backend/src backend/tests
uv run --project backend pytest backend/tests -v
pnpm --dir apps/web lint
pnpm --dir apps/web test
docker compose up -d --build --wait
pnpm --dir apps/web test:e2e
```

`README.md` must document prerequisites, `.env` creation, service startup, bootstrap login, targeted test commands, benchmark manifest validation, and the fact that real provider validation requires user-supplied keys and real product assets. `THIRD_PARTY.md` records each dependency or upstream source actually copied; if none is copied in M0-M1, say so explicitly.

- [ ] **Step 4: Run final M0-M1 verification**

Run: `bash scripts/verify-m0-m1.sh`

Expected: backend lint/tests, web lint/tests, Compose health checks, browser flow, secret redaction, and Redis recovery all pass. Do not claim real provider quality or the 30-SKU benchmark passed unless real keys and real benchmark assets were supplied and the report exists.

- [ ] **Step 5: Commit, merge, verify main, and clean the branch when safe**

```bash
git add .
git commit -m "test: verify m0 m1 vertical slice"
git switch main
git merge --ff-only feat/m0-m1-foundation
bash scripts/verify-m0-m1.sh
```

If a remote exists, push `main`, verify `origin/main` contains the feature tip, then delete the local and remote feature branch. If no remote exists, report that push and remote branch cleanup were not applicable; delete the local feature branch only after `main` contains its tip.

---

## Completion Evidence

M0-M1 is complete only when all of the following are available:

- `bash scripts/verify-m0-m1.sh` exits 0 on `main`.
- A browser flow demonstrates SKU creation, reference upload, encrypted mock model configuration, durable generation, review, and ZIP export.
- Export `manifest.json` traces output to SKU, input hashes, truth anchor version, provider, model, parameters, cost, and reviewer.
- Secret-redaction and Redis-loss recovery tests pass.
- `aiimage-benchmark validate` rejects missing categories, missing strict-mode views, missing files, and incorrect hashes with precise messages.
- Real provider and 30-SKU quality claims remain explicitly unverified until user-supplied assets and keys produce a saved capability report.
