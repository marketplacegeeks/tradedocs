# External Integrations

**Analysis Date:** 2026-06-20

## APIs & External Services

**None Detected**

No third-party API integrations (Stripe, SendGrid, Slack, etc.) are currently configured.

## Data Storage

**Databases:**
- PostgreSQL 16 (primary database)
  - Connection: Via `DATABASE_URL` in production (Railway) or `DB_*` environment variables in development
  - Client: psycopg2-binary 2.9.11
  - ORM: Django ORM
  - Connection string format: `postgres://user:password@host:port/dbname`

**File Storage:**
- Local filesystem in development (`MEDIA_ROOT = BASE_DIR / "media"`, `MEDIA_URL = "/media/"`)
- Architecture supports swapping to S3 or R2 in production (comment in `tradetocs/settings.py`: "Swap DEFAULT_FILE_STORAGE for S3/R2 in production without touching models")
- Primarily stores user uploads (e.g., signed document copies)

**Caching:**
- None detected. Django cache framework not configured.

## Authentication & Identity

**Auth Provider:**
- Custom JWT implementation (no external OAuth/SSO provider)
  - Library: djangorestframework_simplejwt 5.5.1
  - Token type: Bearer tokens in HTTP Authorization header
  - Access token lifetime: Configurable via `TRADETOCS_ACCESS_TOKEN_LIFETIME_MINUTES` (default: 30 minutes)
  - Refresh token lifetime: Configurable via `TRADETOCS_REFRESH_TOKEN_LIFETIME_DAYS` (default: 7 days)
  - Refresh mechanism: Rotating refresh tokens with automatic blacklist after rotation (`ROTATE_REFRESH_TOKENS = True`, `BLACKLIST_AFTER_ROTATION = True`)

**User Model:**
- Custom user model: `apps.accounts.User` (extends AbstractBaseUser)
  - Login via email (USERNAME_FIELD = "email")
  - Roles: SUPER_ADMIN, COMPANY_ADMIN, CHECKER, MAKER
  - Soft-delete via `is_active = False` (never hard-deleted)

**Frontend Token Storage:**
- localStorage keys: `access_token`, `refresh_token`, `auth_user`
- HTTP-only cookie support not currently used (stored in localStorage)
- Axios interceptor (`src/api/axiosInstance.ts`) attaches token to every request
- Auto-refresh: Triggered on 401 response; failed refresh clears tokens and redirects to `/login`

## Monitoring & Observability

**Error Tracking:**
- None detected. No Sentry, Rollbar, or DataDog integration.

**Logs:**
- Console/stdout logging (Django default configuration)
- Email logging available via `EMAIL_BACKEND` configuration (default: console backend for dev)
- No structured logging service detected

## CI/CD & Deployment

**Hosting:**
- Railway (inferred from docker-compose.yml and settings comments mentioning Railway PostgreSQL plugin)
- Gunicorn as WSGI application server
- Whitenoise for static file serving in production

**CI Pipeline:**
- None detected. No GitHub Actions, GitLab CI, or Jenkins configuration found.

**Database Migrations:**
- Django migrations in each app (`apps/*/migrations/`)
- Managed via `python manage.py migrate`

## Environment Configuration

**Required Environment Variables (Backend):**

**Core:**
- `TRADETOCS_SECRET_KEY` - Django secret key (must be changed from default in production)
- `TRADETOCS_DEBUG` - Boolean debug flag (False in production)
- `TRADETOCS_ALLOWED_HOSTS` - Comma-separated list of allowed hosts

**Database:**
- `DATABASE_URL` - Full connection string (used in production via Railway PostgreSQL plugin)
- OR individual components (fallback if DATABASE_URL not set):
  - `DB_NAME` - Database name
  - `DB_USER` - Database user
  - `DB_PASSWORD` - Database password
  - `DB_HOST` - Database host
  - `DB_PORT` - Database port

**JWT/Authentication:**
- `TRADETOCS_ACCESS_TOKEN_LIFETIME_MINUTES` - JWT access token lifetime (default: 30)
- `TRADETOCS_REFRESH_TOKEN_LIFETIME_DAYS` - JWT refresh token lifetime (default: 7)

**CORS:**
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins (default: http://localhost:5173,http://127.0.0.1:5173)
- Constraint #28: Never use `CORS_ALLOW_ALL_ORIGINS = True`

**Email:**
- `TRADETOCS_EMAIL_BACKEND` - Email backend class (default: django.core.mail.backends.console.EmailBackend)
- `TRADETOCS_DEFAULT_FROM_EMAIL` - Default from email address (default: dev@tradetocs.local)

**Required Environment Variables (Frontend):**
- `VITE_API_BASE_URL` - Django API base URL (e.g., http://localhost:8000/api/v1)

**Secrets Location:**
- `.env` file in project root (git-ignored, contains local environment variables)
- Production: Railway service environment variables (auto-injected at build/runtime)

## Webhooks & Callbacks

**Incoming:**
- None detected. No webhook endpoints configured.

**Outgoing:**
- None detected. No outgoing webhook calls found.

## API Endpoints

**Base URL:** `/api/v1/`

**Authentication Endpoints:**
- `POST /auth/token/` - Login (obtain access and refresh tokens)
- `POST /auth/token/refresh/` - Refresh expired access token
- `POST /auth/logout/` - Logout (blacklist refresh token)
- `GET /auth/me/` - Get current user profile
- `POST /auth/reset-password/` - Request password reset

**User Management Endpoints:**
- `GET /users/` - List users (paginated, filtered)
- `POST /users/` - Create new user
- `GET /users/{id}/` - Retrieve user detail
- `PATCH /users/{id}/` - Update user
- `DELETE /users/{id}/` - Delete user (soft-delete via is_active=False)

**Core Document Endpoints:**
- Proforma Invoices: `/proforma-invoices/`, `/proforma-invoices/{id}/line-items/`, etc.
- Packing Lists: `/packing-lists/`, `/packing-lists/{id}/containers/`, etc.
- Commercial Invoices: `/commercial-invoices/`
- Purchase Orders: `/purchase-orders/`
- Certificate of Analysis: `/coa/`

**Master Data Endpoints:**
- `/organisations/`, `/banks/`, `/countries/`, `/ports/`, `/incoterms/`, `/payment-terms/`, etc.

**Report/PDF Endpoints:**
- PDF generation embedded in document endpoints (e.g., `/proforma-invoices/{id}/pdf/`)

**Filtering & Pagination:**
- DjangoFilterBackend enabled on list endpoints
- QuerySet filtering available via query parameters
- Pagination handled by DRF (default pagination class configured)

## Default Configuration Values

**Development Defaults (overridable via env vars):**
- Database: PostgreSQL on localhost:5432 (user: postgres, password: postgres, db: tradetocs)
- Frontend API URL: http://localhost:8000/api/v1
- Frontend Dev Server: http://localhost:5173
- JWT Access Token: 30 minutes
- JWT Refresh Token: 7 days
- CORS Origins: http://localhost:5173, http://127.0.0.1:5173
- Email Backend: Console (prints to stdout)
- Debug: True
- Secret Key: insecure dev key (must change in production)

---

*Integration audit: 2026-06-20*
