# Phase 4: Test Coverage Hardening — Context

**Gathered:** 2026-06-20
**Status:** Ready for planning
**Source:** Codebase audit — `.planning/codebase/CONCERNS.md`

<domain>
## Phase Boundary

Add targeted tests for the highest-risk gaps identified in the audit. All tests are new test functions in existing test files — no production code changes. Focus on paths that currently fail silently or are untested entirely.

</domain>

<decisions>
## Implementation Decisions

### Priority 1: Permission Enforcement Tests (HIGH risk)
- What to add:
  - Checker CANNOT edit a document in DRAFT (should get 403)
  - Checker CANNOT delete a document (should get 403)
  - Only the creator or Admin can edit a DRAFT document
  - No self-approval: Checker who created a document cannot approve it (FR-08.2)
- Files: `apps/proforma_invoice/tests/test_views.py`, `apps/packing_list/tests/test_views.py`, `apps/workflow/tests/test_views.py` (or `test_services.py`)
- Use existing `factories.py` to create Maker-created documents, then test Checker operations

### Priority 2: PL Without CI (Orphaned State) Tests (HIGH risk)
- What to add:
  - Serializer returns None on all CI-dependent getter methods when CI is missing (not 500)
  - API response contains null for CI fields when CI is None (not a crash)
  - CI deletion triggering correct PL behaviour
- Files: `apps/packing_list/tests/test_views.py`
- Setup: Manually set `packing_list.commercial_invoice = None` in test or delete CI directly

### Priority 3: Joint PL+CI Workflow Cascade Tests (MEDIUM risk)
- What to add:
  - When PL is approved, CI is also approved (status parity)
  - When PL is rejected, CI is also rejected
  - Cascade when linked PI is permanently rejected — PL/CI go to PERMANENTLY_REJECTED
  - Rollback test: If CI status update fails, PL status is NOT updated (atomic rollback)
- Files: `apps/workflow/tests/test_services.py` (or `apps/packing_list/tests/test_views.py`)

### Priority 4: PDF Edge Case Tests (LOW risk)
- What to add:
  - Very long company name (>100 chars) doesn't crash PDF generation
  - Very long product description doesn't crash PDF
  - Missing optional fields (bank, incoterm) produce valid PDF
- Files: `apps/packing_list/tests/test_views.py`, `apps/commercial_invoice/tests/test_views.py`
- Approach: Call the PDF endpoint directly with edge-case factory data

### Priority 5: Concurrent Document Creation (MEDIUM risk)
- What to add:
  - Two concurrent PI creations get unique document numbers (no duplicates)
  - Use `threading.Thread` to simulate concurrent requests in test
- Files: `apps/proforma_invoice/tests/test_views.py`
- Note: This requires Django test client with transaction isolation awareness

### Claude's Discretion
- Whether to use `pytest-django`'s `django_db(transaction=True)` for concurrent tests
- Whether to parametrize PDF edge case tests or write separate functions
- Exact test naming convention to follow existing patterns in test files

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Audit Findings
- `.planning/codebase/CONCERNS.md` — Test Coverage Gaps section (all priorities)

### Project Rules
- `CLAUDE.md` — Testing rules: pytest, factory-boy, SubFactory for relations, no hardcoded IDs
- `requirements/requirements.md` — FR-08.2 (no self-approval)
- `.planning/phases/phase-0-reference/NOTES.md` — permissions matrix (what each role can do)

### Files to Add Tests To
- `apps/proforma_invoice/tests/test_views.py`
- `apps/packing_list/tests/test_views.py`
- `apps/commercial_invoice/tests/test_views.py`
- `apps/workflow/tests/test_services.py` (create if not exists)
- `apps/certificate_of_analysis/tests/test_views.py`

### Existing Factories (must not duplicate)
- `apps/packing_list/tests/factories.py`
- `apps/proforma_invoice/tests/factories.py`
- `apps/accounts/tests/factories.py`

</canonical_refs>

<specifics>
## Specific Ideas

- For self-approval test: create document as Checker user, then try to approve as same user → expect 403/ValidationError from WorkflowService
- For orphaned CI test: use `CommercialInvoice.objects.filter(packing_list=pl).delete()` then call serializer
- For concurrent test: `with ThreadPoolExecutor(max_workers=2) as pool: futures = [pool.submit(create_pi, client) for _ in range(2)]` — collect results and assert unique doc numbers
- All new tests must use `@pytest.mark.django_db` decorator

</specifics>

<deferred>
## Deferred Ideas

- Load tests with 10+ concurrent creates (beyond unit test scope — for staging environment)
- Property-based tests with Hypothesis for PDF data (backlog — low priority)

</deferred>

---

*Phase: 04-test-coverage*
*Context gathered: 2026-06-20 via codebase audit*
