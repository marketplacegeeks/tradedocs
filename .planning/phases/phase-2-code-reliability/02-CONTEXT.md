# Phase 2: Code Reliability — Context

**Gathered:** 2026-06-20
**Status:** Ready for planning
**Source:** Codebase audit — `.planning/codebase/CONCERNS.md`

<domain>
## Phase Boundary

Fix all silent-failure paths caused by broad `except Exception` blocks and null-reference bugs across serializers, views, and services. Every change is a targeted bug fix — no new features, no refactors beyond the specific lines identified in the audit.

</domain>

<decisions>
## Implementation Decisions

### Exception Handling — Serializers
- Replace every `except Exception` block with the most specific exception type that can occur:
  - For OneToOne/FK reverse access → `RelatedObjectDoesNotExist` (from `django.core.exceptions`)
  - For attribute access on None → check `if obj is not None` before access
- Files and lines:
  - `apps/packing_list/serializers.py` lines 125-128, 233-236, 263, 270, 306, 317, 356, 370, 372
  - `apps/certificate_of_analysis/serializers.py` lines 96, 99-100
  - `apps/commercial_invoice/serializers.py` lines 81, 92, 97, 106
  - `apps/workflow/serializers.py` line 25
  - `apps/purchase_order/serializers.py` line 250
- Pattern: `try: ... except RelatedObjectDoesNotExist: return None` (not `except Exception: return None`)

### Exception Handling — Views
- Files and lines:
  - `apps/packing_list/views.py` lines 219-220, 258-259, 407-408
  - `apps/workflow/services.py` line 177
- In `perform_update` (line 215+): if CI doesn't exist, raise `serializers.ValidationError` rather than silently skipping
- In Destroy (lines 256-260, 407): catch only `ProtectedError` explicitly; re-raise all other exceptions

### Null CI Reference Fix
- File: `apps/packing_list/views.py` lines 217-242
- Problem: `ci = None` set on exception (line 218), then `ci.ci_date` accessed unconditionally at lines 222-242
- Fix: Wrap all `ci.*` attribute access in `if ci is not None:` guard; or raise `ValidationError` if `ci` is required

### Destroy Operation Safety
- File: `apps/packing_list/views.py` lines 256-260 and 407
- Problem: `except Exception: pass` silently swallows `ProtectedError` during CI deletion, then deletes PL → orphan CI
- Fix: `except ProtectedError: raise` (re-raise); only pass on `RelatedObjectDoesNotExist` (CI genuinely doesn't exist)

### `_get_ci()` Serializer Pattern
- File: `apps/packing_list/serializers.py` lines 231-236
- Fix: All views that use `PackingListSerializer` must pass queryset with `select_related("commercial_invoice")` so CI is already loaded
- In `_get_ci()`, add `logger.warning("CI missing for PL %s", obj.pk)` when returning None (unexpected in production)

### Atomic Transaction Audit
- File: `apps/workflow/services.py` lines 182-210
- Confirm all paths through `transition_joint()` are within `transaction.atomic()` — no status update happens outside the atomic block
- No code changes needed if audit passes; add inline comment confirming coverage

### Claude's Discretion
- Exact logging format for the CI-missing warning
- Whether to use Python `logging` module or Django's `logger = logging.getLogger(__name__)`
- Import organization when adding `RelatedObjectDoesNotExist`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Audit Findings
- `.planning/codebase/CONCERNS.md` — exact file locations, line numbers, fix approaches for all exception handling issues

### Project Rules
- `CLAUDE.md` — constraint #5 (WorkflowService), constraint #9 (PDF in memory), constraint #3 (FK on_delete=PROTECT)
- `requirements/technical_architecture.md` — Section 9 hard constraints

### Files to Fix
- `apps/packing_list/serializers.py`
- `apps/packing_list/views.py`
- `apps/certificate_of_analysis/serializers.py`
- `apps/commercial_invoice/serializers.py`
- `apps/workflow/serializers.py`
- `apps/workflow/services.py`
- `apps/purchase_order/serializers.py`

</canonical_refs>

<specifics>
## Specific Ideas

- Use `from django.core.exceptions import RelatedObjectDoesNotExist` (not `ObjectDoesNotExist` — that's the base class; `RelatedObjectDoesNotExist` is more specific for reverse FK access)
- For `ProtectedError`: `from django.db.models import ProtectedError`
- The `_get_ci()` helper at serializer line 231 is used by many downstream getters — fixing it with `select_related` in views is the cleanest approach (no serializer changes needed for the pattern itself)

</specifics>

<deferred>
## Deferred Ideas

- Performance: batch CI rebuild (scheduled for backlog — not a reliability issue)
- Rate limiting (Phase 3)
- Test coverage for these fixes (Phase 4)

</deferred>

---

*Phase: 02-code-reliability*
*Context gathered: 2026-06-20 via codebase audit*
