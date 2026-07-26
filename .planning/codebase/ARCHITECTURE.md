# Architecture

**Analysis Date:** 2026-06-20

## Pattern Overview

**Overall:** Django REST Framework backend with React TypeScript frontend, following a **multi-tier layered architecture** with domain-driven app separation.

**Key Characteristics:**
- Monolithic Django backend with modular Django apps (accounts, master_data, proforma_invoice, packing_list, commercial_invoice, workflow, purchase_order, certificate_of_analysis)
- REST API-first design with explicit permission classes on every endpoint
- Workflow state machine enforced through a centralized `WorkflowService` (single source of truth for all document transitions)
- Frontend driven by React + React Router with context-based auth and React Query for data fetching
- PDF generation in-memory using ReportLab, streamed directly (never written to disk)

## Layers

**Presentation (Frontend):**
- Purpose: React SPA with role-based UI routing and form handling
- Location: `frontend/src/`
- Contains: Page components, form components, API client modules, auth context, design utilities
- Depends on: Backend REST API, localStorage for auth tokens
- Used by: End users (Makers, Checkers, Company Admins, Super Admins)

**API Gateway (Django REST Framework):**
- Purpose: REST endpoint layer that validates requests, enforces permissions, serializes responses
- Location: `apps/*/views.py`, `apps/*/urls.py`
- Contains: ViewSets, APIViews, custom permission classes, serializers for request/response validation
- Depends on: Models, Services, Workflow Service
- Used by: Frontend via Axios HTTP calls; reports service

**Business Logic (Services & Models):**
- Purpose: Core domain logic isolated from HTTP concerns
- Location: `apps/*/services.py`, `apps/*/models.py`
- Contains: Document generation logic, workflow transitions, validation rules, document numbering
- Depends on: Database, transaction.atomic() for consistency
- Used by: Views, Workflow Service, other services

**Data Access (Models & ORM):**
- Purpose: Django ORM models representing domain entities
- Location: `apps/*/models.py`
- Contains: ProformaInvoice, PackingList, CommercialInvoice, User, Organisation, and related models
- Depends on: PostgreSQL database, Django migrations
- Used by: Services, Views, Admin interface

**Master Data (Reference Tables):**
- Purpose: Lookup tables for organisations, countries, ports, banks, payment terms, incoterms, UOMs
- Location: `apps/master_data/models.py`
- Contains: Country, Port, Location, Organisation, Bank, Incoterm, UOM, PaymentTerm, PreCarriageBy, Currency, CurrencyRate
- Depends on: Database
- Used by: All document types via foreign keys with `on_delete=PROTECT`

**Workflow Coordination:**
- Purpose: Centralized state machine enforcing all status transitions and audit trails
- Location: `apps/workflow/services.py`, `apps/workflow/models.py`
- Contains: WorkflowService (handles PI, PL+CI joint, PO, COA transitions), AuditLog model (immutable records)
- Depends on: Models, User roles
- Used by: All document views when submitting, approving, rejecting, reworking documents

**PDF Generation:**
- Purpose: In-memory PDF rendering and streaming
- Location: `pdf/` (separate from Django apps)
- Contains: Generators for PI, PL, CI, PO, COA using ReportLab
- Depends on: Models, serializer data
- Used by: Document detail views via @action endpoints that return FileResponse

## Data Flow

**Document Creation & Submission Flow:**

1. User (Maker) fills out form in React component (`frontend/src/pages/proforma-invoice/ProformaInvoiceCreatePage.tsx`)
2. Form submits POST to `POST /api/v1/proforma-invoices/` → `ProformaInvoiceViewSet.create()`
3. View calls serializer `ProformaInvoiceSerializer.create()` which:
   - Calls `ProformaInvoiceService.generate_document_number()` to get unique PI-YYYY-NNNN
   - Creates ProformaInvoice record with status=DRAFT, created_by=request.user
   - Creates linked LineItem and Charge records
4. Response returns created document to frontend
5. User clicks "Submit for Approval" → POST to `POST /api/v1/proforma-invoices/{id}/submit-action/`
6. View calls `WorkflowService.transition()` which:
   - Validates action is allowed from current status (DRAFT → PENDING_APPROVAL)
   - Validates user role (MAKER can submit)
   - Validates comment if required
   - Updates document.status = PENDING_APPROVAL in transaction.atomic()
   - Creates AuditLog entry (same transaction)
7. Frontend polls or receives notification; document appears in Checker's queue

**Document Approval Flow:**

1. Checker views document detail page, sees "Approve" button
2. Clicks button → POST to `/api/v1/proforma-invoices/{id}/approve-action/` with comment
3. View calls `WorkflowService.transition()` with action="APPROVE"
4. Service validates:
   - Current status is PENDING_APPROVAL
   - User role is CHECKER (or COMPANY_ADMIN)
   - Creator ≠ Approver (unless admin)
5. Updates status to APPROVED, writes AuditLog
6. PDF can now be generated via `GET /api/v1/proforma-invoices/{id}/download-pdf/`

**PDF Streaming Flow:**

1. Frontend calls `GET /api/v1/proforma-invoices/{id}/download-pdf/`
2. View retrieves document, calls `pdf.proforma_invoice.generate()` passing model instance
3. ReportLab generator builds PDF in-memory (BytesIO)
4. View returns `FileResponse(pdf_buffer, content_type='application/pdf', filename='...')`
5. Browser receives binary stream and triggers download

**State Management:**

- Frontend auth: `AuthContext` in `frontend/src/store/AuthContext.tsx` stores user + tokens in localStorage
- Status enum: `DOCUMENT_STATUS` in `frontend/src/utils/constants.ts` (mirrors backend `apps/workflow/constants.py`)
- Backend status: Stored in `document.status` CharField (choices from `DOCUMENT_STATUS_CHOICES`)
- Audit trail: Every transition recorded in `AuditLog` with from_status, to_status, performed_by, performed_at, comment

## Key Abstractions

**WorkflowService (Transition State Machine):**
- Purpose: Single authority for all document status transitions
- Examples: `apps/workflow/services.py`
- Pattern: Static method `transition(document, document_type, action, performed_by, comment)` that:
  - Looks up allowed transitions in transition table (PI_TRANSITIONS, PLCI_TRANSITIONS, PO_TRANSITIONS)
  - Checks user role permission
  - Validates mandatory comments (REJECT, REWORK, PERMANENTLY_REJECT)
  - Performs transition inside `transaction.atomic()` with AuditLog creation
  - Cascades PERMANENTLY_REJECTED status to linked documents

**Document Number Generation:**
- Purpose: Guarantee unique, formatted document numbers
- Examples: `apps/proforma_invoice/services.py`, `apps/packing_list/services.py`, `apps/commercial_invoice/services.py`
- Pattern: `select_for_update()` lock on all records for current year, count, return `PI-YYYY-NNNN`, `PL-YYYY-NNNN`, `CI-YYYY-NNNN`

**Serializer Layering:**
- Purpose: Separate read vs. write serialization, embed nested relationships
- Examples: `ProformaInvoiceListSerializer` (list only), `ProformaInvoiceSerializer` (create/update with nested items)
- Pattern: Read-only fields for computed totals, writable fields for input, nested serializers for line items/charges

**Master Data ForeignKey Pattern:**
- Purpose: Prevent accidental deletion of reference data that documents depend on
- Examples: All FK to `master_data.Organisation`, `master_data.Country`, `master_data.Port` use `on_delete=PROTECT`
- Pattern: Ensures data integrity; trying to delete referenced master data raises IntegrityError

**Soft Delete (is_active):**
- Purpose: Never hard-delete users or organisations; retain audit history
- Examples: `User.is_active`, `Organisation.is_active`
- Pattern: Queries filter `is_active=True` by default, but data is never removed from DB

## Entry Points

**Backend Entry:**
- Location: `tradetocs/urls.py` (main URL router)
- Triggers: HTTP request from frontend
- Responsibilities: Route to appropriate app URL pattern, load middleware

**Frontend Entry:**
- Location: `frontend/src/main.tsx` (React root)
- Triggers: Browser page load
- Responsibilities: Initialize providers (Router, Query, Auth, Ant Design), render App component

**API Entry Points (Key):**
- `POST /api/v1/auth/login/` → `TokenObtainPairView` (JWT token pair)
- `GET /api/v1/auth/me/` → `MeView` (current user profile)
- `POST /api/v1/proforma-invoices/` → `ProformaInvoiceViewSet.create()` (create PI)
- `POST /api/v1/proforma-invoices/{id}/submit-action/` → workflow transition action
- `POST /api/v1/packing-lists/` → `PackingListViewSet.create()` (creates PL + CI together)
- `GET /api/v1/proforma-invoices/{id}/download-pdf/` → stream PDF

**Dashboard Entry:**
- Location: `GET /api/v1/dashboard/` → `DashboardView` in `apps/workflow/dashboard_views.py`
- Triggers: User navigates to dashboard
- Responsibilities: Aggregate pending documents, counts by status, summary for each user role

## Error Handling

**Strategy:** REST exception handling via DRF's `@api_view` decorator and explicit exception raising in views/services.

**Patterns:**

- **Validation Error:** `rest_framework.exceptions.ValidationError` for business rule violations (e.g., missing comment on REJECT)
  - Returns HTTP 400 with detail dict keyed by field name
  - Example: `{"comment": "A comment is required when performing 'REWORK'."}`

- **Permission Denied:** `rest_framework.exceptions.PermissionDenied` for role-based access violations
  - Returns HTTP 403
  - Example: "Your role (MAKER) is not allowed to perform 'APPROVE'."

- **Not Found:** DRF's automatic 404 when model instance doesn't exist
  - Returns HTTP 404

- **Integrity Error:** DB constraint violation (e.g., duplicate pi_number, FK PROTECT)
  - Caught and wrapped as 400 ValidationError with detail message
  - Prevents leaking database error details to frontend

## Cross-Cutting Concerns

**Logging:** Console logging via Python `logging` module; structured logs in production via Django settings

**Validation:** 
- **Model-level:** DecimalField constraints (max_digits, decimal_places) for monetary and weight fields
- **Serializer-level:** DRF field validators, custom `validate_*` methods for business rules
- **View-level:** WorkflowService and custom permission classes for state/role validation

**Authentication:** 
- Backend: JWT (SimpleJWT) stored in access_token / refresh_token cookies
- Frontend: Tokens stored in localStorage; `AuthContext` tracks user identity
- Every API endpoint (except /login/) requires `Authorization: Bearer <token>` header or 401 response

**Authorization:**
- Role-based: `permission_classes` on every view (MAKER, CHECKER, COMPANY_ADMIN, SUPER_ADMIN)
- Document-level: Can only edit documents you created (creator check in WorkflowService)
- Custom permission classes: `IsAnyRole`, `IsCompanyAdmin`, `IsSuperAdmin` in `apps/accounts/permissions.py`

**Pagination:** `StandardPageNumberPagination` in `tradetocs/pagination.py` applied to list views

**Filtering:** Django Filter + DRF's `DjangoFilterBackend` for status, created_by, date ranges on list endpoints

---

*Architecture analysis: 2026-06-20*
