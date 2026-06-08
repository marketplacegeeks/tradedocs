# TradeDocs — Session Memory

## Completed
- Bootstrap: project structure, .venv (at `.venv/`), docker-compose, initial Django migrations committed.
- pytest.ini fixed (missing [pytest] header added).
- PostgreSQL running via Docker Compose (docker-compose.yml at project root).
- **Layer 1 — `accounts` app** ✓ (Custom User model, JWT auth, permission classes, 26 tests)
- **Layer 1 — `master_data` reference tables** ✓ (7 lookup models, all endpoints, 41 tests)
- **Layer 1 — Organisation model (FR-04)** ✓ (Organisation, OrganisationAddress, OrganisationTag, OrganisationTaxCode via address fields, full API + tests)
- **Layer 1 — Bank master (FR-05)** ✓ (Bank, Currency, intermediary fields, SWIFT/IBAN validation)
- **Layer 1 — TCTemplate (FR-07)** ✓
- **Layer 1 — TypeOfPackage** ✓
- **Layer 2 — workflow app** ✓ (WorkflowService, AuditLog, status transitions)
- **Layer 2 — Proforma Invoice (FR-09)** ✓ (header, line items, charges, PDF, workflow)
- **Layer 2 — Packing List (FR-14)** ✓ (header, containers, container items, PDF, workflow, copy-container)
- **Layer 2 — Commercial Invoice (FR-15)** ✓ (wizard, line item aggregation, two-mode PDF, workflow)
- **Layer 2 — Purchase Order app** ✓ (exists in apps/purchase_order/)
- **Currency support** ✓ (dynamic currency on PI/PL/CI — removed hardcoded USD; latest feature as of session end)

## Dev Server Commands
- PostgreSQL: already running via `docker-compose up -d` (docker-compose.yml at root)
- Django: `source .venv/bin/activate && python manage.py runserver 8000`
- Frontend: `cd frontend && npm run dev` (Vite, runs on port 5173)
- venv is at `.venv/` (NOT `venv/`)

## Patterns & Notes
- factory-boy: use `@factory.post_generation` with explicit `self.save()` for password setting.
- CountryFactory iso2/iso3 sequences: use letter-pair formula `chr(65 + (n//26)%26) + chr(65 + n%26)` — never use string slicing `[:2]` on sequences (collisions when n≥10).
- Settings use `python-decouple`. DB config uses DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT (not DATABASE_URL) for local dev.
- `apps/accounts/apps.py` uses `label = "accounts"` to avoid Django admin conflicts.
- OrganisationAddress has IEC + tax fields inlined (not a separate OrganisationTaxCode model — it evolved differently from original architecture doc).
- OrganisationTag includes VENDOR tag (beyond the original 4 in requirements).

- **COA feature (FR-COA-01 through FR-COA-13)** ✓ — all 6 stages complete:
  - Stage 1: master_data additions — Product, ProductGrade, TestParameter, TestMethod, ProductTestTemplate, ProductTestTemplateRow (migration 0018)
  - Stage 2: apps/certificate_of_analysis/ — CertificateOfAnalysis, COAParameter, document number generation, full API, workflow
  - Stage 6: pdf/certificate_of_analysis.py — in-memory PDF, never written to disk
  - Stage 3-5: Frontend — src/api/coa.ts, src/pages/coa/{COAListPage,COAFormPage,COADetailPage}.tsx, Products/TestParameters/TestMethods tabs on ReferenceDataPage, COA sidebar entry
  - Tests: 56 tests, 99% coverage (apps/certificate_of_analysis/tests/)

## Patterns & Notes (additions)
- Custom User model uses `.full_name` NOT `.get_full_name()` — fix serializers accordingly
- AuditLog uses `performed_at` field NOT `created_at` — check AuditLogSerializer fields
- COA uses PI_TRANSITIONS (same workflow state machine as PI) — registered in WorkflowService
- COA master data migration is 0018_coa_master_data (0016/0017 already existed before it)

## Active Task
None — COA feature just completed.

## Failed / Unresolved
- None known.
