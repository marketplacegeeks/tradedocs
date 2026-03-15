# Technical Architecture — TradeDocs

**Version:** 1.0
**Last Updated:** 2026-03-15
**Status:** Authoritative — read this before every development task

---

## 1. System Overview

TradeDocs is a web application for a single trading house to create, review, approve, and export three types of trade documents: Proforma Invoice, Packing List, and Commercial Invoice. All users belong to one organisation and operate under a maker–checker approval workflow, where a Maker drafts documents and a Checker approves or rejects them before they are finalised.

**Architecture pattern:** REST API backend (Django) + React single-page application frontend. The two are fully decoupled — the backend exposes a versioned JSON API, the frontend consumes it. There is no server-rendered HTML for the application itself.

**Why this pattern:** The document forms are complex and highly interactive (auto-calculated fields, multi-step wizards, live totals). A React frontend handles this better than Django templates. The decoupled pattern also lets the API be reused if a mobile app or integration is added later.

---

## 2. Tech Stack

### Backend

| Tool / Library | What it does |
| --- | --- |
| Python 3.12 | Programming language |
| Django 5.x | Web framework; handles models, ORM, admin, migrations |
| Django REST Framework (DRF) | Turns Django models into a JSON API with authentication and permissions |
| djangorestframework-simplejwt | Issues and validates JWT tokens [short-lived login tokens] for the API |
| django-cors-headers | Allows the React frontend (different port/domain) to call the API |
| django-filter | Adds filtering and search to API list endpoints |
| psycopg2-binary | Driver that lets Django talk to PostgreSQL |
| ReportLab | Generates PDF files from Python code |
| Pillow | Required by ReportLab for image handling in PDFs |
| gunicorn | Production web server that runs Django on Railway |
| python-decouple | Reads environment variables from a `.env` file cleanly |
| pytest-django | Testing framework for Django |
| factory-boy | Creates test data (fake organisations, documents, etc.) for tests |

### Frontend

| Tool / Library | What it does |
| --- | --- |
| React 18 | UI library; builds the interactive forms and pages |
| TypeScript | Typed JavaScript; catches errors before the code runs |
| Vite | Build tool; fast local dev server and production bundler |
| React Router v6 | Handles navigation between pages without a full page reload |
| TanStack Query (React Query) v5 | Fetches, caches, and syncs all API data; replaces Redux for server state |
| Axios | HTTP client that calls the Django API; handles JWT token attachment automatically |
| React Hook Form | Manages complex form state (validation, errors, submission) efficiently |
| Zod | Validates form data shapes in TypeScript before sending to the API |
| Ant Design (antd) | UI component library; provides tables, forms, modals, steps wizard, dropdowns |
| dayjs | Lightweight date formatting and manipulation library |
| React Context API | Stores the current user's identity and role in memory — no external library needed |

### Infrastructure

| Tool | What it does |
| --- | --- |
| PostgreSQL (Railway managed) | Primary database; stores all application data |
| Railway | Cloud platform that hosts and runs all services |
| GitHub | Source code repository; Railway auto-deploys on push to `main` |

---

## 3. Django App Structure

Each Django app maps to one functional area. Apps are created under a `apps/` directory inside the project root.

```
tradetocs/              ← Django project root (settings, urls, wsgi)
apps/
  accounts/             ← User model, login, roles, password management
  master_data/          ← All master data: Organisations, Banks, Countries, Ports,
                           Locations, Incoterms, UOM, PaymentTerms, PreCarriageBy,
                           T&C Templates
  proforma_invoice/     ← Proforma Invoice header, line items, additional charges, PDF
  packing_list/         ← Packing List header, containers, container items, PDF
  commercial_invoice/   ← Commercial Invoice, line items (aggregated from PL), PDF
  workflow/             ← Approval workflow engine, audit log, state transition rules
  reports/              ← Placeholder; read-only query endpoints for future reporting
pdf/                    ← PDF generation utilities (ReportLab); imported by document apps
```

**Why separate apps per document type:** Each document type has its own models, serializers, PDF layout, and workflow behaviour. Keeping them separate prevents any one file from becoming unmanageably large and makes it possible to work on one document type without touching others.

---

## 4. Database

### Core Models and Relationships

```
User
  ├── role: COMPANY_ADMIN | CHECKER | MAKER
  └── is_active: bool

Organisation
  ├── name, iec_code, is_active
  ├── → OrganisationAddress (one or more; at least one required)
  │     └── address_type: REGISTERED | FACTORY | OFFICE
  │         line1, line2, city, state, pin
  │         country → Country
  │         email, contact_name, phone_country_code, phone_number
  ├── → OrganisationTaxCode (zero or more)
  │     └── tax_type, tax_code
  └── → OrganisationTag (one or more)
        └── tag: EXPORTER | CONSIGNEE | BUYER | NOTIFY_PARTY

Bank
  └── nickname, beneficiary_name, bank_name
      bank_country → Country
      branch_address, account_number, account_type, currency
      swift_code, iban, routing_code

Country / Port / Location / Incoterm / UOM / PaymentTerm / PreCarriageBy / TCTemplate
  └── Simple lookup tables; managed by Company Admin

ProformaInvoice
  ├── exporter → Organisation (tagged EXPORTER)
  ├── consignee → Organisation (tagged CONSIGNEE)
  ├── buyer → Organisation (tagged BUYER), nullable
  ├── payment_terms → PaymentTerm
  ├── bank → Bank, nullable
  ├── incoterms → Incoterm
  ├── [shipping fields] → Port, Location, PreCarriageBy
  ├── tc_template → TCTemplate, nullable
  ├── tc_content: TextField (snapshot stored at creation)
  ├── status: DRAFT | PENDING_APPROVAL | APPROVED | REWORK | PERMANENTLY_REJECTED
  ├── pi_number: CharField (auto-generated, unique)
  ├── created_by → User
  ├── → ProformaInvoiceLineItem (one or more before submission)
  └── → ProformaInvoiceCharge (zero or more; for additional charges like bank fees)

ProformaInvoiceLineItem
  └── pi → ProformaInvoice
      hsn_code, item_code, description, quantity (3dp), uom → UOM
      rate_usd (2dp), amount_usd (calculated, stored)

ProformaInvoiceCharge
  └── pi → ProformaInvoice
      description, amount_usd (2dp)

PackingList
  ├── proforma_invoice → ProformaInvoice
  ├── exporter → Organisation, consignee → Organisation, buyer → Organisation nullable
  ├── notify_party → Organisation nullable
  ├── [all shipping fields mirrored from PI, overridable]
  ├── [order references: po, lc, bl, so, other — each with number + date]
  ├── status: DRAFT | PENDING_APPROVAL | APPROVED | REWORK | PERMANENTLY_REJECTED
  ├── pl_number: CharField (auto-generated, unique)
  ├── created_by → User
  └── → Container (one or more)

Container
  ├── packing_list → PackingList
  ├── container_ref, marks_numbers, seal_number
  ├── net_weight (3dp), tare_weight (3dp), gross_weight (3dp, computed on save)
  └── → ContainerItem (one or more)

ContainerItem
  └── container → Container
      hsn_code, item_code, packages_kind, description
      quantity (3dp), uom → UOM, batch_details

CommercialInvoice
  ├── packing_list → PackingList (must be APPROVED at creation time)
  ├── bank → Bank
  ├── ci_number: CharField (auto-generated, overridable by Maker)
  ├── fob_rate (2dp), freight (2dp), insurance (2dp), lc_details
  ├── status: DRAFT | PENDING_APPROVAL | APPROVED | REJECTED | DISABLED
  ├── created_by → User
  └── → CommercialInvoiceLineItem (aggregated from PL at creation, stored as snapshot)

CommercialInvoiceLineItem
  └── ci → CommercialInvoice
      item_code, uom → UOM, hsn_code, description, packages_kind
      total_quantity (3dp), rate_usd (2dp, entered by Maker), amount_usd (computed)

AuditLog
  └── document_type: CharField (e.g. "proforma_invoice")
      document_id: PositiveIntegerField
      document_number: CharField (snapshot of number at time of action)
      action: CharField (e.g. SUBMITTED, APPROVED, REJECTED, PERMANENTLY_REJECTED)
      from_status: CharField
      to_status: CharField
      comment: TextField (nullable)
      performed_by → User
      performed_at: DateTimeField (auto_now_add)

SignedCopyUpload
  └── document_type, document_id, file: FileField, uploaded_by → User, uploaded_at
```

### Indexing & Constraint Decisions

| Decision | Reason |
| --- | --- |
| Index on `status` for all three document models | Most list views filter by status |
| Index on `created_by` for all three document models | Makers filter to their own documents |
| Index on `(document_type, document_id)` on AuditLog | Audit trail queries always filter by these two |
| `PROTECT` on all FK references to master data | Prevents deleting a Bank or Port that is used on a document |
| `pi_number`, `pl_number`, `ci_number` are `unique=True` | Enforced at DB level, not just application level |
| `Organisation.is_active` instead of deletion | Organisation records are never hard-deleted |
| `gross_weight` stored (not only computed) on Container | PDF generation reads it directly; recomputed on every save of `net_weight` or `tare_weight` |
| All monetary amounts: `DecimalField(max_digits=15, decimal_places=2)` | Avoids floating-point rounding errors |
| All weights: `DecimalField(max_digits=12, decimal_places=3)` | Matches the 3 decimal place precision in requirements |

---

## 5. API Design

### URL Structure

All API endpoints are prefixed with `/api/v1/`.

```
/api/v1/
  auth/
    login/                     POST — returns access + refresh JWT tokens
    logout/                    POST — blacklists the refresh token
    token/refresh/             POST — exchanges refresh token for new access token
    me/                        GET — returns current user's profile and role

  master-data/
    organisations/             GET, POST
    organisations/{id}/        GET, PUT, PATCH
    organisations/{id}/addresses/     GET, POST
    organisations/{id}/addresses/{aid}/  GET, PUT, DELETE
    banks/                     GET, POST
    banks/{id}/                GET, PUT, PATCH
    countries/                 GET, POST, PUT (lookup data)
    ports/                     GET, POST, PUT
    locations/                 GET, POST, PUT
    incoterms/                 GET, POST, PUT
    uom/                       GET, POST, PUT
    payment-terms/             GET, POST, PUT
    pre-carriage/              GET, POST, PUT
    tc-templates/              GET, POST
    tc-templates/{id}/         GET, PUT, PATCH

  proforma-invoices/           GET (list), POST (create)
  proforma-invoices/{id}/      GET (detail), PUT, PATCH
  proforma-invoices/{id}/line-items/       GET, POST
  proforma-invoices/{id}/line-items/{lid}/ PUT, DELETE
  proforma-invoices/{id}/charges/          GET, POST
  proforma-invoices/{id}/charges/{cid}/    PUT, DELETE
  proforma-invoices/{id}/workflow/         POST — body: { action, comment }
  proforma-invoices/{id}/pdf/              GET — streams PDF file
  proforma-invoices/{id}/audit-log/        GET

  packing-lists/               GET, POST
  packing-lists/{id}/          GET, PUT, PATCH
  packing-lists/{id}/containers/           GET, POST
  packing-lists/{id}/containers/{cid}/     GET, PUT, DELETE
  packing-lists/{id}/containers/{cid}/items/      GET, POST
  packing-lists/{id}/containers/{cid}/items/{iid}/ PUT, DELETE
  packing-lists/{id}/containers/{cid}/copy/        POST — copies container + items
  packing-lists/{id}/workflow/             POST — body: { action, comment }
  packing-lists/{id}/pdf/                  GET
  packing-lists/{id}/audit-log/            GET

  commercial-invoices/         GET, POST (wizard submit)
  commercial-invoices/{id}/    GET, PUT, PATCH (edit Draft/Rejected)
  commercial-invoices/{id}/line-items/     GET — read-only; POST not available
  commercial-invoices/{id}/workflow/       POST
  commercial-invoices/{id}/pdf/            GET — query param: ?mode=draft|final
  commercial-invoices/{id}/audit-log/      GET

  wizard/
    eligible-consignees/       GET — consignees with ≥1 Approved PL
    approved-packing-lists/    GET — query param: ?consignee_id=X
    aggregate-line-items/      GET — query param: ?packing_list_id=X

  users/                       GET (list), POST (invite)
  users/{id}/                  GET, PATCH (role, is_active)

  signed-copies/               POST — upload scanned signed copy
  signed-copies/{id}/          GET — download
```

### Authentication

**Method:** JWT (JSON Web Tokens) via `djangorestframework-simplejwt`.

- Login returns an **access token** (expires in 30 minutes) and a **refresh token** (expires in 7 days).
- The React frontend stores tokens in `localStorage` [a browser storage area]. Every API request attaches the access token in the `Authorization: Bearer <token>` header (handled automatically by the Axios interceptor).
- When the access token expires, Axios automatically calls `/api/v1/auth/token/refresh/` with the refresh token and retries the original request.
- Logout blacklists the refresh token server-side so it cannot be reused.

### Authorization (Roles → Permissions)

Custom DRF permission classes are defined in `apps/accounts/permissions.py`. These are composed on each view.

| Permission Class | Grants access to |
| --- | --- |
| `IsCompanyAdmin` | Users with role `COMPANY_ADMIN` |
| `IsCheckerOrAdmin` | Users with role `CHECKER` or `COMPANY_ADMIN` |
| `IsAnyRole` | Any authenticated user (Maker, Checker, Company Admin) |
| `IsDocumentOwner` | Maker who created the document (for edit/delete operations on Draft) |
| `CanPerformWorkflowAction` | Evaluated per action in `WorkflowService`; not a blanket permission |

Document write permissions follow the rule: **only the Maker can create/edit, and only in Draft or Rework state**. Checkers and Admins can read everything but can only trigger workflow actions (approve, reject, etc.) — never edit content fields.

### Workflow Endpoint Convention

All state transitions use a single POST to `/{document}/{id}/workflow/` with a JSON body:

```json
{ "action": "SUBMIT" | "APPROVE" | "REJECT" | "PERMANENTLY_REJECT" | "DISABLE", "comment": "optional or required" }
```

This single endpoint routes to `WorkflowService`, which validates the action, enforces role rules, transitions the status, writes the audit log, and triggers notifications. No status field is ever updated directly in any other view.

---

## 6. React Frontend

### Folder Structure

```
frontend/
  public/
  src/
    api/                  ← One file per resource (e.g. proformaInvoice.ts, bank.ts)
                            All Axios calls live here. Pages never call Axios directly.
    assets/               ← Logos, fonts, static images
    components/
      common/             ← Shared UI: StatusBadge, AuditLogDrawer, PDFDownloadButton,
                             ConfirmModal, WorkflowActionButton, NumberDisplay
      layout/             ← AppShell, Sidebar, TopBar, PageHeader
      documents/          ← Shared document UI: PartyBlock, ShippingBlock, AddressSelector
    hooks/
      useAuth.ts          ← Returns current user, role, and logout function
      useWorkflowAction.ts← Handles workflow POST + optimistic UI update
      useDocumentPdf.ts   ← Triggers PDF download with correct filename
    pages/
      auth/
        LoginPage.tsx
      dashboard/
        DashboardPage.tsx
      proforma-invoice/
        ProformaInvoiceListPage.tsx    ← Index table with status filters
        ProformaInvoiceCreatePage.tsx  ← Header creation form
        ProformaInvoiceDetailPage.tsx  ← Header + line items + charges + workflow
      packing-list/
        PackingListListPage.tsx
        PackingListFormPage.tsx        ← Handles both create and edit
      commercial-invoice/
        CommercialInvoiceListPage.tsx
        CommercialInvoiceWizardPage.tsx  ← 5-step wizard
        CommercialInvoiceDetailPage.tsx  ← Read/edit view post-creation
      master-data/
        OrganisationListPage.tsx
        OrganisationFormPage.tsx
        BankListPage.tsx
        BankFormPage.tsx
        ReferenceDataPage.tsx          ← Countries, Ports, Incoterms, UOM, etc. (tabbed)
        TCTemplateListPage.tsx
        TCTemplateFormPage.tsx
      user-management/
        UserListPage.tsx
        UserFormPage.tsx
      reports/
        ReportsPage.tsx                ← Placeholder page
    store/
      AuthContext.tsx      ← Stores { user, role, isAuthenticated }; populated on login
    utils/
      formatters.ts        ← formatCurrency(), formatWeight(), formatDate(), amountInWords()
      constants.ts         ← Document status enums, role constants — mirror of backend enums
      validators.ts        ← Zod schemas for form validation
    App.tsx                ← Route definitions + ProtectedRoute wrapper
    main.tsx
```

### State Management

| State type | Tool | Reason |
| --- | --- | --- |
| Server data (documents, master data, lists) | TanStack Query | Handles caching, refetching, loading/error states automatically |
| Current user / auth session | React Context (`AuthContext`) | Simple; only one piece of global state needed |
| Form data | React Hook Form | Isolates form re-renders; integrates cleanly with Zod validation |
| UI state (modal open/closed, selected tab) | Local `useState` in each component | No global UI state is shared across pages |

Redux is not used. For this application's scale and shape, TanStack Query + Context is sufficient and significantly simpler.

### Pages → Requirements Mapping

| Page | Requirements |
| --- | --- |
| `ProformaInvoiceCreatePage` | FR-09.1, FR-09.2, FR-09.3, FR-09.4 |
| `ProformaInvoiceDetailPage` | FR-09.5 (line items), FR-09.6 (PDF), FR-08 (workflow actions) |
| `PackingListFormPage` | FR-14.1–FR-14.9 (all in one form, create + edit mode) |
| `CommercialInvoiceWizardPage` | FR-15.1–FR-15.6 (5-step wizard) |
| `CommercialInvoiceDetailPage` | FR-15.7 (workflow), FR-15.8 (PDF) |
| `OrganisationFormPage` | FR-04.1–FR-04.4 |
| `BankFormPage` | FR-05 |
| `ReferenceDataPage` | FR-06 |
| `TCTemplateFormPage` | FR-07 |
| Any document page | FR-08 (workflow actions rendered based on role + status) |

### Role-Based UI Rules

A `ProtectedRoute` component checks `AuthContext` and redirects if the user lacks the required role. Within pages, action buttons (Submit, Approve, Reject, etc.) are conditionally rendered based on `user.role` and the document's `status`. The `WorkflowActionButton` component encapsulates this logic and is reused across all three document types.

---

## 7. Railway Deployment

### Services

| Service | Type | What runs |
| --- | --- | --- |
| `web` | Web service | Django + Gunicorn; handles all API requests |
| `db` | Managed PostgreSQL | Primary database |
| `frontend` | Static site | Vite-built React app served as static files |

The React build (`npm run build`) outputs to `frontend/dist/`, which Railway serves as a static site. The Django API and React frontend are **separate Railway services** with separate domains (e.g. `api.tradetocs.railway.app` and `app.tradetocs.railway.app`).

### Environment Strategy

Two environments: **development** (local) and **production** (Railway).

| Environment | Config |
| --- | --- |
| Local (dev) | `.env` file; SQLite or local PostgreSQL; `DEBUG=True` |
| Production | Railway environment variables; managed PostgreSQL; `DEBUG=False` |

### Environment Variable Naming Convention

All environment variables are `SCREAMING_SNAKE_CASE` with a `TRADETOCS_` prefix for app-specific variables.

```
# Core
TRADETOCS_SECRET_KEY
TRADETOCS_DEBUG
TRADETOCS_ALLOWED_HOSTS

# Database
DATABASE_URL               ← Set automatically by Railway PostgreSQL plugin

# Email
TRADETOCS_EMAIL_BACKEND
TRADETOCS_SENDGRID_API_KEY
TRADETOCS_DEFAULT_FROM_EMAIL

# JWT
TRADETOCS_ACCESS_TOKEN_LIFETIME_MINUTES
TRADETOCS_REFRESH_TOKEN_LIFETIME_DAYS

# Frontend
VITE_API_BASE_URL          ← The Django API URL; used by Vite at build time
```

---

## 8. Security

### Authentication Security
- Access tokens expire in 30 minutes. Refresh tokens expire in 7 days and are stored server-side (blacklisted on logout).
- Passwords are hashed using Django's default PBKDF2 algorithm with a SHA-256 hash. No plain text passwords are ever stored or logged.
- The "Forgot Password" flow is admin-managed (per requirements): Company Admin resets passwords manually via the User Management page. There is no email-based self-reset.

### Data Protection
- All traffic between browser, Railway services, and database is encrypted via TLS (HTTPS). Railway enforces this by default.
- Data at rest (database) is encrypted by Railway's managed PostgreSQL service.
- Personally identifiable information (contact names, emails, phone numbers) is stored in `OrganisationAddress` and never duplicated unnecessarily.

### Access Control
- Every API view declares explicit permission classes. No view defaults to "allow all authenticated users" without deliberate intent.
- Document content fields (exporter, line items, shipping fields) can only be written by a Maker, and only when the document is in `DRAFT` or `REWORK` state. The serializer and view both enforce this — the serializer makes fields read-only if the document is not in an editable state.
- Workflow actions (approve, reject, etc.) are validated entirely inside `WorkflowService`, which checks both the user's role and the document's current state before proceeding.
- CORS is configured to allow requests only from the known frontend domain. All other origins are rejected.

### Audit & Compliance
- Every document state change writes an `AuditLog` entry inside the same database transaction as the status update. If the log write fails, the state change is rolled back.
- Audit logs are never deleted by the application. Retention for 7 years is enforced by a database-level policy on the Railway PostgreSQL instance.

---

## 9. Constraints & Conventions

**This section is authoritative. Every line of code written for this project must comply with these rules.**

### General

1. **Never read this file and skip it.** Before starting any task, read this file to understand the conventions. If a task requires deviating from these conventions, update this file first and explain why.

2. **No new dependencies without updating this file.** If a new library is needed, add it to Section 2 with a plain-English explanation before using it.

3. **Django apps live under ****`apps/`****.** Never create an app at the project root. Import them as `apps.proforma_invoice.models` etc.

4. **Migrations must be committed.** Every model change requires a migration file checked in to version control. Never use `--fake` in production.

### Models

5. **All monetary amounts use ****`DecimalField(max_digits=15, decimal_places=2)`****.** Never use `FloatField` for money.

6. **All weights use ****`DecimalField(max_digits=12, decimal_places=3)`****.** Never use `FloatField` for weights.

7. **All FK references to master data use ****`on_delete=PROTECT`****.** This prevents accidental deletion of an Organisation, Bank, Port, etc. that is referenced by a document.

8. **Organisation records are never hard-deleted.** Set `is_active=False` instead. The same applies to User records.

9. **`gross_weight`**** on ****`Container`**** is always stored (never computed on-the-fly).** Recompute and save it whenever `net_weight` or `tare_weight` changes, using `Container.save()` override.

10. **Document status is always a string matching a ****`DocumentStatus`**** enum.** Define this enum in `apps/workflow/constants.py` and import it everywhere. Never hardcode status strings like `"draft"` in view or serializer code.

### Workflow

11. **All status transitions go through ****`WorkflowService`**** in ****`apps/workflow/services.py`****.** Never update a document's `status` field anywhere else — not in serializers, not in signals, not in management commands.

12. **`WorkflowService`**** must write an ****`AuditLog`**** entry in the same database transaction as the status update.** Use `transaction.atomic()` wrapping both operations.

13. **Permanently Rejected cascading is implemented only in ****`WorkflowService.permanently_reject()`****.** Never use a Django signal for cascade logic — signals are invisible and hard to debug.

14. **`Disabled`**** state is valid only for ****`CommercialInvoice`****.** `WorkflowService` must raise a `ValueError` if `DISABLE` action is attempted on a ProformaInvoice or PackingList.

15. **Mandatory comment enforcement:** `WorkflowService` must block any `REJECT`, `REWORK`, `PERMANENTLY_REJECT`, or `DISABLE` action if the `comment` field is empty. Raise a `ValidationError` with a clear message.

### Auto-Generated Numbers

16. **PI, PL, and CI numbers are generated inside a ****`select_for_update()`**** [database lock] transaction.** The sequence for each document type is determined by `COUNT(*) + 1` within a locked query. This prevents duplicate numbers if two users save simultaneously. Implement this in `apps/{document_app}/services.py` in a function called `generate_document_number()`.

17. **Number formats are fixed:**
  - Proforma Invoice: `PI-YYYY-NNNN` (4-digit, zero-padded)
  - Packing List: `PL-YYYY-NNNN`
  - Commercial Invoice: `CI-YYYY-NNNN`

### API & Serializers

18. **Serializers are state-aware.** For document serializers, fields that are not editable in the current state must be declared `read_only=True` dynamically based on the document's `status`. Do this in `__init__` using `self.fields['field_name'].read_only = True`.

19. **List endpoints must support filtering by ****`status`**** and ****`created_by`**** at minimum.** Use `django-filter` for this — do not write manual `filter()` calls in views.

20. **PDF endpoints stream the file directly from the view.** Use Django's `StreamingHttpResponse` or `FileResponse` with `content_type='application/pdf'`. Never write PDFs to disk and serve them — generate in memory.

21. **The CI wizard's line item aggregation is computed in ****`CommercialInvoiceService.aggregate_line_items(packing_list_id)`****.** This function is called when the Maker reaches Step 3 and its output is stored on the `CommercialInvoiceLineItem` rows at the point of CI creation — not recomputed later.

### Frontend

22. **All API calls live in ****`src/api/*.ts`**** files.** Page components and hooks import from these files. No component calls `axios` directly.

23. **Document status values and role constants in the frontend are imported from ****`src/utils/constants.ts`****.** This file mirrors the backend enums. Never hardcode a status string like `"DRAFT"` in a component.

24. **The ****`WorkflowActionButton`**** component handles all role + status checks for what actions are visible.** It takes `documentStatus`, `userRole`, and `documentType` as props and renders the correct buttons. Do not repeat this logic in individual pages.

25. **TanStack Query keys follow the pattern ****`[resource, id, subresource]`**, e.g. `['proforma-invoice', '123', 'line-items']`. Use these consistently to allow targeted cache invalidation.

26. **After a workflow action succeeds, invalidate the document query and the audit log query.** Do not optimistically update the status — refetch from the server to ensure consistency.

### Security

27. **Never log or print sensitive values** (passwords, tokens, PII such as email addresses or contact names) in any print statement, logger call, or error message.

28. **CORS is configured to the known frontend domain only.** Do not use `CORS_ALLOW_ALL_ORIGINS = True` in any environment, including development. Use `CORS_ALLOWED_ORIGINS` with the explicit localhost dev URL.

29. **Every DRF view class must explicitly declare ****`permission_classes`****.** The global default in settings is `IsAuthenticated` as a safety net, but it must never be relied upon as the sole permission check for sensitive endpoints.

30. **Email notifications are sent synchronously in WorkflowService.** Do not introduce Celery or any async task queue.

---

## Appendix: Document Lifecycle Summary (Quick Reference)

```
ProformaInvoice:
  DRAFT → PENDING_APPROVAL → APPROVED
                           → REWORK → DRAFT (Maker edits) → PENDING_APPROVAL
  Any state → PERMANENTLY_REJECTED (terminal; cascades to linked PLs and CIs)

PackingList:
  DRAFT → PENDING_APPROVAL → APPROVED
                           → REWORK → DRAFT → PENDING_APPROVAL
  Any state → PERMANENTLY_REJECTED (terminal; cascades to linked CIs)

CommercialInvoice:
  DRAFT → PENDING_APPROVAL → APPROVED → DISABLED (terminal)
                           → REJECTED → DRAFT (Maker edits) → PENDING_APPROVAL
  Any state → PERMANENTLY_REJECTED (terminal)
```

**PDF watermark rule:** DRAFT watermark on all states except APPROVED. APPROVED = clean final PDF.
**PDF access rule for Packing List:** Maker and Checker can only download PDF when status is APPROVED. Company Admin can download at any state.
**PDF access rule for Commercial Invoice:** Maker can download Draft PDF when DRAFT or REJECTED. Final PDF (all roles) only when APPROVED.
