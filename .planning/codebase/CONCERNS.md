# Codebase Concerns

**Analysis Date:** 2026-06-20

## Tech Debt

**Broad Exception Handling in Serializers:**
- Issue: Multiple `except Exception` blocks catching all exception types and returning `None` silently, masking real errors
- Files: 
  - `apps/packing_list/serializers.py` lines 125-128, 233-236, 235-236, 263, 270, 306, 317, 356, 370, 372
  - `apps/certificate_of_analysis/serializers.py` lines 96, 99-100
  - `apps/commercial_invoice/serializers.py` lines 81, 92, 97, 106
  - `apps/workflow/serializers.py` line 25
  - `apps/purchase_order/serializers.py` line 250
- Impact: Bugs in related object access (e.g., CI not linked to PL) fail silently. Debugging becomes difficult. Real exceptions (database errors, permission issues) get hidden.
- Fix approach: Replace with specific exception types:
  - Use `RelatedObjectDoesNotExist` for OneToOne/FK access
  - Use `ci.commercial_invoice` with `try: ... except RelatedObjectDoesNotExist` instead of bare `except Exception`
  - Document expected exceptions in docstrings

**Bare Exception Handling in Views:**
- Issue: Same problem in views catching all exceptions
- Files: 
  - `apps/packing_list/views.py` lines 219-220, 258-259, 407-408
  - `apps/workflow/services.py` line 177
- Impact: Silent failures when CI is expected but missing; cascading errors in subsequent operations
- Fix approach: Replace with `RelatedObjectDoesNotExist` or validate CI existence before use. In `perform_update` (line 215+), if CI doesn't exist, should raise validation error rather than silently skipping

**Null CI Reference Risk:**
- Issue: Line 223 in `apps/packing_list/views.py` attempts to access `ci.ci_date` after setting `ci = None`. If exception occurred on line 218, subsequent lines 222-242 will crash with `AttributeError`.
- Files: `apps/packing_list/views.py` lines 217-242
- Impact: Update requests fail with 500 error instead of clear validation error. PL is partially updated but CI is not.
- Fix approach: Check `if ci is not None` before attempting to update CI fields (line 240 does this partially but not comprehensively)

## Known Bugs

**Pending CI Status Inconsistency:**
- Symptoms: PL and CI can drift out of sync if joint workflow transition fails partway through
- Files: `apps/workflow/services.py` lines 182-210, `apps/packing_list/views.py` line 278-283
- Trigger: If `WorkflowService.transition_joint()` raises exception after PL status is updated but before CI is updated, atomic rollback should prevent this, but confirm all paths are wrapped
- Workaround: Atomic transaction at line 182 should prevent this, but code should be audited
- Recommendation: Add integration test that verifies PL+CI status are always equal

**Missing CI on Packing List Retrieval:**
- Symptoms: `get_ci()` in serializer returns None; CI fields show as null in API response; links missing in UI
- Files: `apps/packing_list/models.py` (likely missing `related_name="packing_list"` on CI OneToOneField)
- Trigger: Unknown — should never happen if PL creation is transactional (line 174-193 in views is atomic)
- Workaround: Manually create CI from admin interface
- Recommendation: Add database constraint that enforces CI existence or migration to make CI creation mandatory

## Security Considerations

**Maker-Checker Bypass Risk (Partial):**
- Risk: `IsDocumentOwner` permission class only checks `created_by_id == request.user.id` for writes, but many views use `IsAnyRole` which grants all authenticated users access
- Files: `apps/accounts/permissions.py` line 44, but not used in `apps/packing_list/views.py` (uses `IsAnyRole` instead)
- Current mitigation: `perform_update()` manually checks role in views (line 202-203), but this is enforcement in views, not permissions
- Recommendations: 
  - Either apply `IsDocumentOwner` at view level or ensure all sensitive operations check `created_by` in serializer validators
  - Document why certain views use `IsAnyRole` instead of object-level permissions

**No Rate Limiting on Document Creation:**
- Risk: Users can create unlimited PI/PL/CI documents with no throttle
- Files: All viewsets in `apps/proforma_invoice/views.py`, `apps/packing_list/views.py`, `apps/commercial_invoice/views.py`
- Impact: Potential spam/disk space exhaustion
- Recommendations: Add DRF throttling (SimpleRateThrottle, ScopedRateThrottle) to document creation endpoints

**PDF Generation Memory Risk:**
- Risk: PDF generation in memory could cause OOM on large documents
- Files: `apps/packing_list/views.py` line 307, `apps/commercial_invoice/views.py` (similar endpoints)
- Impact: Server crash on large multi-container PLs
- Current mitigation: ReportLab is fairly efficient; but no max size enforcement
- Recommendations: Add size limit checks or stream large PDFs differently; monitor memory usage

## Performance Bottlenecks

**N+1 Query Issues in List View (Partially Mitigated):**
- Problem: Early code (before line 84 in `apps/packing_list/views.py`) had N+1 on `proforma_invoice__currency` and `ci.bank`
- Files: `apps/packing_list/views.py` line 100-124 (fixed with explicit prefetches)
- Cause: Why initially missing → likely incremental development without query profiling
- Current state: Fixed with `select_related` and `prefetch_related`, but future changes risk reintroduction
- Improvement path: Use `django-debug-toolbar` in dev to catch N+1 early; add `.only()` / `.defer()` to further optimize

**Inefficient CI Line Item Aggregation:**
- Problem: `get_ci_total()` and `get_fob_value()` in serializer (lines 352-377) call `.all()` on CI line items for every PL in a list, causing multiple queries
- Files: `apps/packing_list/serializers.py` lines 352-377
- Cause: Serializer method fields don't benefit from prefetch_related; would need annotation in view
- Improvement path: Use `annotate(total_amount=Sum(...))` in the view queryset instead of computing in serializer

**Rebuild CI Line Items on Every Container Change:**
- Problem: Every container/item create/update/delete calls `rebuild_ci_line_items()` which recomputes all CI line items
- Files: `apps/packing_list/views.py` lines 461, 472, 549, 555, 562, 509
- Cause: Simplest approach; avoids stale line items but potentially slow for large PLs
- Improvement path: Batch rebuild at commit time (post_save signal) instead of per-operation; consider caching line item counts

## Fragile Areas

**Joint PL+CI Workflow Transition:**
- Files: `apps/workflow/services.py` lines 114-211, `apps/packing_list/views.py` line 278-283
- Why fragile: Two separate status updates (PL then CI) within single atomic block. If second fails after first commits, atomicity rollback works, but code is tightly coupled
- Safe modification: 
  - Add comprehensive tests that verify both PL and CI statuses change together
  - Consider moving CI into a nested serializer or combining into single "document pair" entity
  - Add unique constraint or check constraint at DB level to prevent PL.status != CI.status
- Test coverage: `apps/packing_list/tests/test_views.py` should have tests for workflow failures; review coverage

**CI Creation Cascaded from PL Creation:**
- Files: `apps/packing_list/views.py` lines 174-193, `apps/packing_list/serializers.py`
- Why fragile: CI is created inside PL perform_create; PL knows about CI fields (ci_date, bank_id, etc.) from request; tight coupling
- Safe modification: 
  - Consider separating CI creation into a post_create signal or separate service
  - Document CI creation contract explicitly
  - Add tests that verify CI is created atomically with PL
- Test coverage: Gaps around CI creation failure scenarios

**Exception Handling in Destroy Operations:**
- Files: `apps/packing_list/views.py` lines 256-260, 407
- Why fragile: Bare `except Exception: pass` when deleting CI before PL. If CI delete fails for permissions (PROTECT), silently continues and deletes PL, leaving orphan CI
- Safe modification: Explicitly catch only `ProtectedError` and handle it; re-raise others
- Test coverage: Test deletion when CI has protected references

**Serializer `_get_ci()` Helper Pattern:**
- Files: `apps/packing_list/serializers.py` lines 231-236
- Why fragile: Used by many methods; if CI is ever missing, all downstream getters return None silently
- Safe modification: 
  - Use `select_related("commercial_invoice")` in all views that use this serializer
  - Log warning if CI is missing (shouldn't happen if transactions work)
  - Add assertion in serializer to fail fast in dev

## Scaling Limits

**Document Number Generation Locking:**
- Current capacity: `select_for_update()` locks efficiently for single-digit concurrent users
- Limit: If hundreds of users create documents simultaneously, lock contention will slow down. Row-level locks are serialized by database.
- Files: `apps/packing_list/services.py` line 28, `apps/proforma_invoice/services.py`, `apps/commercial_invoice/services.py`
- Scaling path: 
  - For moderate scale (10-50 concurrent), current approach works
  - For higher scale, consider:
    - Redis-based distributed counter (atomic increment)
    - Pre-allocate document number ranges per user/org
    - Async number assignment (immediate DRAFT with temp number, permanent on approval)

**PDF Generation Memory on Large Shipments:**
- Current capacity: ~100 containers per PL before ReportLab struggles
- Limit: Memory-based approach will fail on multi-thousand-item shipments
- Scaling path: 
  - Stream PDF in chunks (chunked_response)
  - Generate on-demand from cache instead of always re-rendering
  - Consider table-based approach that ReportLab can paginate

**Master Data Cascade on Deactivation:**
- Risk: `on_delete=PROTECT` prevents deletion of Banks, Ports, UOMs, etc. used in documents
- Scaling path: Deactivation (set `is_active=False`) is the intended pattern, but no migration guide for users
- Recommendations: 
  - Add UI workflow for bulk deactivation
  - Document that master data is never hard-deleted
  - Consider audit trail on deactivation

## Dependencies at Risk

**ReportLab PDF Generation:**
- Risk: No version pin; could introduce breaking changes
- Files: `pdf/` module
- Impact: PDF rendering could break on minor version upgrades
- Migration plan: Pin version in `requirements.txt`; test after upgrades

**DRF Serializer Validation:**
- Risk: Broad use of `SerializerMethodField` with no caching. Could be slow on large datasets.
- Files: Throughout `apps/*/serializers.py`
- Impact: List endpoints with many display methods get slow
- Migration plan: Use `@cached_property` or annotation-based approaches for computed fields

## Test Coverage Gaps

**Broad Exception Handling Not Tested:**
- What's not tested: Scenarios where CI is missing, FK access fails, etc.
- Files: `apps/packing_list/tests/test_views.py`, `apps/certificate_of_analysis/tests/test_views.py`
- Risk: Silent failures go unnoticed in production
- Priority: High — add tests for:
  - PL without CI (orphaned state)
  - CI deletion triggering PL update
  - Serializer getters when related objects are None

**Concurrent Document Creation Not Tested:**
- What's not tested: Race conditions in `select_for_update()` blocks
- Files: `apps/packing_list/services.py`, `apps/proforma_invoice/services.py`
- Risk: Duplicate document numbers under load
- Priority: Medium — add load test with 10+ concurrent creates

**Workflow Cascade Failures Not Tested:**
- What's not tested: PI rejection cascade to PL/CI when database constraints fail
- Files: `apps/workflow/services.py` lines 242-285
- Risk: PI rejected but PL still in PENDING_APPROVAL
- Priority: Medium — add tests for:
  - Cascade when linked document is in PERMANENTLY_REJECTED state
  - Cascade with invalid state transitions

**PDF Generation Edge Cases:**
- What's not tested: Very long company names, addresses, descriptions; missing optional fields
- Files: `pdf/packing_list_generator.py`, `pdf/commercial_invoice_generator.py`
- Risk: PDF layout breaks or crashes on edge case data
- Priority: Low — add property-based tests with long strings

**Permission Enforcement Inconsistent:**
- What's not tested: Whether `IsAnyRole` combined with manual role checks is truly equivalent to object-level permissions
- Files: `apps/accounts/permissions.py`, `apps/packing_list/views.py`
- Risk: Inconsistent permission enforcement; some endpoints allow Checkers to edit when they shouldn't
- Priority: High — add tests that verify:
  - Checkers cannot edit/delete documents
  - Only creator or Admin can edit DRAFT
  - Approval flow respects FR-08.2 (no self-approval)

## Missing Critical Features

**No Audit Trail Search:**
- Problem: AuditLog exists but no search/filter endpoint. Users cannot trace changes over time.
- Blocks: Compliance reporting; troubleshooting who made what change
- Files: `apps/workflow/models.py`, no dedicated search in `apps/workflow/views.py`
- Recommendation: Add AuditLogViewSet with filtering on document_id, document_type, performed_by, action

**No Bulk Operations:**
- Problem: Cannot reject multiple PIs at once, cannot bulk-approve
- Blocks: Checker workflows with 100+ documents
- Impact: Slow approval cycles
- Recommendation: Add bulk endpoints (e.g., `POST /proforma-invoices/bulk-workflow/`)

**No Change Notifications:**
- Problem: No webhooks, email, or in-app notifications when document status changes
- Blocks: Async workflow; users must manually check status
- Impact: Slow collaboration; easy to miss approvals
- Recommendation: Add simple webhook system or Django signals → email

---

*Concerns audit: 2026-06-20*
