---
phase: phase-5-critical-features
reviewed: 2026-06-20T00:00:00Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - apps/workflow/views.py
  - apps/workflow/urls.py
  - apps/workflow/serializers.py
  - apps/workflow/signals.py
  - apps/workflow/apps.py
  - apps/workflow/tests/test_audit_log_viewset.py
  - apps/workflow/tests/test_signals.py
  - apps/proforma_invoice/views.py
  - apps/packing_list/views.py
  - apps/commercial_invoice/views.py
  - apps/proforma_invoice/tests/test_bulk_workflow.py
  - apps/packing_list/tests/test_bulk_workflow.py
  - apps/commercial_invoice/tests/test_bulk_workflow.py
  - frontend/src/api/auditLog.ts
  - frontend/src/api/bulkWorkflow.ts
  - tradetocs/urls.py
  - tradetocs/settings.py
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-06-20
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

This phase implements the global AuditLog viewset, email notification signals, bulk-workflow endpoints on all three document types, and signed-copy upload. The overall design is solid: WorkflowService is correctly used as the single transition point, transactions are atomic, and every view declares `permission_classes` explicitly. Signal email failures are swallowed as required.

One critical bug was found in the frontend: `bulkWorkflow.ts` includes the `/api/v1/` version prefix in its URL paths, while `axiosInstance` already has `baseURL` set to `/api/v1`. This produces malformed requests to `/api/v1/api/v1/...` and makes all three bulk-workflow endpoints unreachable from the frontend. Four warnings relate to inconsistent `update_fields` on `signed_copy` saves, a missing `order_by` on the PI audit-log endpoint, an unvalidated input type risk in bulk-workflow, and a documentation mismatch on the `BulkWorkflowRequest` type. Three info items cover minor style inconsistencies.

---

## Critical Issues

### CR-01: `bulkWorkflow.ts` hardcodes `/api/v1/` path prefix — all three bulk-workflow endpoints are unreachable

**File:** `frontend/src/api/bulkWorkflow.ts:30-55`

**Issue:** `axiosInstance` is configured with `baseURL: "http://localhost:8000/api/v1"` (see `axiosInstance.ts:8`). Every other API file passes a relative path such as `"/proforma-invoices/"`. `bulkWorkflow.ts` passes absolute paths that repeat the prefix: `"/api/v1/proforma-invoices/bulk-workflow/"`. Axios appends this to the base URL, producing `http://localhost:8000/api/v1/api/v1/proforma-invoices/bulk-workflow/` — a 404 in every environment.

**Fix:** Remove the `/api/v1` prefix from all three paths, matching the convention of every other file in `src/api/`:

```ts
// bulkWorkflow.ts

export async function bulkWorkflowPI(body: BulkWorkflowRequest): Promise<BulkWorkflowResponse> {
  const response = await axiosInstance.post<BulkWorkflowResponse>(
    "/proforma-invoices/bulk-workflow/",   // was: "/api/v1/proforma-invoices/bulk-workflow/"
    body
  );
  return response.data;
}

export async function bulkWorkflowPL(body: BulkWorkflowRequest): Promise<BulkWorkflowResponse> {
  const response = await axiosInstance.post<BulkWorkflowResponse>(
    "/packing-lists/bulk-workflow/",        // was: "/api/v1/packing-lists/bulk-workflow/"
    body
  );
  return response.data;
}

export async function bulkWorkflowCI(body: BulkWorkflowRequest): Promise<BulkWorkflowResponse> {
  const response = await axiosInstance.post<BulkWorkflowResponse>(
    "/commercial-invoices/bulk-workflow/",  // was: "/api/v1/commercial-invoices/bulk-workflow/"
    body
  );
  return response.data;
}
```

---

## Warnings

### WR-01: `ProformaInvoice.signed_copy` save omits `updated_at` from `update_fields`

**File:** `apps/proforma_invoice/views.py:227`

**Issue:** `pi.save(update_fields=["signed_copy"])` does not include `"updated_at"`. The `PackingList` equivalent at `packing_list/views.py:414` correctly saves `["signed_copy", "updated_at"]`. The `ProformaInvoice` model has an `auto_now=True` `updated_at` field (line 195 of `models.py`). When `update_fields` is set, Django does **not** auto-update `auto_now` fields unless they are explicitly listed. The document's `updated_at` timestamp will be stale after a signed-copy upload on a PI.

**Fix:**
```python
# apps/proforma_invoice/views.py:227
pi.save(update_fields=["signed_copy", "updated_at"])
```

The same omission exists in the CI view (`commercial_invoice/views.py:189`). Both should be updated:

```python
# apps/commercial_invoice/views.py:189
ci.save(update_fields=["signed_copy", "updated_at"])
```

---

### WR-02: PI per-document audit-log endpoint returns results in undefined order

**File:** `apps/proforma_invoice/views.py:323-327`

**Issue:** The `audit_log` action on `ProformaInvoiceViewSet` does not call `.order_by()` on its queryset. The equivalent endpoint on `PackingListViewSet` (`packing_list/views.py:510`) explicitly adds `.order_by("-performed_at")`. Without an explicit order, the database may return rows in any order (typically insertion order, but not guaranteed), making the audit trail non-deterministic for the caller.

**Fix:**
```python
# apps/proforma_invoice/views.py:323-327
logs = AuditLog.objects.filter(
    document_type="proforma_invoice",
    document_id=pi.pk,
).select_related("performed_by").order_by("-performed_at")
```

---

### WR-03: `bulk_workflow` does not validate that `document_ids` elements are integers

**File:** `apps/proforma_invoice/views.py:273-274`, `apps/packing_list/views.py:457-458`, `apps/commercial_invoice/views.py:110-111`

**Issue:** The validation check `not isinstance(document_ids, list)` confirms the outer container is a list but does not verify that elements are integers. A caller sending `{"document_ids": ["abc", null, {}], "action": "APPROVE"}` passes the validation guard. `ProformaInvoice.objects.filter(pk__in=document_ids)` will raise a `ValueError` or `DataError` from the database driver (non-integer PK lookup), resulting in an unhandled 500 error rather than a clean 400.

**Fix:**
```python
# Add after the isinstance check, in all three bulk_workflow views
if not document_ids or not isinstance(document_ids, list):
    raise ValidationError({"document_ids": "A non-empty list of document IDs is required."})
if not all(isinstance(id_, int) for id_ in document_ids):
    raise ValidationError({"document_ids": "All document IDs must be integers."})
```

---

### WR-04: `AuditLogFilterSet` date filter uses midnight boundary — last day's entries may be excluded

**File:** `apps/workflow/views.py:25-26`

**Issue:** `performed_at_before` uses `DateFilter(field_name="performed_at", lookup_expr="lte")`. `performed_at` is a `DateTimeField` stored in UTC. A caller passing `performed_at_before=2026-06-20` compares against `2026-06-20 00:00:00`, not `2026-06-20 23:59:59.999`. Any log entry timestamped **on** June 20 (e.g., `2026-06-20T14:30:00Z`) is excluded from the result. This is a common date filter trap that makes the `before` boundary unintuitive to API consumers.

**Fix:** Use `DateTimeFilter` with `lookup_expr="lt"` on the start of the next day, or switch to `DateTimeFilter` and document that callers must pass a full ISO datetime. The least-surprising fix is to adjust the bound at query time:

```python
from django_filters import DateTimeFilter

performed_at_before = DateTimeFilter(field_name="performed_at", lookup_expr="lte")
```

And document that callers should pass `performed_at_before=2026-06-20T23:59:59` for an inclusive end-of-day boundary. Alternatively keep `DateFilter` but use `lookup_expr="lt"` on a derived next-day value (requires a custom filter method).

---

## Info

### IN-01: `BulkWorkflowRequest.action` typed as `string` — constraint #12 recommends constants

**File:** `frontend/src/api/bulkWorkflow.ts:9`

**Issue:** The `action` field is typed as `string` with a comment directing callers to use `constants.ts`. CLAUDE.md rule 12 states status strings must come from `src/utils/constants.ts`. Using a plain `string` type means TypeScript will not catch invalid action values at compile time.

**Fix:** Import the action type union from constants and tighten the type:
```ts
import { WorkflowAction } from "@/utils/constants";

export interface BulkWorkflowRequest {
  document_ids: number[];
  action: WorkflowAction;  // was: string
  comment?: string;
}
```
(Requires `WorkflowAction` to be defined and exported in `constants.ts`.)

---

### IN-02: `AuditLogSerializer` re-exported through `proforma_invoice/serializers.py`

**File:** `apps/proforma_invoice/views.py:33`, `apps/proforma_invoice/serializers.py:453`

**Issue:** `AuditLogSerializer` is defined in `apps/workflow/serializers.py` and re-exported from `apps/proforma_invoice/serializers.py` via a bare import at line 453 (`from apps.workflow.serializers import AuditLogSerializer  # noqa: F401, E402`). `apps/proforma_invoice/views.py` then imports it from `apps.proforma_invoice.serializers`. The `packing_list/views.py` correctly imports `AuditLogSerializer` directly from `apps.workflow.serializers`. The re-export pattern is fragile and adds an indirection with no benefit.

**Fix:** Change the PI view import to match the PL convention:
```python
# apps/proforma_invoice/views.py
from apps.workflow.serializers import AuditLogSerializer
```
And remove the re-export line from `apps/proforma_invoice/serializers.py`.

---

### IN-03: `TestWorkflowSignals` mixes Django `TestCase` with `pytest-django` marker conventions

**File:** `apps/workflow/tests/test_signals.py:31`

**Issue:** The class inherits from `django.test.TestCase` (which wraps each test in a transaction) rather than using `@pytest.mark.django_db` like the rest of the test suite. This works but is inconsistent with the project's pytest-native style. The two styles can interact subtly with fixtures and factory_boy's `_create` strategy. There is no functional bug here, but mixing paradigms reduces maintainability.

**Fix:** Convert to a plain class with `@pytest.mark.django_db(transaction=True)` (needed because signals fire after `commit`, and `TestCase` uses savepoints that prevent post-commit hooks from running):
```python
@pytest.mark.django_db(transaction=True)
class TestWorkflowSignals:
    def setup_method(self):
        mail.outbox = []
    ...
```

---

_Reviewed: 2026-06-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
