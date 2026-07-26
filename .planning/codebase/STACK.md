# Technology Stack

**Analysis Date:** 2026-06-20

## Languages

**Backend:**
- Python 3.12 - Django REST Framework application serving `/api/v1` endpoints
- Django ORM for database access and model definitions

**Frontend:**
- TypeScript ~5.9.3 - React component-based SPA
- JSX/TSX - React component syntax
- CSS - Handled via Ant Design (antd) styling

## Runtime

**Backend Environment:**
- Python 3.12.0 (via pyenv at `/Users/aniket/.pyenv/versions/3.12.0`)
- Virtual environment: `.venv/` (pyvenv-based)
- WSGI application: `tradetocs.wsgi.application`
- ASGI application: `tradetocs.asgi.application`
- Process manager: Gunicorn 25.1.0 for production

**Frontend Environment:**
- Node.js v25.8.0
- NPM (included with Node)

## Frameworks

**Backend:**
- Django 6.0.3 - Web framework
- Django REST Framework 3.16.1 - REST API layer
- djangorestframework_simplejwt 5.5.1 - JWT authentication with token blacklist
- django-cors-headers 4.9.0 - CORS handling
- django-filter 25.2 - QuerySet filtering for list endpoints

**Frontend:**
- React 19.2.4 - UI framework
- React Router 7.13.1 - Client-side routing
- Vite 5.4.0 - Build tool and dev server
- Ant Design (antd) 6.3.3 - Component library
- TipTap 2.27.2 - Rich text editor (with link and underline extensions)

**Testing:**
- pytest 9.0.2 - Python test runner
- pytest-django 4.12.0 - Django integration for pytest
- factory-boy 3.3.3 - Test fixtures and factories
- Faker 40.11.0 - Fake data generation

## Key Dependencies

**Backend - Critical:**
- psycopg2-binary 2.9.11 - PostgreSQL database driver
- PyJWT 2.12.1 - JWT token creation and validation
- reportlab 4.4.10 - PDF generation (used in `pdf/` directory for invoice and packing list generation)
- Pillow 12.1.1 - Image processing (used by reportlab for PDF generation)

**Backend - Infrastructure:**
- gunicorn 25.1.0 - WSGI server for production
- whitenoise 6.9.0 - Serves static files in production (CompressedManifestStaticFilesStorage)
- asgiref 3.11.1 - ASGI compatibility layer
- dj-database-url 2.3.0 - DATABASE_URL parsing for environment-based DB config
- python-decouple 3.8 - Environment variable management
- sqlparse 0.5.5 - SQL parsing utility
- charset-normalizer 3.4.5 - Character encoding detection

**Backend - Utilities:**
- num2words 0.5.14 - Convert numbers to words (likely for PDF document formatting)
- phonenumbers 8.13.55 - Phone number parsing and validation (user contact info)
- Pygments 2.19.2 - Code syntax highlighting (for admin panel or reports)

**Frontend - Critical:**
- axios 1.13.6 - HTTP client (all API calls via `src/api/*.ts`)
- react-hook-form 7.71.2 - Form state management
- @hookform/resolvers 5.2.2 - Form validation resolvers
- zod 4.3.6 - Schema validation library

**Frontend - UI & UX:**
- Lucide React 0.577.0 - Icon library
- dayjs 1.11.20 - Date/time manipulation
- @tanstack/react-query 5.90.21 - Server state management and caching

## Configuration

**Environment:**
- Backend: `python-decouple` config function reads from `.env` file
- Frontend: Vite environment variables via `import.meta.env` (VITE_* prefix)
- Production database URL injected via `DATABASE_URL` environment variable (Railway PostgreSQL plugin)

**Key Configuration Files:**
- `tradetocs/settings.py` - Django configuration (SECRET_KEY, DEBUG, INSTALLED_APPS, DATABASES, REST_FRAMEWORK, JWT, CORS, EMAIL)
- `frontend/vite.config.ts` - Vite build config (React plugin enabled)
- `frontend/tsconfig.json` - TypeScript compiler options (target ES2023, strict mode enabled)
- `frontend/tsconfig.app.json` - Application-specific TypeScript config
- `docker-compose.yml` - PostgreSQL 16 dev database definition

**Backend Environment Variables:**
- `TRADETOCS_SECRET_KEY` - Django secret key (default: dev-insecure-key-change-in-production)
- `TRADETOCS_DEBUG` - Debug mode (default: True)
- `TRADETOCS_ALLOWED_HOSTS` - Allowed hosts (default: localhost,127.0.0.1)
- `DATABASE_URL` - Full database connection string (used in production via Railway)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - Individual DB params (fallback if DATABASE_URL not set)
- `CORS_ALLOWED_ORIGINS` - CORS allowed origins (default: http://localhost:5173,http://127.0.0.1:5173)
- `TRADETOCS_ACCESS_TOKEN_LIFETIME_MINUTES` - JWT access token lifetime (default: 30 minutes)
- `TRADETOCS_REFRESH_TOKEN_LIFETIME_DAYS` - JWT refresh token lifetime (default: 7 days)
- `TRADETOCS_EMAIL_BACKEND` - Email backend (default: django.core.mail.backends.console.EmailBackend for dev)
- `TRADETOCS_DEFAULT_FROM_EMAIL` - Default from email (default: dev@tradetocs.local)

**Frontend Environment Variables:**
- `VITE_API_BASE_URL` - Django API base URL (default: http://localhost:8000/api/v1)

## Build & Development

**Backend:**
- Entry point: `manage.py` (Django management CLI)
- Development server: `python manage.py runserver` (default: http://localhost:8000)
- Production server: Gunicorn + Whitenoise for static files

**Frontend:**
- Entry point: `frontend/src/main.tsx` (Vite entry point)
- Dev server: `npm run dev` (via Vite, default: http://localhost:5173)
- Build: `npm run build` (produces optimized bundle)
- Linting: `npm run lint` (ESLint configuration)

## Database

**Type:** PostgreSQL 16
**Client Library:** psycopg2-binary 2.9.11
**ORM:** Django ORM
**Connection pooling:** `conn_max_age=600` when using DATABASE_URL
**Development:** Docker Compose service `db` (postgres:16)
**Media storage:** Local filesystem (`MEDIA_ROOT = BASE_DIR / "media"` in development; swappable for S3/R2 in production)

## Static Files

**Development:** Served by Django development server
**Production:** Whitenoise (CompressedManifestStaticFilesStorage) serves from `STATIC_ROOT = staticfiles/`
**Frontend build output:** Compiled by Vite into `frontend/dist/` (not committed)

## Authentication

**Backend:**
- JWT (via djangorestframework_simplejwt 5.5.1)
- Tokens stored in HTTP-only cookies or localStorage (frontend-side)
- Token refresh endpoint: `/auth/token/refresh/` (called automatically by axios interceptor if 401)
- Token blacklist: `rest_framework_simplejwt.token_blacklist` app tracks blacklisted tokens

**Frontend:**
- Tokens stored in localStorage (`access_token`, `refresh_token`)
- Axios interceptor automatically attaches `Authorization: Bearer {token}` header
- Auto-refresh on 401 response (via `src/api/axiosInstance.ts`)

## Deployment

**Target Platform:** Railway (implied by docker-compose.yml and settings comments)
**Database:** Railway PostgreSQL plugin (DATABASE_URL auto-set)
**Frontend:** Static asset deployment (built SPA served by backend or CDN)
**Process Manager:** Gunicorn for WSGI application
**Static Files:** Whitenoise middleware serves pre-compressed static files

---

*Stack analysis: 2026-06-20*
