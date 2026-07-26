# Codebase Structure

**Analysis Date:** 2026-07-26

## Directory Layout

```
/Users/aniket/Documents/Development/TradeDocs/
├── apps/                           # Django apps (backend business logic)
│   ├── accounts/                   # Users, roles, JWT auth
│   ├── master_data/                # Reference entities (Organisation, Country, Port, Bank, etc.)
│   ├── workflow/                   # WorkflowService, AuditLog, status constants
│   ├── proforma_invoice/           # PI models, views, serializers
│   ├── packing_list/               # PL models, views, serializers
│   ├── commercial_invoice/         # CI models, views, serializers
│   ├── purchase_order/             # PO models, views, serializers
│   ├── certificate_of_analysis/    # COA models, views, serializers
│   └── manual_edits/               # Audit log viewer, manual data correction
├── frontend/                       # React/TypeScript SPA
│   ├── src/
│   │   ├── pages/                  # Page components (one folder per feature)
│   │   ├── components/             # Shared UI components
│   │   ├── api/                    # Axios API client functions
│   │   ├── store/                  # AuthContext (global state)
│   │   ├── utils/                  # constants.ts, apiErrors.ts
│   │   ├── assets/                 # Images, icons, static files
│   │   ├── App.tsx                 # Root router
│   │   └── main.tsx                # Vite entry point
│   ├── dist/                       # Built production assets (generated)
│   ├── tests/                      # E2E tests (Playwright)
│   └── vite.config.ts              # Vite bundler config
├── pdf/                            # ReportLab + python-docx PDF/Word generators
├── tradetocs/                      # Django settings, root URL config
│   ├── settings.py                 # Django configuration (DB, INSTALLED_APPS, JWT, CORS)
│   ├── urls.py                     # Root URL router
│   ├── wsgi.py                     # WSGI entry point
│   ├── asgi.py                     # ASGI entry point
│   └── pagination.py               # StandardPageNumberPagination class
├── docs/                           # Generated documentation
├── requirements/                   # Requirements docs (separate from code)
├── manage.py                       # Django CLI
├── pytest.ini                      # Pytest configuration
├── requirements.txt                # Python dependencies
├── Procfile                        # Heroku/Railway deployment config
├── CLAUDE.md                       # Project rules (read before any task)
├── .claude/                        # User instructions for Claude
│   └── designsystem.md             # Frontend design system guidelines
└── .env                            # Environment variables (local development only)
```

## Directory Purposes

**apps/ (Backend Django Apps)**
- Purpose: Modular business logic organized by domain
- Contains: Models, Views, Serializers, Services, Tests per app
- Key structure: Each app is self-contained with its own migrations, tests, URL patterns

**apps/accounts/**
- Purpose: Authentication, user management, roles, permissions
- Contains: `models.py` (User model with role choices), `views.py` (token endpoints), `permissions.py` (permission classes)
- Key files: `models.py:User`, `models.py:UserRole`, `views.py:TokenObtainPairView`, `permissions.py:IsMakerOrAdmin`

**apps/master_data/**
- Purpose: Reference data shared across all documents (Organisations, Countries, Ports, Banks, Currencies, Terms, etc.)
- Contains: Multiple simple models (Country, Port, Location, Incoterm, UOM, PaymentTerm, PreCarriageBy, TypeOfPackage, TCTemplate, Bank, Currency, etc.)
- Key files: `models.py` (all reference entities with is_active soft-delete), `views.py` (read-only list endpoints), `management/commands/` (data seeding)

**apps/workflow/**
- Purpose: Central workflow orchestration (status transitions, AuditLog, constants)
- Contains: `services.py:WorkflowService` (THE critical enforcement point), `constants.py` (transition tables), `models.py:AuditLog`, `signals.py` (Django signals for events)
- Key files: `services.py:WorkflowService.transition()`, `constants.py:PI_TRANSITIONS/PLCI_TRANSITIONS`, `models.py:AuditLog`

**apps/proforma_invoice/**
- Purpose: Proforma Invoice document (FR-09) — header + line items + charges
- Contains: `models.py` (ProformaInvoice, ProformaInvoiceLineItem, ProformaInvoiceCharge), `views.py` (CRUD + PDF export), `serializers.py` (nested validation)
- Key files: `models.py:ProformaInvoice`, `views.py:ProformaInvoiceViewSet`, `services.py:ProformaInvoiceService`

**apps/packing_list/**
- Purpose: Packing List document (FR-14M) — **created as a unit with CommercialInvoice**
- Contains: `models.py` (PackingList, PackingListContainer, PackingListContainerItem), `views.py` (joint PL+CI workflows), `serializers.py`
- Key files: `models.py:PackingList` (has FK to ProformaInvoice), `services.py:PackingListService`

**apps/commercial_invoice/**
- Purpose: Commercial Invoice document (FR-14M) — **linked to PackingList (parent), never created independently**
- Contains: `models.py` (CommercialInvoice, CommercialInvoiceLineItem), `views.py` (read-only; updates via PL), `serializers.py`
- Key files: `models.py:CommercialInvoice` (FK to PackingList), `views.py` (mostly read-only)

**apps/purchase_order/**
- Purpose: Purchase Order document (FR-PO) — standalone workflow
- Contains: `models.py` (PurchaseOrder, PurchaseOrderLineItem), `views.py`, `serializers.py`

**apps/certificate_of_analysis/**
- Purpose: Certificate of Analysis document (FR-COA) — test results for commodities
- Contains: `models.py` (CertificateOfAnalysis, TestParameter), `views.py`, `serializers.py`

**apps/manual_edits/**
- Purpose: Audit log viewer + manual correction interface for admins
- Contains: `models.py` (ManualEdit record), `views.py` (list/create endpoints), `services.py` (apply edits with tracking)

**frontend/ (React SPA)**
- Purpose: Single Page Application (TypeScript + React)
- Contains: Pages, components, API client, auth context, constants

**frontend/src/pages/**
- Purpose: Page-level containers (one folder per feature)
- Contains: `auth/` (login), `proforma-invoice/` (Create, Edit, List, Detail), `packing-list/`, `commercial-invoice/`, `master-data/`, `reports/`, `dashboard/`, `users/`, `manual-edits/`
- Pattern: Each folder contains 1+ React components; no shared state; data fetched via API

**frontend/src/components/**
- Purpose: Reusable UI building blocks
- Contains: `common/` (buttons, forms, modals), `layout/` (page chrome, navigation), `AppLayout.tsx`, `AuditLogDrawer.tsx`, `ProtectedRoute.tsx`

**frontend/src/api/**
- Purpose: Centralized Axios-based HTTP client (Constraint #11: no component calls Axios directly)
- Contains: One file per backend resource: `proformaInvoices.ts`, `packingLists.ts`, `organisations.ts`, `auth.ts`, etc.
- Pattern: Each file exports typed functions (e.g., `export async function create(data)`)
- Key file: `axiosInstance.ts` (shared Axios instance with token interceptor + 401 refresh)

**frontend/src/store/**
- Purpose: Global state management
- Contains: `AuthContext.tsx` (current user, role, token refresh)
- Pattern: Context API only; no Redux/Zustand

**frontend/src/utils/**
- Purpose: Shared utilities
- Contains: `constants.ts` (mirror of backend enums: DOCUMENT_STATUS, ROLES, INCOTERM_SELLER_FIELDS, etc.), `apiErrors.ts` (error parsing)
- Key file: `constants.ts` (Constraint #12: import status/role strings from here, never hardcode)

**pdf/**
- Purpose: PDF + Word (.docx) generation using ReportLab + python-docx
- Contains: Generator classes for each document type
- Pattern: One `*_generator.py` (ReportLab PDF) + optional `*_word.py`/`*_word_generator.py` (Word output)
- Examples: `proforma_invoice_generator.py`, `packing_list_generator.py`, `commercial_invoice_word_generator.py`
- Key file: `base.py` (base styles, fonts, common flowables)

**tradetocs/ (Django Project Settings)**
- Purpose: Django project-level configuration
- Contains: `settings.py` (INSTALLED_APPS, DB, middleware, JWT config), `urls.py` (API root routes), `wsgi.py`, `asgi.py`
- Key file: `settings.py` (Constraint #28: CORS_ALLOWED_ORIGINS is explicit list, never wildcard)

## Key File Locations

**Entry Points:**
- `tradetocs/urls.py` — Django root URL config; maps `/api/v1/` paths to app viewsets
- `tradetocs/wsgi.py` — WSGI entry (production server)
- `frontend/src/main.tsx` — Vite app bootstrap
- `frontend/src/App.tsx` — React router root

**Configuration:**
- `tradetocs/settings.py` — Django settings (DB, auth, CORS, email)
- `frontend/vite.config.ts` — Vite bundler (dev server, build output)
- `pytest.ini` — Pytest discovery + config
- `requirements.txt` — Python package versions

**Core Logic:**
- `apps/workflow/services.py` — WorkflowService (status transitions, audit logging)
- `apps/workflow/constants.py` — Transition tables, workflow actions
- `apps/accounts/permissions.py` — Role-based permission classes
- `frontend/src/utils/constants.ts` — Frontend enum mirrors

**Testing:**
- `apps/{app}/tests/` — Test files for each app (factories.py, test_models.py, test_views.py)
- `frontend/tests/e2e/` — Playwright E2E tests

## Naming Conventions

**Files:**
- Backend: `models.py`, `views.py`, `serializers.py`, `services.py`, `permissions.py`, `urls.py`, `admin.py`
- Frontend: `.tsx` (components), `.ts` (utilities, API), `.css` or `.module.css` (styles)
- Tests: `test_*.py` (pytest discovers these) or `*.test.ts`/`*.spec.ts` (frontend)

**Directories:**
- Backend apps: lowercase with underscore (e.g., `proforma_invoice`, `commercial_invoice`)
- Frontend pages: kebab-case (e.g., `proforma-invoice`, `manual-edits`)
- Frontend components: PascalCase folder names (e.g., `common/`, `layout/`)

**Python Classes:**
- Models: PascalCase, singular (e.g., `ProformaInvoice`, `ProformaInvoiceLineItem`, `AuditLog`)
- ViewSets: PascalCase ending in `ViewSet` (e.g., `ProformaInvoiceViewSet`)
- Serializers: PascalCase ending in `Serializer` (e.g., `ProformaInvoiceSerializer`)
- Services: PascalCase ending in `Service` (e.g., `WorkflowService`)
- Permission classes: PascalCase ending in permission name (e.g., `IsMakerOrAdmin`, `IsChecker`)

**Django Constants:**
- Status choices: UPPERCASE (e.g., `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REWORK`, `PERMANENTLY_REJECTED`)
- Workflow actions: UPPERCASE (e.g., `SUBMIT`, `APPROVE`, `REWORK`, `PERMANENTLY_REJECT`)
- Stored in workflow/constants.py

**React Components:**
- PascalCase file/folder names (e.g., `ProformaInvoiceCreate.tsx`, `AuditLogDrawer.tsx`)
- Props interfaces: `{ComponentName}Props` (e.g., `ProformaInvoiceCreateProps`)

**TypeScript Types:**
- Interfaces/Types: PascalCase (e.g., `User`, `ProformaInvoice`, `WorkflowTransition`)
- Enums in frontend: UPPERCASE_SNAKE_CASE keys (mirrored from backend: `DOCUMENT_STATUS.DRAFT`)

## Where to Add New Code

**New Feature (e.g., new document type):**
1. Create backend app: `python manage.py startapp {new_app_name}`
   - Add to `INSTALLED_APPS` in `tradetocs/settings.py`
   - Structure: `models.py`, `serializers.py`, `views.py`, `services.py`, `urls.py`, `tests/`
2. Add URL patterns to `tradetocs/urls.py`
3. Create frontend folder: `frontend/src/pages/{new-feature}/`
4. Create API client: `frontend/src/api/{newFeature}.ts`
5. Update `frontend/src/utils/constants.ts` with any new enums
6. Add routes to `frontend/src/App.tsx`

**New API Endpoint (existing app):**
- Add method to ViewSet in `apps/{app}/views.py` or create new APIView
- Add route to `apps/{app}/urls.py`
- Add test in `apps/{app}/tests/test_views.py`
- Add API function in `frontend/src/api/{resource}.ts`

**New Component/Module (frontend):**
- Shared UI: `frontend/src/components/{category}/ComponentName.tsx`
- Page-specific: `frontend/src/pages/{feature}/ComponentName.tsx`
- All data fetching via API client layer (`frontend/src/api/`)

**Utilities:**
- Shared helpers: `frontend/src/utils/{utility}.ts`
- Backend helpers: `apps/{app}/utils.py` or dedicated `services.py`

**Tests:**
- Backend model tests: `apps/{app}/tests/test_models.py` with factory-boy factories in `apps/{app}/tests/factories.py`
- Backend view tests: `apps/{app}/tests/test_views.py` (one test class per ViewSet)
- Frontend E2E: `frontend/tests/e2e/{feature}.spec.ts` (Playwright)

## Special Directories

**apps/{app}/migrations/**
- Purpose: Database schema version control (auto-generated by `python manage.py makemigrations`)
- Generated: Yes (auto)
- Committed: Yes (required for reproducible deployments)
- Note: Never edit migration files manually; use `makemigrations` + `migrate` workflow

**apps/{app}/tests/**
- Purpose: Pytest test files and test fixtures (factories)
- Generated: No (written by developer)
- Committed: Yes (required)
- Structure: `__init__.py`, `factories.py` (factory-boy), `test_models.py`, `test_views.py`

**frontend/dist/**
- Purpose: Built production assets (compiled JS, CSS, HTML)
- Generated: Yes (by `npm run build`)
- Committed: No (.gitignored)

**frontend/tests/e2e/fixtures/**
- Purpose: Shared test data generators for Playwright E2E tests
- Generated: No (written by developer)
- Committed: Yes
- Usage: Create organizations, users, documents for E2E test scenarios

**pdf/ (no subdirectories)**
- Purpose: Flat structure for all PDF generators; no app nesting needed (shared across documents)
- Generated: No (written by developer)
- Committed: Yes

**docs/**
- Purpose: Auto-generated or manually maintained documentation
- Generated: Possibly (Sphinx, etc.)
- Committed: Usually yes

**memory/**
- Purpose: Experimental or working directory (unclear purpose; appears unused)
- Committed: Possibly (check .gitignore)

**railway_exports/**
- Purpose: Railway deployment artifacts (not part of active codebase)
- Committed: Yes (but likely outdated)

## Git Structure

**Main branch:** `main`
- Always deployable; all tests passing
- Protected; requires PR review before merge

**Typical workflow:**
1. Create feature branch from `main`
2. Commit changes following conventional commit format
3. Push and create PR
4. All tests must pass in CI (run `pytest` before committing)
5. Merge to `main` via PR

**CI/CD:**
- Location: `.github/workflows/` (GitHub Actions) or Railway auto-deploy
- Runs: `pytest`, linting, build

## Frontend Build & Dev

**Development:**
```bash
cd frontend
npm run dev          # Starts Vite dev server (http://localhost:5173)
npm run build        # Compiles to dist/
npm run preview      # Preview production build locally
```

**Environment:**
- `frontend/.env` or `frontend/.env.local` (not committed)
- Key var: `VITE_API_BASE_URL` (defaults to http://localhost:8000/api/v1)

## Backend Development

**Setup:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

**Run:**
```bash
python manage.py runserver          # http://localhost:8000
python manage.py runserver 0.0.0.0:8000  # For external access
```

**Tests:**
```bash
pytest                               # Run all tests
pytest apps/proforma_invoice/tests/  # Run app-specific tests
pytest --cov=apps/ --cov-report=html  # Coverage report
```

---

*Structure analysis: 2026-07-26*
