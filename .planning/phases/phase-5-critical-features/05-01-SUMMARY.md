---
phase: 05-critical-features
plan: "01"
subsystem: workflow
tags: [audit-log, api, django-filter, drf, typescript, read-only]
dependency_graph:
  requires:
    - apps/workflow/models.py (AuditLog model)
    - apps/accounts/permissions.py (IsAnyRole)
    - tradetocs/pagination.py (StandardPageNumberPagination)
    - django-filter (already installed)
  provides:
    - GET /api/v1/audit-logs/ (paginated, filterable audit log list)
    - GET /api/v1/audit-logs/{id}/ (single audit log entry)
    - frontend/src/api/auditLog.ts (typed API client)
  affects:
    - tradetocs/urls.py (new include added)
tech_stack:
  added: []
  patterns:
    - ReadOnlyModelViewSet with role-filtered get_queryset()
    - django-filter FilterSet for multi-field filtering
    - StandardPageNumberPagination (activated by ?page= param)
key_files:
  created:
    - apps/workflow/views.py
    - apps/workflow/urls.py
    - apps/workflow/tests/test_audit_log_viewset.py
    - frontend/src/api/auditLog.ts
  modified:
    - apps/workflow/serializers.py
    - tradetocs/urls.py
decisions:
  - "Maker role scoping: 'their own documents logs' interpreted as performed_by=request.user (not document creator). Creator-scoped JOIN across PI/PL/CI would require three UNION queries with no shared FK path — deferred. Per-document detail page audit trail covers primary Maker use case."
  - "Tests pass ?page=1 to activate StandardPageNumberPagination (project pagination skips pagination when page param absent)"
metrics:
  duration: "~20 minutes"
  completed: "2026-06-20"
  tasks_completed: 2
  files_created: 4
  files_modified: 2
---

# Phase 5 Plan 01: Audit Log Search API Summary

**One-liner:** Read-only AuditLogViewSet at GET /api/v1/audit-logs/ with django-filter support, role-scoped queryset, and typed TypeScript frontend client.

---

## What Was Built

A global audit log search endpoint so authenticated users can query the full history of document status transitions, filterable by document, actor, action type, and date range.

**Backend:**
- `AuditLogListSerializer` — ModelSerializer exposing all AuditLog fields plus `performed_by_name` (resolved from FK)
- `AuditLogFilterSet` — django-filter FilterSet for `document_id`, `document_type`, `performed_by`, `action`, `performed_at_after`, `performed_at_before`
- `AuditLogViewSet` — `ReadOnlyModelViewSet` with `IsAnyRole` permission, Maker-scoped queryset, `StandardPageNumberPagination`, and ordering support
- Router registration at `/api/v1/audit-logs/` via `apps/workflow/urls.py`
- Include wired into `tradetocs/urls.py` below the dashboard line

**Frontend:**
- `frontend/src/api/auditLog.ts` — typed TypeScript functions `fetchAuditLogs(params)` and `fetchAuditLogDetail(id)` using `axiosInstance` (constraint #11 satisfied — no component calls axios directly)

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add AuditLogListSerializer, AuditLogViewSet, urls.py, wire tradetocs/urls.py | 27fe268 | apps/workflow/serializers.py, views.py (new), urls.py (new), tradetocs/urls.py |
| 2 | Backend tests + frontend auditLog.ts API client | cc6bb96 | apps/workflow/tests/test_audit_log_viewset.py (new), frontend/src/api/auditLog.ts (new) |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Tests adapted for StandardPageNumberPagination skip-without-page behavior**
- **Found during:** Task 2
- **Issue:** `StandardPageNumberPagination.paginate_queryset()` returns `None` (plain list) when no `?page=` param is present. Tests asserting on `response.data["count"]` and `response.data["results"]` failed because response was a plain list.
- **Fix:** Added `{"page": 1}` to list test requests so pagination activates and returns `{count, next, previous, results}` shape.
- **Files modified:** `apps/workflow/tests/test_audit_log_viewset.py`
- **Commit:** cc6bb96

---

## Test Results

```
13 passed, 0 failed (apps/workflow/ — includes 6 pre-existing + 7 new)
```

All 7 new test cases pass:
1. `test_list_returns_200_for_checker`
2. `test_list_returns_200_for_admin`
3. `test_maker_sees_only_own_actions`
4. `test_unauthenticated_returns_401`
5. `test_filter_by_document_type`
6. `test_filter_by_action`
7. `test_retrieve_single_entry`

---

## Known Stubs

None — all data flows from the live AuditLog queryset. No placeholder values.

---

## Threat Flags

No new threat surface beyond the plan's threat model. The endpoint is read-only; `AuditLog` rows are only written by `WorkflowService`. Maker scoping enforced in `get_queryset()` (T-05-01-01 mitigated).

---

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| apps/workflow/views.py exists | FOUND |
| apps/workflow/urls.py exists | FOUND |
| apps/workflow/serializers.py exists | FOUND |
| apps/workflow/tests/test_audit_log_viewset.py exists | FOUND |
| frontend/src/api/auditLog.ts exists | FOUND |
| Commit 27fe268 exists | FOUND |
| Commit cc6bb96 exists | FOUND |
