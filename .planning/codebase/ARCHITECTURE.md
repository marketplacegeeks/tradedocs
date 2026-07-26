# Architecture

**Analysis Date:** 2026-07-26

## Pattern Overview

**Overall:** Django REST Framework (DRF) monolith with modular apps + React SPA frontend. Multi-document workflow with shared business rules enforced through a centralized WorkflowService.

**Key Characteristics:**
- Single source of truth for all status transitions via `apps/workflow/services.py:WorkflowService`
- Document-centric design: Proforma Invoice → Packing List → Commercial Invoice (linear dependency chain)
- Role-based access control (SUPER_ADMIN, COMPANY_ADMIN, CHECKER, MAKER) enforced at both API and frontend levels
- Decimal arithmetic throughout (no floating-point) for monetary and weight fields
- In-memory PDF generation streamed directly (ReportLab)
- JWT authentication with token refresh interceptor on frontend
- Soft-delete pattern: entities marked `is_active=False` rather than hard-deleted

## Layers

**API Layer (DRF Views):**
- Purpose: Accept HTTP requests, delegate to services, return JSON responses
- Location: `apps/{app}/views.py` for each app (e.g., `apps/proforma_invoice/views.py`)
- Contains: ViewSets, custom APIViews, report views, PDF export endpoints
- Depends on: Serializers (validation), Services (business logic), Models (data)
- Used by: React frontend via Axios

**Business Logic Layer (Services):**
- Purpose: Encapsulate complex workflows, generate document numbers, cascade deletions, coordinate multi-model updates
- Location: `apps/{app}/services.py`, especially `apps/workflow/services.py` (the critical enforcement point)
- Contains: `WorkflowService.transition()` (all status changes), document number generation with `select_for_update()`, permanent rejection cascades
- Depends on: Models, constants, transaction management
- Used by: Views (requested by HTTP), signals (on model events)

**Data Layer (Models):**
- Purpose: Define entity structure, constraints, relationships
- Location: `apps/{app}/models.py`
- Contains: Django ORM models with ForeignKeys (PROTECT on master data), DecimalField for amounts/weights, status fields tied to workflow.constants
- Depends on: Django ORM, workflow constants for status choices
- Used by: Serializers (representation), Views (querying), Services (manipulation)

**Serializer Layer (DRF):**
- Purpose: Validate input, transform model instances to JSON, handle nested relations
- Location: `apps/{app}/serializers.py`
- Contains: ModelSerializer subclasses, nested serializers (e.g., LineItems within PI), validation methods
- Depends on: Models, utils
- Used by: Views (during request/response)

**PDF Generation Layer (ReportLab):**
- Purpose: Generate in-memory PDFs for export (never written to disk per Constraint #20)
- Location: `pdf/{document_type}.py` and `pdf/{document_type}_generator.py` and `pdf/{document_type}_word.py`
- Contains: ReportLab flowables and styles (PDF), python-docx document builders (Word .docx)
- Depends on: Models (via queries from views/services)
- Used by: DRF views (stream as FileResponse)

**Frontend API Client Layer (Axios):**
- Purpose: Centralized HTTP communication, token management, retry logic
- Location: `frontend/src/api/{resource}.ts` (one file per API resource)
- Contains: Axios instance with interceptors (token attach, 401 refresh), typed API methods
- Depends on: localStorage (tokens), axiosInstance
- Used by: React components, AuthContext

**Frontend UI Layer (React/TypeScript):**
- Purpose: Render pages, capture user input, display workflow state
- Location: `frontend/src/pages/{feature}/` for page containers, `frontend/src/components/` for shared UI
- Contains: React functional components, forms (Formik or similar), data tables
- Depends on: API client layer, constants (status/role strings), AuthContext
- Used by: Browser

## Data Flow

**Document Creation (PI → PL → CI):**

1. User (Maker) navigates to "Create Proforma Invoice" → `frontend/src/pages/proforma-invoice/Create.tsx`
2. Form submission calls `frontend/src/api/proformaInvoices.ts:create(payload)`
3. Axios POST to `http://localhost:8000/api/v1/proforma-invoices/` with JWT token
4. `apps/proforma_invoice/views.py:ProformaInvoiceViewSet.create()` receives request
5. `ProformaInvoiceSerializer.create()` validates and saves model instance
6. `apps/proforma_invoice/models.py:ProformaInvoice.save()` triggers signal (if any) or service call generates `pi_number` via `select_for_update()`
7. Response includes `pi_id` and `pi_number`
8. Frontend stores PI ID, user can now add line items (nested POST to same resource)
9. User submits for approval → calls `frontend/src/api/proformaInvoices.ts:submitForApproval(piId, comment)`
10. POST to `/api/v1/proforma-invoices/{id}/submit-for-approval/` with comment
11. `ProformaInvoiceViewSet.submit_for_approval()` calls `WorkflowService.transition(document=pi, action="SUBMIT", performed_by=user, comment=comment)`
12. `WorkflowService.transition()` inside `transaction.atomic()`:
    - Validates transition is legal given current status
    - Validates user has permission (role check)
    - Validates comment if required
    - Updates `pi.status = "PENDING_APPROVAL"`
    - Creates `AuditLog` entry with all audit metadata
    - If rejected at this stage, cascades to linked PLs/CIs
13. Response includes new status; frontend updates list view

**Document Approval (Checker Role):**

1. Checker navigates to "Pending Approval" tab (filtered list by status)
2. Selects PI, clicks "Approve"
3. Frontend POST to `/api/v1/proforma-invoices/{id}/approve/` with optional comment
4. `ProformaInvoiceViewSet.approve()` calls `WorkflowService.transition()` with action="APPROVE"
5. Same atomic transaction: status → "APPROVED", AuditLog created
6. If rejection after approval: cascade (PERMANENTLY_REJECT status flows to linked documents via `_cascade_permanently_rejected()`)

**Packing List Creation (from PI):**

1. User selects an APPROVED PI, clicks "Create Packing List"
2. Frontend wizard (`frontend/src/pages/packing-list/Create.tsx`) guides through steps:
   - Step 1: Auto-populated from PI (exporter, consignee, etc.)
   - Step 2-4: Containers and items
   - Step 5: Incoterms, cost breakdown (freight, insurance, etc.)
3. POST to `/api/v1/packing-lists/` with nested containers
4. `apps/packing_list/views.py:PackingListViewSet.create()` receives request
5. Service creates both PackingList AND CommercialInvoice in same transaction (FR-14M.12)
6. Both records created in DRAFT, share workflow (joint approval)

**PDF Export:**

1. User views PI detail, clicks "Download PDF"
2. Frontend calls `frontend/src/api/proformaInvoices.ts:exportPDF(piId)`
3. GET `/api/v1/proforma-invoices/{id}/export-pdf/`
4. `ProformaInvoiceViewSet.export_pdf()` queries PI + line items + charges
5. Calls `pdf/proforma_invoice_generator.py:ProformaInvoiceGenerator(pi=instance).generate()`
6. ReportLab builds flowables in memory (no disk write)
7. Returns `FileResponse(buffer, content_type='application/pdf')`
8. Browser downloads file

**State Management:**

- **Backend:** Status is the source of truth in DB; AuditLog records every transition
- **Frontend:** AuthContext holds current user + role; components fetch status from API on mount; local component state for form input only
- **JWT:** Access token in localStorage, refreshed automatically on 401 via interceptor

## Key Abstractions

**WorkflowService (apps/workflow/services.py):**
- Purpose: Centralized gateway for all status transitions
- Examples: `ProformaInvoice.status`, `PackingList.status`, `CommercialInvoice.status`
- Pattern: Static methods accepting document instance + action; returns new status; throws PermissionDenied or ValidationError on rule violation

**Transition Tables (apps/workflow/constants.py):**
- Purpose: Define state machine rules (which roles can perform which actions from each state)
- Examples: `PI_TRANSITIONS` (Proforma Invoice), `PLCI_TRANSITIONS` (PL+CI joint), `PO_TRANSITIONS` (Purchase Order)
- Pattern: Nested dict `{current_status: {action_name: (next_status, [allowed_roles])}}`

**AuditLog (apps/workflow/models.py):**
- Purpose: Immutable record of all transitions with metadata
- Pattern: Created alongside every status change in the same `transaction.atomic()`
- Fields: `document_type`, `document_id`, `document_number`, `action`, `from_status`, `to_status`, `comment`, `performed_by`, `timestamp`

**Document Number Generation (per app service):**
- Purpose: Auto-generate unique formatted numbers (`PI-2026-0001`, `PL-2026-0042`, etc.)
- Pattern: Query max existing number for year using `select_for_update()` to prevent race conditions
- Location: Service methods in each app (e.g., `ProformaInvoiceService.generate_document_number()`)

**TypeScript Constants (frontend/src/utils/constants.ts):**
- Purpose: Mirror backend enums to avoid hardcoding status/role strings in components
- Examples: `DOCUMENT_STATUS.DRAFT`, `ROLES.MAKER`, `INCOTERM_SELLER_FIELDS["CIF"]`
- Pattern: Centralized export; imported by components, API clients, forms

**Organisation Master Data (apps/master_data/models.py):**
- Purpose: Centralized registry of exporters, consignees, buyers, notify parties; supports soft-delete
- Pattern: `is_active=False` marks deleted records; ForeignKey `on_delete=PROTECT` prevents orphaning
- Related models: `Address`, `BankAccount`, `BankAccountDetails` (hierarchical data model)

## Entry Points

**Backend API Entry:**
- Location: `tradetocs/urls.py` (Django root URL config)
- Triggers: HTTP requests from frontend or external clients
- Responsibilities: Route `/api/v1/{path}` to appropriate viewset/view; return JSON

**Frontend Entry:**
- Location: `frontend/src/main.tsx` (Vite app bootstrap)
- Triggers: Browser page load
- Responsibilities: Initialize React app, AuthContext, render App.tsx router

**Authentication Entry:**
- Location: `apps/accounts/views.py:TokenObtainPairView` (DRF-SimpleJWT)
- Triggers: POST `/api/v1/auth/token/` with email + password
- Responsibilities: Validate credentials, return access + refresh tokens

**Dashboard/Reporting Entry:**
- Location: `apps/workflow/dashboard_views.py:DashboardView`
- Triggers: GET `/api/v1/dashboard/`
- Responsibilities: Return counts (pending approval, approved, rework, etc.) for each document type

## Error Handling

**Strategy:** Fail fast with descriptive messages; use DRF exception classes.

**Patterns:**
- **ValidationError:** Raised when serializer validation fails or business rule violated (e.g., missing comment on reject action)
  - Response: HTTP 400 with `{"detail": "..."}` or field-specific errors
- **PermissionDenied:** Raised when user role insufficient or workflow state forbids action
  - Response: HTTP 403 with `{"detail": "Your role (MAKER) is not allowed to perform 'APPROVE'."}`
- **ObjectDoesNotExist:** Caught in service layer when related model missing (e.g., no CI linked to PL)
  - Response: HTTP 400 with descriptive message
- **FileResponse (PDF):** Streamed directly; if PDF generation fails mid-stream, HTTP error sent before file buffer exhausted

## Cross-Cutting Concerns

**Logging:** 
- AuditLog table: Every status transition logged with user, timestamp, from/to status, action, comment
- No separate logging service; audit data IS the logging mechanism

**Validation:**
- Serializer-level: Field type checks, required fields, range validation (e.g., decimal precision)
- Service-level: Business rule checks (workflow transitions, comment requirements, cascade rules)
- Database-level: Constraints on unique fields (pi_number, pl_number, etc.), on_delete policies

**Authentication:**
- Backend: JWT via rest_framework_simplejwt; every endpoint decorated with `@permission_classes([IsAuthenticated])` or similar
- Frontend: localStorage stores access/refresh tokens; Axios interceptor attaches bearer token to every request; 401 triggers refresh + retry

**Authorization:**
- Granular permission classes in `apps/accounts/permissions.py`: `IsMakerOrAdmin`, `IsChecker`, `IsSuperAdmin`, `IsAnyRole`
- Assigned at ViewSet method level (e.g., `create` requires `IsMakerOrAdmin`)
- WorkflowService enforces transition rules per role

**Multi-tenancy (Implicit):**
- Single tenant instance; all users belong to same organisation context
- Assumption: Company Admin manages all users; no cross-org visibility
- If multi-tenant needed in future: add Organisation FK to User model, filter all queries by user.organisation

---

*Architecture analysis: 2026-07-26*
