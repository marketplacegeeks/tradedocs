# Codebase Structure

**Analysis Date:** 2026-06-20

## Directory Layout

```
TradeDocs/
├── manage.py                           # Django CLI entry point
├── pytest.ini                          # Pytest configuration
├── requirements.txt                    # Python dependencies
├── tradetocs/                          # Django project settings
│   ├── settings.py                     # Django configuration (DB, apps, middleware)
│   ├── urls.py                         # Root URL router
│   ├── wsgi.py                         # WSGI application
│   ├── asgi.py                         # ASGI application
│   └── pagination.py                   # StandardPageNumberPagination class
├── apps/                               # All Django apps (domain-driven)
│   ├── accounts/                       # User authentication & roles
│   ├── master_data/                    # Reference data (organisations, countries, ports, etc.)
│   ├── workflow/                       # Status machine, audit logging
│   ├── proforma_invoice/               # PI document type
│   ├── packing_list/                   # PL document type
│   ├── commercial_invoice/             # CI document type
│   ├── purchase_order/                 # PO document type
│   └── certificate_of_analysis/        # COA document type
├── pdf/                                # PDF generation (ReportLab-based)
│   ├── base.py                         # Shared PDF utilities
│   ├── proforma_invoice.py             # PI PDF generator
│   ├── packing_list_generator.py       # PL PDF generator
│   ├── commercial_invoice_generator.py # CI PDF generator
│   ├── purchase_order.py               # PO PDF generator
│   ├── certificate_of_analysis.py      # COA PDF generator
│   └── utils.py                        # PDF utility functions
├── frontend/                           # React TypeScript SPA
│   ├── package.json                    # Frontend dependencies
│   ├── tsconfig.json                   # TypeScript configuration
│   ├── src/
│   │   ├── main.tsx                    # React app entry point
│   │   ├── App.tsx                     # Main router & layout
│   │   ├── api/                        # API client modules (Axios)
│   │   ├── pages/                      # Page components (route-based)
│   │   ├── components/                 # Reusable UI components
│   │   ├── store/                      # Context providers (AuthContext)
│   │   └── utils/                      # Constants, helpers
│   └── public/                         # Static assets
└── docs/                               # Documentation & specifications
```

## Directory Purposes

**`tradetocs/`:**
- Purpose: Django project root; configuration, settings, main URL routing
- Contains: settings.py (database, installed apps, middleware), urls.py (API route registration)
- Key files: `tradetocs/settings.py` (REST_FRAMEWORK config, AUTH_USER_MODEL), `tradetocs/urls.py` (route dispatcher)

**`apps/accounts/`:**
- Purpose: User management, roles, JWT authentication
- Contains: User model (email-based), UserRole choices, views for login/logout/token refresh, custom permissions
- Key files: `models.py` (User, UserRole), `views.py` (LoginView, MeView, UserListCreateView), `permissions.py` (IsCompanyAdmin, IsAnyRole)

**`apps/master_data/`:**
- Purpose: Lookup/reference data for all documents (organisations, countries, ports, banks, payment terms)
- Contains: Models for Country, Port, Location, Organisation, Bank, Incoterm, UOM, PaymentTerm, PreCarriageBy, Currency
- Key files: `models.py` (all reference models), `views.py` (CRUD for each), `urls.py` (77 endpoints for reference data CRUD)

**`apps/workflow/`:**
- Purpose: Centralized workflow state machine, audit logging, dashboard aggregation
- Contains: WorkflowService (transition logic), AuditLog model (immutable records), dashboard views
- Key files: `services.py` (WorkflowService.transition, constraint enforcement), `constants.py` (transition tables), `models.py` (AuditLog), `dashboard_views.py` (aggregate stats)

**`apps/proforma_invoice/`:**
- Purpose: Proforma Invoice document type with header, line items, charges
- Contains: ProformaInvoice model, ProformaInvoiceLineItem, ProformaInvoiceCharge, serializers, views
- Key files: `models.py` (PI header + nested models), `views.py` (CRUD + workflow actions + PDF download), `services.py` (document number generation), `serializers.py` (nested serialization)

**`apps/packing_list/`:**
- Purpose: Packing List document type (always created with matching Commercial Invoice)
- Contains: PackingList header, Container (shipping containers), ContainerItem, serializers, views
- Key files: `models.py` (PL header + containers), `views.py` (joint PL+CI operations), `services.py` (PL document numbering), `serializers.py` (nested serialization with containers)

**`apps/commercial_invoice/`:**
- Purpose: Commercial Invoice document type (linked to PackingList)
- Contains: CommercialInvoice model (header only), aggregated line items from PL
- Key files: `models.py` (CI linked to PL), `views.py` (CRUD + PDF download), `services.py` (CI document numbering)

**`apps/purchase_order/`:**
- Purpose: Purchase Order document type (independent from PI/PL/CI workflow)
- Contains: PurchaseOrder model, POLineItem, serializers, views
- Key files: `models.py` (PO header + line items), `views.py` (CRUD + workflow), `services.py` (PO numbering)

**`apps/certificate_of_analysis/`:**
- Purpose: Certificate of Analysis document type (testing/quality records)
- Contains: CertificateOfAnalysis model, COAParameter, serializers, views
- Key files: `models.py` (COA header + test parameters), `views.py` (CRUD + workflow + PDF), `services.py` (COA numbering)

**`pdf/`:**
- Purpose: In-memory PDF generation using ReportLab
- Contains: Generator classes for each document type, base utilities
- Key files: `base.py` (shared PDF building blocks), `proforma_invoice.py` (PI → PDF), `packing_list_generator.py` (PL → PDF), `commercial_invoice_generator.py` (CI → PDF), `utils.py` (page utilities)

**`frontend/src/`:**
- Purpose: React TypeScript single-page application
- Contains: Page components (one per route), reusable UI components, API client modules, auth context

**`frontend/src/api/`:**
- Purpose: HTTP client layer; all Axios calls centralized here (no direct axios in components)
- Contains: Typed API functions for each resource (proformaInvoices.ts, packingLists.ts, organisations.ts, etc.)
- Key files: `axiosInstance.ts` (configured Axios with auth headers), individual resource files (proformaInvoices.ts, packingLists.ts)

**`frontend/src/pages/`:**
- Purpose: Route-based page components
- Contains: Subdirectories for each feature (auth, proforma-invoice, packing-list, master-data, dashboard, reports)
- Key files: `*ListPage.tsx` (list views with filters), `*DetailPage.tsx` (detail + workflow actions), `*CreatePage.tsx` / `*FormPage.tsx` (forms)

**`frontend/src/components/`:**
- Purpose: Reusable UI components
- Contains: Layout components (AppLayout, ProtectedRoute), shared widgets (WorkflowActionButton, AuditLogDrawer)
- Key files: `AppLayout.tsx` (sidebar + main layout), `ProtectedRoute.tsx` (auth guard), `WorkflowActionButton.tsx` (submit/approve buttons)

**`frontend/src/store/`:**
- Purpose: Global state management
- Contains: AuthContext for authentication state
- Key files: `AuthContext.tsx` (user identity, login/logout, localStorage persistence)

**`frontend/src/utils/`:**
- Purpose: Shared utilities and constants
- Contains: Enum mirrors (ROLES, DOCUMENT_STATUS), UI labels, formatting helpers
- Key files: `constants.ts` (ROLES, DOCUMENT_STATUS, ORG_TAGS, INCOTERM_SELLER_FIELDS)

## Key File Locations

**Entry Points:**
- `manage.py`: Django management CLI
- `tradetocs/urls.py`: Main URL router dispatcher
- `frontend/src/main.tsx`: React app initialization
- `frontend/src/App.tsx`: Route definitions and layout

**Configuration:**
- `tradetocs/settings.py`: Django config (database, apps, middleware, REST_FRAMEWORK, JWT)
- `frontend/package.json`: Node dependencies, scripts
- `frontend/tsconfig.json`: TypeScript compiler options
- `pytest.ini`: Test runner config (DJANGO_SETTINGS_MODULE, discovery patterns)

**Core Logic:**
- `apps/workflow/services.py`: WorkflowService (state machine, constraint enforcement)
- `apps/proforma_invoice/services.py`: PI document number generation
- `apps/packing_list/services.py`: PL document number generation
- `apps/commercial_invoice/services.py`: CI document number generation

**Testing:**
- `apps/accounts/tests/`: User model & view tests; factories.py with role-based factories
- `apps/proforma_invoice/tests/`: PI CRUD & workflow tests
- `apps/packing_list/tests/`: PL+CI joint operation tests
- `apps/workflow/tests/`: Transition logic & cascade tests

## Naming Conventions

**Files:**
- Python models: `models.py` (one per app)
- Python views: `views.py` (ViewSet or APIView classes)
- Python serializers: `serializers.py` (ModelSerializer or custom Serializer)
- Python services: `services.py` (business logic, no HTTP concern)
- Python constants: `constants.py` (enums, transition tables, choice mappings)
- Python tests: `tests/test_*.py` (test_models.py, test_views.py)
- Python factories: `tests/factories.py` (factory_boy model factories)
- Frontend pages: `*Page.tsx` (ListPage, DetailPage, CreatePage, FormPage)
- Frontend components: `*.tsx` (PascalCase for component names)
- Frontend API: `*.ts` (camelCase, one file per resource)

**Directories:**
- Django apps: lowercase, underscores (accounts, master_data, proforma_invoice)
- Frontend pages: kebab-case (auth, master-data, proforma-invoice, packing-list)
- Frontend components: PascalCase subdirectories inside `src/components/`
- Tests: `tests/` directory inside each Django app, with `__init__.py`

**Database Tables:**
- Format: `{app_name}_{model_name}` (accounts_user, workflow_audit_log, proforma_invoice_proformainvoice)
- Explicitly set in model `Meta.db_table` to avoid Django's default conversion

**URLs/Endpoints:**
- Backend: `POST /api/v1/{resource}/` (create), `GET /api/v1/{resource}/` (list), `GET /api/v1/{resource}/{id}/` (detail), `PUT /api/v1/{resource}/{id}/` (update)
- Actions: `POST /api/v1/{resource}/{id}/{action}-action/` (e.g., `/submit-action/`, `/approve-action/`, `/reject-action/`)
- Document numbers: Format string {TYPE}-YYYY-NNNN (PI-2026-0001, PL-2026-0042, CI-2026-0015)

## Where to Add New Code

**New Feature in Existing Document Type (e.g., new field on PI):**
- Primary code: Add field to `apps/proforma_invoice/models.py`, migration, serializer field
- View logic: Add to `apps/proforma_invoice/views.py` if it affects endpoints
- Tests: Add test case to `apps/proforma_invoice/tests/test_models.py` and `test_views.py`
- Frontend: Add form input to `frontend/src/pages/proforma-invoice/ProformaInvoiceFormPage.tsx`, update API type in `frontend/src/api/proformaInvoices.ts`

**New Document Type (e.g., ShippingInstruction):**
- Create new app: `python manage.py startapp shipping_instruction`
- Models: `apps/shipping_instruction/models.py` (header + nested models)
- Views: `apps/shipping_instruction/views.py` (ViewSet + action endpoints)
- Serializers: `apps/shipping_instruction/serializers.py`
- Services: `apps/shipping_instruction/services.py` (document number generation)
- Workflow: Add transition table to `apps/workflow/constants.py`
- PDF: `pdf/shipping_instruction.py` (ReportLab generator)
- Frontend: Create `frontend/src/pages/shipping-instruction/` (ListPage, DetailPage, CreatePage, FormPage)
- Frontend API: Create `frontend/src/api/shippingInstructions.ts`
- Register in `tradetocs/urls.py`

**New Workflow Action (e.g., "ESCALATE"):**
- Add to `apps/workflow/constants.py` transition tables
- Implement logic in `WorkflowService._cascade_*` if it affects linked documents
- Add test case to `apps/workflow/tests/test_services.py`
- Add button/action to frontend (WorkflowActionButton component)

**New Master Data Reference (e.g., Currency):**
- Model: Add to `apps/master_data/models.py`
- Views: Add CRUD ViewSet to `apps/master_data/views.py`
- Serializer: Add serializer to `apps/master_data/serializers.py`
- URLs: Register in `apps/master_data/urls.py`
- Frontend: Add API calls to `frontend/src/api/referenceData.ts` or new file

**Shared Utility Function:**
- Python backend: `apps/{domain}/services.py` (if domain-specific) or create `shared/utils.py`
- React frontend: `frontend/src/utils/helpers.ts` (for formatting, validation), `frontend/src/api/axiosInstance.ts` (for HTTP config)

**New Unit Test:**
- Location: `apps/{app}/tests/test_{component}.py`
- Pattern: Use factories from `apps/{app}/tests/factories.py` (SubFactory for relations, never hardcoded IDs)
- Assertion: Happy path + permission denial for each endpoint
- Run: `pytest apps/{app}/tests/` or `pytest --cov=apps/{app}`

## Special Directories

**`apps/` (Django apps):**
- Purpose: Domain-driven app organization
- Generated: No (handwritten)
- Committed: Yes

**`pdf/` (PDF generators):**
- Purpose: In-memory PDF rendering
- Generated: No (handwritten)
- Committed: Yes
- Note: Output PDFs are never written to disk; always streamed as FileResponse

**`frontend/node_modules/`:**
- Purpose: Installed npm dependencies
- Generated: Yes (created by `npm install`)
- Committed: No (in .gitignore)

**`frontend/dist/`:**
- Purpose: Built/bundled frontend (Vite output)
- Generated: Yes (created by `npm run build`)
- Committed: No (in .gitignore)

**`migrations/` (inside each app):**
- Purpose: Database schema versions
- Generated: Yes (created by `python manage.py makemigrations`)
- Committed: Yes (must be versioned)

**`tests/__pycache__/`:**
- Purpose: Compiled Python test cache
- Generated: Yes (created by pytest)
- Committed: No (in .gitignore)

**`media/`:**
- Purpose: User-uploaded files
- Generated: Yes (at runtime)
- Committed: No (in .gitignore)

**`docs/`:**
- Purpose: Requirements, specifications, planning documents
- Generated: No (handwritten)
- Committed: Yes

---

*Structure analysis: 2026-06-20*
