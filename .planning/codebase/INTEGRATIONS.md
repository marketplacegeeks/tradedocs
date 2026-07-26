# External Integrations

**Analysis Date:** 2026-07-26

## APIs & External Services

**Internal Backend APIs:**
- REST API endpoints defined in `/apps/*/urls.py`
- No third-party payment gateways, shipping APIs, or external services integrated
- API versioning: `api/v1/` (namespace in `tradetocs/urls.py`)

## Data Storage

**Databases:**
- PostgreSQL (primary)
  - Connection: `DATABASE_URL` env var (parsed in `tradetocs/settings.py` line 71-84)
  - Client: Django ORM with psycopg2-binary adapter
  - Fallback to individual DB_* env vars (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
  - Connection pooling: `conn_max_age=600` (10 minutes)

**File Storage:**
- Local filesystem only in development
  - Media root: `BASE_DIR / media` (configured in `tradetocs/settings.py`)
  - Static files: `BASE_DIR / staticfiles` (served by WhiteNoiseMiddleware in production)
  - Signed copy uploads: maximum 3 MB (`SIGNED_COPY_MAX_BYTES` in settings)
- **Production path:** Comment in `tradetocs/settings.py` line 159 indicates S3/R2 can be swapped in by changing `DEFAULT_FILE_STORAGE` without touching models

**Caching:**
- None detected — no Redis, Memcached, or other caching backend configured

## Authentication & Identity

**Auth Provider:**
- Custom JWT implementation via djangorestframework-simplejwt
  - Endpoint: `POST /api/v1/auth/login/` (expects email + password)
  - Token refresh: `POST /api/v1/auth/token/refresh/` (expects refresh token)
  - Logout: `POST /api/v1/auth/logout/` (blacklists refresh token)
  - User profile: `GET /api/v1/auth/me/`
- Implementation files:
  - Backend: `apps/accounts/views.py` (LoginView, LogoutView, TokenRefreshAPIView, MeView)
  - Frontend: `frontend/src/api/auth.ts` (login/logout functions)
  - Frontend interceptor: `frontend/src/api/axiosInstance.ts` (auto-attaches Bearer token, handles 401 refresh)
- Token lifecycle:
  - Access token TTL: 30 minutes (configurable via `TRADETOCS_ACCESS_TOKEN_LIFETIME_MINUTES`)
  - Refresh token TTL: 7 days (configurable via `TRADETOCS_REFRESH_TOKEN_LIFETIME_DAYS`)
  - Token rotation enabled (ROTATE_REFRESH_TOKENS = True)
  - Refresh token blacklisting enabled (BLACKLIST_AFTER_ROTATION = True)
- Authorization:
  - Role-based: SUPER_ADMIN, COMPANY_ADMIN, CHECKER, MAKER (defined in `apps/accounts/models.py`)
  - Global default: all DRF endpoints require authentication unless explicitly declared (REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES in settings)

## Monitoring & Observability

**Error Tracking:**
- None detected — no Sentry, DataDog, or similar integration

**Logs:**
- Django default logging to console
- No centralized logging backend detected
- Email backend for notifications: console backend in dev (configurable via `TRADETOCS_EMAIL_BACKEND`)

## CI/CD & Deployment

**Hosting:**
- Railway (evidence: DATABASE_URL auto-provisioning comment in settings)
- Deployment via Gunicorn + Django WSGI application (`tradetocs/wsgi.py`)

**CI Pipeline:**
- None detected — no GitHub Actions, GitLab CI, or similar configured in repository root

## Environment Configuration

**Required env vars:**
- `TRADETOCS_SECRET_KEY` - Django secret key (MUST change in production)
- `DATABASE_URL` or (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
- `TRADETOCS_ALLOWED_HOSTS` - Comma-separated list for production domain
- `CORS_ALLOWED_ORIGINS` - Frontend URL(s)
- `TRADETOCS_FRONTEND_BASE_URL` - For email deep links
- `VITE_API_BASE_URL` - Frontend API endpoint URL

**Optional env vars:**
- `TRADETOCS_DEBUG` - Debug mode (default: True)
- `TRADETOCS_ACCESS_TOKEN_LIFETIME_MINUTES` - JWT access token TTL (default: 30)
- `TRADETOCS_REFRESH_TOKEN_LIFETIME_DAYS` - JWT refresh token TTL (default: 7)
- `TRADETOCS_EMAIL_BACKEND` - Email service backend (default: console)
- `TRADETOCS_DEFAULT_FROM_EMAIL` - Sender email (default: dev@tradetocs.local)

**Secrets location:**
- Environment variables (sourced from `.env` file in development)
- `.env` file is gitignored and should never be committed

## Webhooks & Callbacks

**Incoming:**
- None detected — no webhook listeners for external services

**Outgoing:**
- Email notifications only (via Django email backend)
  - Deep links built using `TRADETOCS_FRONTEND_BASE_URL`
  - Subject to `TRADETOCS_EMAIL_BACKEND` configuration

## Document Generation

**PDF Export:**
- ReportLab 4.4.10 - Used in `pdf/` directory for PDF generation
  - In-memory generation (streamed, never written to disk per constraint #18 in CLAUDE.md)
  - Entry points: `pdf/cif_client_invoice_word_generator.py`, `pdf/commercial_invoice_generator.py`, etc.

**Word (.docx) Export:**
- python-docx 1.2.0 - Used for DOCX generation
  - Supports Proforma Invoice, Packing List, Commercial Invoice, Purchase Order, Certificate of Analysis exports

**Number Formatting:**
- num2words 0.5.14 - Converts numeric totals to words in documents

---

*Integration audit: 2026-07-26*
