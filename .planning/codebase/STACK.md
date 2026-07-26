# Technology Stack

**Analysis Date:** 2026-07-26

## Languages

**Primary:**
- Python 3.12 - Backend (Django), database models, API logic, PDF generation
- TypeScript 5.9.3 - Frontend (React), type-safe UI components and API clients
- JavaScript - Frontend build tooling and Node scripts

**Secondary:**
- HTML/CSS - Rendered via React with Ant Design component library

## Runtime

**Environment:**
- Python 3.12.0 - Backend runtime
- Node.js 26.4.0 - Frontend build and development

**Package Manager:**
- pip - Python package management
- npm 11.17.0 - Node package management
- Lockfile: `requirements.txt` (pinned), `frontend/package-lock.json` (present)

## Frameworks

**Core:**
- Django 6.0.3 - Web framework and ORM for backend
- Django REST Framework 3.16.1 - API serialization, viewsets, permissions
- React 19.2.4 - Frontend UI library
- Vite 5.4.0 - Frontend build tool and dev server

**Authentication:**
- djangorestframework-simplejwt 5.5.1 - JWT token generation/validation
- PyJWT 2.12.1 - JWT encoding/decoding

**Form & Validation:**
- React Hook Form 7.71.2 - Frontend form state management
- Zod 4.3.6 - Frontend schema validation
- @hookform/resolvers 5.2.2 - Integration between Hook Form and Zod

**Testing:**
- pytest 9.0.2 - Python test runner
- pytest-django 4.12.0 - Django test utilities
- @playwright/test 1.61.1 - E2E browser automation (configured in `frontend/playwright.config.ts`)

**Build/Dev:**
- @vitejs/plugin-react 4.3.0 - React integration for Vite
- TypeScript 5.9.3 - Type checking for frontend
- @eslint/js 9.39.4 - JavaScript linting
- typescript-eslint 8.56.1 - TypeScript linting
- eslint-plugin-react-hooks 7.0.1 - React hooks linting
- eslint-plugin-react-refresh 0.5.2 - Fast refresh linting

**UI Components:**
- Ant Design (antd) 6.3.3 - Component library for form fields, modals, tables
- Lucide React 0.577.0 - Icon library
- TipTap 2.27.2 - WYSIWYG editor framework
- @tiptap/starter-kit - TipTap baseline extensions
- @tiptap/extension-link - Hyperlink support for editor
- @tiptap/extension-underline - Text underline for editor
- @tiptap/react - React integration for TipTap

**Data:**
- axios 1.13.6 - HTTP client for API calls (wrapped in `frontend/src/api/`)
- @tanstack/react-query 5.90.21 - Server state management and caching

**Utilities:**
- dayjs 1.11.20 - Date/time manipulation (lightweight Date alternative)
- react-router-dom 7.13.1 - Client-side routing
- xlsx 0.18.5 - Excel export (used in frontend for reports)

## Key Dependencies

**Critical:**
- Django 6.0.3 - Core backend framework and ORM
- djangorestframework 3.16.1 - API endpoint definition and serialization
- psycopg2-binary 2.9.11 - PostgreSQL adapter for Python
- reportlab 4.4.10 - PDF generation (used in `pdf/` directory for ReportLab exports)
- python-docx 1.2.0 - DOCX generation for Word document exports

**Infrastructure:**
- gunicorn 25.1.0 - WSGI application server for production
- whitenoise 6.9.0 - Serves static files in production; configured in `tradetocs/settings.py`
- django-cors-headers 4.9.0 - CORS handling for frontend-to-backend communication
- dj-database-url 2.3.0 - Parses DATABASE_URL env var in `tradetocs/settings.py`
- python-decouple 3.8 - Environment variable loading

**Domain-Specific:**
- phonenumbers 8.13.55 - International phone number validation and formatting
- num2words 0.5.14 - Converts numbers to words (used in trade document formatting)
- Faker 40.11.0 - Test data generation via factory-boy
- factory-boy 3.3.3 - ORM-agnostic test fixture factory pattern

**Utilities:**
- django-filter 25.2 - Query parameter filtering in DRF viewsets
- Pillow 12.1.1 - Image processing and validation
- sqlparse 0.5.5 - SQL parsing (utility dependency)
- charset-normalizer 3.4.5 - Character encoding detection
- packaging 26.0 - Version parsing utilities

## Configuration

**Environment:**
- Loaded via `python-decouple.config()` in `tradetocs/settings.py`
- Key env vars (with defaults shown):
  - `DATABASE_URL` - PostgreSQL connection string (Railway auto-sets this)
  - `TRADETOCS_SECRET_KEY` - Django secret key (default: dev-insecure-key-change-in-production)
  - `TRADETOCS_DEBUG` - Debug mode (default: True)
  - `TRADETOCS_ALLOWED_HOSTS` - Comma-separated list (default: localhost,127.0.0.1)
  - `CORS_ALLOWED_ORIGINS` - Frontend URLs (default: http://localhost:5173,http://127.0.0.1:5173)
  - `TRADETOCS_ACCESS_TOKEN_LIFETIME_MINUTES` - JWT access token TTL (default: 30)
  - `TRADETOCS_REFRESH_TOKEN_LIFETIME_DAYS` - JWT refresh token TTL (default: 7)
  - `TRADETOCS_EMAIL_BACKEND` - Email service (default: console backend for dev)
  - `TRADETOCS_DEFAULT_FROM_EMAIL` - Sender email (default: dev@tradetocs.local)
  - `TRADETOCS_FRONTEND_BASE_URL` - Used for email deep links (default: http://localhost:5173)
  - `VITE_API_BASE_URL` - Frontend API endpoint (default: http://localhost:8000/api/v1)

**Build:**
- Backend: `tradetocs/settings.py` (Django configuration)
- Frontend: `frontend/vite.config.ts` (Vite bundler), `frontend/tsconfig.json` (TypeScript)
- ESLint: `frontend/eslint.config.js` (flat config format)
- Tests: `pytest.ini` (pytest configuration)

## Platform Requirements

**Development:**
- Python 3.12.x
- Node.js 26.x (or compatible v24+)
- PostgreSQL (local development) or Railway PostgreSQL (production)
- Virtual environment recommended for Python

**Production:**
- Deployment target: Railway (indicated by DATABASE_URL auto-provisioning in settings)
- Gunicorn serves Django app
- Static files served via WhiteNoiseMiddleware or nginx
- Media files: local disk in dev, must swap to S3/R2 in production (comment in `tradetocs/settings.py` line 159)

---

*Stack analysis: 2026-07-26*
