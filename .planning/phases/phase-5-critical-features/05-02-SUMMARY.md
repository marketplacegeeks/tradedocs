---
phase: 05-critical-features
plan: "02"
subsystem: bulk-workflow
tags: [bulk-workflow, proforma-invoice, packing-list, commercial-invoice, workflow, frontend-api]
dependency_graph:
  requires: []
  provides: [bulk-workflow-endpoints, bulk-workflow-frontend-client]
  affects: [apps/proforma_invoice, apps/packing_list, apps/commercial_invoice, frontend/src/api]
tech_stack:
  added: []
  patterns: [per-document-try-except-isolation, detail=False DRF action, WorkflowService delegation]
key_files:
  created:
    - apps/proforma_invoice/tests/test_bulk_workflow.py
    - apps/packing_list/tests/test_bulk_workflow.py
    - apps/commercial_invoice/tests/test_bulk_workflow.py
    - frontend/src/api/bulkWorkflow.ts
  modified:
    - apps/proforma_invoice/views.py
    - apps/packing_list/views.py
    - apps/commercial_invoice/views.py
decisions:
  - "No outer transaction.atomic() in bulk endpoint — WorkflowService handles atomicity internally per document; per-doc try/except ensures one failure does not roll back others"
  - "PL bulk uses transition_joint() (not transition()) so PL and linked CI always transition together"
  - "CI bulk uses transition() directly with document_type='commercial_invoice' — mirrors how CI individual workflow works"
metrics:
  duration: "~15 minutes"
  completed: "2026-06-20"
  tasks_completed: 2
  tasks_total: 2
  files_created: 4
  files_modified: 3
  tests_added: 21
  test_suite_total: 666
---

# Phase 5 Plan 02: Bulk Workflow Endpoints Summary

**One-liner:** Three `POST /bulk-workflow/` endpoints (PI, PL, CI) with per-document isolation via WorkflowService delegation and typed TypeScript client.

---

## What Was Built

Added `bulk_workflow` POST actions to `ProformaInvoiceViewSet`, `PackingListViewSet`, and `CommercialInvoiceViewSet`. Each endpoint accepts `{"document_ids": [...], "action": "APPROVE", "comment": ""}` and returns `{"succeeded": [...], "failed": [{"id": ..., "reason": "..."}]}`.

**Key design: per-document isolation.** WorkflowService already wraps each transition in its own `transaction.atomic()`. The bulk endpoint uses a bare `try/except` loop with no outer atomic wrapper — so if document 3 fails, the already-committed transitions for documents 1 and 2 are not rolled back. This was explicitly required in the plan's atomicity model.

---

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Add `bulk_workflow` @action to PI, PL, CI viewsets | 0070788 |
| 2 | Write 21 tests + create `frontend/src/api/bulkWorkflow.ts` | 048f125 |

---

## Decisions Made

1. **Per-document isolation over outer atomic block.** The plan explicitly required no outer `transaction.atomic()` in the bulk loop. WorkflowService handles atomicity per-document internally. This gives the desired partial-success behavior.

2. **PL uses `transition_joint()`, not `transition()`.** Packing lists always transition with their linked CI as a single unit. The bulk PL endpoint calls `transition_joint(packing_list=doc, ...)` which handles both PL and CI atomically per document pair.

3. **CI uses `transition()` directly.** The CI viewset's bulk endpoint calls `WorkflowService.transition(document_type="commercial_invoice", ...)` directly. This mirrors the architecture decision in the plan that CI has its own bulk endpoint even though its primary workflow is driven via PL.

4. **N+1 prevention.** All three bulk endpoints fetch the full document set in a single `Model.objects.filter(pk__in=document_ids)` query before the loop. Missing IDs are collected as `"Document not found."` failures.

5. **Error detail extraction.** DRF exceptions can have dict/list/string detail shapes. The exception handler normalizes all three into a plain string for the `reason` field.

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Known Stubs

None — all three endpoints are fully wired to WorkflowService. The frontend file exports typed functions with real API URLs but has no UI component (UI integration is out of scope for this plan).

---

## Threat Flags

No new security surface beyond what the threat model documented. All role checks and FR-08.2 no-self-approval enforcement are delegated to WorkflowService per document. A Maker attempting to APPROVE via the bulk endpoint receives a `200` response with the document in the `failed` list (PermissionDenied captured per-document) — no unauthorized state change occurs.

---

## Self-Check: PASSED

All 7 expected files found on disk. Both task commits (0070788, 048f125) verified in git log.
