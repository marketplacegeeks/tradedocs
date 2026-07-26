# Codebase Concerns

**Analysis Date:** 2026-07-26

## Tech Debt

**PDF Generation — Table Page Break Handling (Medium Priority)**
- Issue: Line-item tables in PDFs use `splitByRow=False`, which allows table rows to split mid-table across page breaks. This was introduced in commit 4766d7b to fix header repeat issues but reintroduced the original problem from bugs.md item #11.
- Files: `pdf/proforma_invoice.py` (line 404, 459, 479, etc.), `pdf/commercial_invoice_generator.py` (line 288, 425, 441, 447, etc.), `pdf/certificate_of_analysis.py` (line 226, 326), `pdf/purchase_order.py` (implied)
- Impact: Professional documents split mid-table; client finds layout unprofessional. Most problematic for multi-page documents where a 5-10 row table might start near the end of page 1 and continue on page 2.
- Fix approach: Wrap each document's line-item and detail tables in `KeepTogether([...])` Platypus container so the entire table shifts to the next page if it won't fit. This is different from header wrapping — isolates the table structure itself, not just the header. Packing List already uses this pattern (line 720: `KeepTogether([cont_header, weights_table, items_table])`); roll out to PI, CI, CIF, COA, PO.

**CASCADE vs PROTECT Cascade Delete Strategy (Medium Priority)**
- Issue: CommercialInvoiceLineItem uses `on_delete=CASCADE` (related to its parent CI), and Certificate of Analysis uses `on_delete=CASCADE` for parameters. While these are internal detail tables (not master data refs), the asymmetry means deleting a CI will cascade-delete all line items without warning, unlike PROTECT-constrained master data.
- Files: `apps/commercial_invoice/models.py` (line with LineItems FK), `apps/certificate_of_analysis/models.py` (FK to CertificateOfAnalysis)
- Impact: Low risk in practice (CIs and COAs are deleted via hard_delete endpoints with transaction safety), but violates the principle of explicit, constrained deletions that underpins the audit/workflow system.
- Fix approach: No immediate action needed — CIs and COAs are only deleted via explicit Super Admin endpoints inside atomic blocks, which is safe. Document the intentional CASCADE choice in a comment for future maintainers. If audit trail becomes a requirement, consider adding a soft-delete flag (is_deleted=False) to line items / parameters.

**Large Frontend Component Files (Low Priority)**
- Issue: Several frontend pages exceed 1,500 lines and handle multiple concerns (form validation, table management, PDF preview, etc.).
- Files: `frontend/src/pages/packing-list/PackingListCreatePage.tsx` (2,110 lines), `frontend/src/pages/purchase-order/PurchaseOrderFormPage.tsx` (1,365 lines), `frontend/src/pages/coa/COAFormPage.tsx` (1,256 lines)
- Impact: Testing these files is difficult; changes to one concern require retesting many others. IDE refactoring support becomes slower.
- Fix approach: Not urgent for v1.0. Future refactor: split container item form, COA parameter form, and PO item form into dedicated sub-components. Use form validation library (react-hook-form or similar) to centralize validation logic outside the component render tree.

## Known Bugs

**PDF Table Splitting (Partially Solved, Regressed)**
- Symptoms: When a document has many line items, a table may split across page breaks mid-row, leaving a partial row at the bottom of one page and continuing on the next. User finds this unprofessional.
- Files: All PDF generators in `pdf/`
- Trigger: Any document with line-item tables spanning 2+ pages and `splitByRow=False` on the table.
- Workaround: Manually add page breaks before tables, or keep line-item counts low (< 50 items per table).
- Status: Commit 4766d7b added header repeat functionality but disabled table-level `KeepTogether`. This was a trade-off: full-page tables now have repeating headers on multi-page docs, but tables can split mid-row. See bugsstatus.md item #11.

**Line-item Table Header Repetition vs Row Preservation (Architectural Trade-off)**
- Issue: ReportLab's Platypus tables with `repeatRows=1` require `splitByRow=True` to repeat headers correctly. Using `splitByRow=False` prevents splitting but loses automatic header repetition. Wrapping the entire table in `KeepTogether()` forces the whole table to the next page, but then headers won't repeat on a 20-row table that spans 3 pages.
- Files: All PDF generators
- Impact: Current approach prioritizes header repetition (good for multi-page readability) at the cost of potential mid-row splits (poor visual impression). The better UX would be headers-repeat + no-mid-row-splits, which may require custom `Platypus.Tabloid` subclass or paginating tables manually per chunk size.
- Fix approach: Investigate ReportLab's table rendering options (e.g., `Tabloid` wrapper or custom `RowSplitter`). If not available, implement manual chunking: if total rows > threshold, split into multiple 20-30-row tables, each with headers and each wrapped in `KeepTogether()`.

## Security Considerations

**Signed Copy Upload File Validation (Medium Priority)**
- Risk: `/packing-lists/{id}/signed-copy/` endpoint accepts any file type and stores it as a Django FileField. Current validation only checks file size (max 3 MB).
- Files: `apps/packing_list/views.py` (lines 426–462)
- Current mitigation: File size limit (3 MB) prevents extremely large uploads. FileField storage is delegated to Django's file storage backend (default: local filesystem under `MEDIA_ROOT`).
- Recommendations:
  1. Add MIME type whitelist (accept only PDF, image, or document formats).
  2. Scan uploaded files with a malware checker (e.g., ClamAV) before saving.
  3. Store signed copies in a separate, read-only directory or cloud storage (S3, not local filesystem).
  4. Log all file uploads with user, timestamp, file size, and hash for audit trail.

**No Rate Limiting on PDF Generation (Low Priority)**
- Risk: PDF generation endpoints (`/packing-lists/{id}/generate-pdf/`, `/proforma-invoices/{id}/generate-pdf/`, etc.) are not rate-limited, so a user could DoS the server by requesting large PDFs repeatedly.
- Files: `apps/packing_list/views.py` (lines 336–366, 369–397, 400–422), `apps/proforma_invoice/views.py`, `apps/commercial_invoice/views.py`
- Current mitigation: Django's `throttle_scope = "document_creation"` is applied to document creation endpoints, but not PDF generation. PDF endpoints use `@action(detail=True, methods=["get"])` with `permission_classes=[IsAnyRole]` and no throttle.
- Recommendations:
  1. Add a per-user rate limit (e.g., 10 PDF downloads per minute) to PDF generation endpoints using DRF's `ScopedRateThrottle`.
  2. Consider caching PDFs for 1–5 minutes (if they're expensive to generate and the document hasn't changed).
  3. Monitor PDF generation performance with timing instrumentation.

**CSRF Token Not Enforced on JSON API (Low Priority)**
- Risk: Frontend makes axios requests with `Authorization: Bearer <JWT>` header for all mutations (POST/PATCH/DELETE). Django's CSRF middleware is configured but doesn't enforce tokens on JWT-authenticated requests (standard practice).
- Files: `tradetocs/settings.py` (MIDDLEWARE and DRF DEFAULT_AUTHENTICATION_CLASSES)
- Current mitigation: JWT auth is token-based, not cookie-based session auth, so CSRF attacks are not applicable.
- Recommendations: No action needed — JWT authentication is inherently CSRF-safe. Document this in a security.md file for new contributors.

**Email Signals Not Validated / Not Integrated (Low Priority)**
- Risk: Email sending signals exist (`apps/accounts/signals.py` — invitation/activation emails) but the email backend is not configured in settings.py.
- Files: `apps/accounts/signals.py` (implied from memory.md), `tradetocs/settings.py`
- Current mitigation: Emails are not sent in development or staging because `EMAIL_BACKEND` is not configured; signals silently fail.
- Recommendations:
  1. Add a feature flag (env var `SEND_EMAILS=False` by default) to enable/disable email in different environments.
  2. Add integration test that verifies email signals are called (without actually sending).
  3. Document email configuration requirements for production deployment.

## Performance Bottlenecks

**N+1 Query Issues in List Views (Low Risk, Partially Addressed)**
- Problem: Many list endpoints fetch related objects. If not using `select_related()` or `prefetch_related()`, the endpoint makes one query per row.
- Files: All viewset list actions in `apps/*/views.py`
- Current state: ~53 occurrences of `select_related()`/`prefetch_related()` in the codebase, which is good. However, some list views may still have implicit N+1s from serializers that access related fields.
- Improvement path: Run `django-querycount` middleware locally on all list pages and identify any views with > 5 queries. Add `select_related()` / `prefetch_related()` for those. Test with `django.test.utils.CaptureQueriesContext` to assert query count in tests.

**PDF Generation Performance (Medium Priority)**
- Problem: PDF generation for large Packing Lists (50+ containers) can be slow (~2–5s per request) because ReportLab must render every table row in memory.
- Files: `pdf/packing_list_generator.py` (line 720, nested loop over containers and items)
- Cause: No caching of PDFs; every request re-renders from scratch. No pagination/chunking of large tables.
- Improvement path:
  1. Implement simple caching: store PDF in a temporary file/memory for 5 minutes if the document status is Approved (since Approved documents are read-only).
  2. Add a query count / row count check before PDF generation and warn the user if > 100 items.
  3. Consider lazy rendering for CI PDFs: only render line items for the current "page" (pagination on the backend).

**Packing List Rebuild on Every Container Edit (Low Priority)**
- Problem: `rebuild_ci_line_items()` is called on every container/container-item create/update/delete. If a Packing List has 100 containers, this rebuilds the CI 100 times in a bulk import scenario.
- Files: `apps/packing_list/views.py` (lines 599, 610, 629 — calls to `rebuild_ci_line_items()`), `apps/commercial_invoice/services.py` (the rebuild function)
- Cause: Each ContainerViewSet action calls `rebuild_ci_line_items()` individually; no batching.
- Improvement path:
  1. For bulk operations (import 100 containers), wrap them in a single transaction and call rebuild once at the end.
  2. Add a `defer_rebuild` context manager that accumulates changes and rebuilds only on exit.
  3. Current risk is low because typical workflows don't bulk-import 100 containers in one request — but API clients could trigger this.

## Fragile Areas

**WorkflowService Status Transitions (Low Risk, Well-Tested)**
- Files: `apps/workflow/services.py`, `apps/workflow/models.py`
- Why fragile: All document status changes must go through `WorkflowService.transition()` and `transition_joint()`. If new document types are added and not registered in `_get_transitions()`, they silently fail to transition. Tests currently cover all existing doc types (PI, PL, CI, PO, COA).
- Safe modification: Before adding a new document type, register it in `_get_transitions()` with explicit state machine definition. Add test for happy-path and permission-denial. Use type hints to enforce the contract.
- Test coverage: Workflow tests are in `apps/workflow/tests/` (implied) and `test_views.py` for each document type. ~737 passing tests (as of 2026-07-10). Good coverage overall.

**Commercial Invoice Quantity Aggregation (Medium Risk, Recently Fixed)**
- Files: `apps/commercial_invoice/services.py` (line 45 — rebuild_ci_line_items)
- Why fragile: Logic to sum quantities across containers is the foundation for all CI pricing. A bug here produces wildly wrong financial amounts. Was buggy in commit 4766d7b (used `net_material_weight` in KGS instead of `no_of_packages`), fixed in 4b878da.
- Safe modification: Any change to this function must be tested with:
  1. Single container with one item.
  2. Multiple containers with the same item_code + uom.
  3. Multiple items with different item_codes.
  4. Verify that amount = total_quantity × rate (using Decimal arithmetic, never float).
- Test coverage: Test added in packing_list/tests/test_views.py, but a dedicated test in commercial_invoice/tests/test_services.py would be more maintainable.

**PDF Generation with Master Data References (Low Risk)**
- Files: All PDF generators in `pdf/`
- Why fragile: PDFs call `.name` and `.code` on ForeignKey references (e.g., `invoice.incoterms.code`). If a related object is deleted or becomes null, PDF generation fails silently or with cryptic "AttributeError: 'NoneType' object has no attribute 'code'".
- Safe modification: All PDF generators use defensive `getattr(..., None)` and `safe()` helpers. See proforma_invoice.py lines 424–443 for the pattern. Maintain this pattern on any new fields added to PDFs.
- Test coverage: Integration tests should generate PDFs with and without optional fields (e.g., null bank, null incoterm).

**Certificate of Analysis Parameter Validation (Low Risk)**
- Files: `apps/certificate_of_analysis/models.py`, `apps/certificate_of_analysis/serializers.py`, `frontend/src/pages/coa/COAFormPage.tsx`
- Why fragile: COA allows free-text `specification` fields per parameter (fixed in commit 1b79481 to support `<` and `>` characters). If a future refactor limits this or adds regex validation, existing COAs with special characters may fail to load.
- Safe modification: Keep the CharField approach (current state). If regex validation is needed, test with existing data to ensure no false negatives.
- Test coverage: Test coverage in apps/certificate_of_analysis/tests/test_views.py. Good.

## Scaling Limits

**Document Number Generation Concurrency (Low Risk, Already Mitigated)**
- Current capacity: Document number sequences (PI/PL/CI/PO/COA) use `select_for_update()` to prevent duplicates. Max sequence value is 9,999 per year → max 9,999 documents per document type per year. After that, sequence wraps (manual intervention required).
- Limit: If the system scales to > 9,999 PIs per year, the sequence will overflow.
- Scaling path: Extend sequence to 5 digits (99,999 per year) by updating document number formats: `PI-YYYY-NNNN` → `PI-YYYY-NNNNN`. Requires migration to update all existing document numbers and updating PDF/frontend display logic.

**Database Connection Pool (Low Risk)**
- Current capacity: `django-db-gevent` (if using gevent) or standard Django connection pool (typically 5–10 connections).
- Limit: If concurrent users > connection pool size, requests queue up waiting for a connection.
- Scaling path: Monitor connection usage with Django debug toolbar or `django-silk`. Increase pool size if needed. Add database read replicas for heavy list/report queries.

**Frontend Bundle Size (Low Priority)**
- Current capacity: Main app bundle is bundled via Vite (no explicit analysis done). Node modules include react, axios, antd (UI lib), etc.
- Limit: If the frontend continues to grow (more pages, more dependencies), bundle size may exceed 1 MB, impacting load times on slow networks.
- Scaling path: Implement code splitting with React.lazy() for each page (already possible with Vite). Tree-shake unused ant-design components. Monitor bundle size in CI pipeline.

## Dependencies at Risk

**None Identified**
- All critical dependencies (Django 5.x, DRF, ReportLab, Vite, React) are actively maintained and widely used.
- No deprecated or end-of-life libraries detected in `requirements.txt` or `package.json`.

## Missing Critical Features

**User Invitation / Email Notifications (Partially Implemented)**
- Problem: Account creation is manual (super admin creates users in admin panel or via API). No self-service user invitation or email notifications.
- Blocks: Cannot scale user onboarding; all new users require manual admin intervention.
- Path: Implement email-based user invitation (FR-03.3 in requirements — generate token, send email link, user sets password on first login). Signals for email are scaffolded (`apps/accounts/signals.py`) but backend is not configured.

**Organisation Multi-Tenancy (Partially Implemented)**
- Problem: Organisations exist as master data, but data is NOT isolated by tenant. A Maker from Org A can technically view/edit documents from Org B if they have the right permissions (depends on implementation of `.get_queryset()` in views).
- Blocks: Cannot safely onboard multiple trading houses to the same instance.
- Path: Audit all ViewSet `.get_queryset()` methods to ensure they filter by `created_by.organisation` (or add a `created_by_organisation` denorm field). Add integration tests that verify isolation.

**Audit Trail Export (Not Implemented)**
- Problem: AuditLog exists and is written for every status transition, but no export/reporting UI.
- Blocks: Compliance and debugging require direct database queries.
- Path: Add an "Audit Trail" tab to the reports section. Implement CSV export for auditors.

**Two-Factor Authentication (Not Implemented)**
- Problem: Users authenticate with username + password over JWT. No 2FA.
- Blocks: Cannot meet security requirements for some regulated customers.
- Path: Integrate TOTP (Time-based One-Time Password) library and add 2FA setup page. This is a future phase, not blocking v1.0.

## Test Coverage Gaps

**PDF Generation Integration Tests (Medium Priority)**
- What's not tested: PDFs are generated for happy-path scenarios in views, but edge cases are not covered:
  - Document with 100+ line items (multi-page rendering)
  - Document with null/missing optional fields (e.g., no bank, no incoterm)
  - Document with very long text in description fields (text wrapping)
  - Multiple currencies in the same document
- Files: `apps/proforma_invoice/tests/test_views.py`, `apps/packing_list/tests/test_views.py`, `apps/commercial_invoice/tests/test_views.py`, `pdf/`
- Risk: PDF rendering bugs (text cutoff, layout corruption) go undetected until user downloads a document with unusual data.
- Recommendation: Add parametrized pytest tests that generate PDFs with various data patterns and assert file size is reasonable (not corrupted), PDF contains expected text (via pypdf2 or similar).

**Workflow State Machine Verification (Low Priority)**
- What's not tested: Not all state transitions are tested. For example:
  - Can a Checker transition a document from Rework back to Draft? (Should be yes, but verify)
  - Can a Maker in role A transition a document created by Maker in role B? (Depends on role, verify)
  - Simultaneous transition attempts by two users (race condition)
- Files: `apps/workflow/tests/`, each document's `test_views.py`
- Risk: Edge case in workflow logic goes unnoticed, user gets confusing "action not allowed" error.
- Recommendation: Add a test matrix (document_status × user_role × action) and verify the allowed/forbidden outcomes. Add a test for concurrent transitions (two threads calling transition_joint simultaneously).

**Master Data Foreign Key Constraints (Low Priority)**
- What's not tested: Verify that deleting a Port, Bank, Currency, etc. fails gracefully (ProtectedError).
- Files: `apps/master_data/tests/`
- Risk: Accidental deletion of master data by admin causes cascade deletes or confusing error.
- Recommendation: Add test for each PROTECT constraint: attempt to delete a Bank that's referenced by a PI, verify ProtectedError is raised.

---

*Concerns audit: 2026-07-26*
