# Phase 5: Missing Critical Features — Context

**Gathered:** 2026-06-20
**Status:** Ready for planning
**Source:** Codebase audit — `.planning/codebase/CONCERNS.md`

<domain>
## Phase Boundary

Add three features absent from the system that block operational workflows: (1) audit trail search for compliance, (2) bulk document operations for Checker efficiency, (3) change notifications so users know when to act. All three add new API endpoints and minimal frontend hooks — no changes to existing document models or workflow logic.

</domain>

<decisions>
## Implementation Decisions

### Audit Trail Search
- Add `AuditLogViewSet` with read-only endpoints (`list` and `retrieve` only)
- Filtering on: `document_id`, `document_type`, `performed_by`, `action`, `created_at` (date range)
- URL: `GET /api/audit-logs/?document_id=123&action=APPROVED`
- Permissions: Read-only for all authenticated roles; Makers can only see their own documents' logs; Checkers and Admin see all
- File: `apps/workflow/views.py` (add viewset), `apps/workflow/urls.py`, `apps/workflow/serializers.py`
- Frontend: Minimal — a dedicated audit log page or a drawer/modal on the document detail page

### Bulk Workflow Operations
- Add `POST /api/proforma-invoices/bulk-workflow/` endpoint
- Body: `{"document_ids": [1, 2, 3], "action": "APPROVE", "comment": "Bulk approved"}` 
- Validates each document can be transitioned (status check, ownership check)
- Calls `WorkflowService.transition()` for each in a single `transaction.atomic()` block
- Returns: `{"succeeded": [1, 2], "failed": [{"id": 3, "reason": "wrong status"}]}`
- Same pattern for PL and CI: `/api/packing-lists/bulk-workflow/`, `/api/commercial-invoices/bulk-workflow/`
- Permissions: Same as individual workflow action
- Frontend: Checkbox selection on list pages + "Bulk Action" button

### Change Notifications (Email via Django signals)
- Implement as Django signals → email using `django.core.mail.send_mail`
- Signal: `post_save` on `AuditLog` model (already created in WorkflowService)
- Email recipients: document creator (on APPROVED/REJECTED/REWORK) and Checker (on PENDING_APPROVAL)
- Template: Plain-text email with document number, new status, and deep link
- Settings: `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` in dev (already likely configured); prod uses Railway SMTP or SendGrid
- Do NOT block the workflow transition on email failure — use `try/except` around send; log failures
- File: `apps/workflow/signals.py` (new), `apps/workflow/apps.py` (register signal), `apps/workflow/email_templates/` (optional)

### Claude's Discretion
- Frontend UI for audit log (could be a simple table or a detailed modal)
- Whether bulk operations need their own DRF router action (`@action(detail=False)`) or a separate view
- Email template format and exact subject line wording

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Audit Findings
- `.planning/codebase/CONCERNS.md` — Missing Critical Features section

### Project Rules
- `CLAUDE.md` — constraint #5 (ALL status transitions through WorkflowService), constraint #6 (AuditLog in same atomic block), constraint #10 (explicit permission_classes), constraint #11 (all Axios in src/api/*.ts)
- `requirements/requirements.md` — FR-08.2 (no self-approval); any bulk-action flow must respect this
- `requirements/technical_architecture.md` — Section 9 constraints

### Existing Code to Extend
- `apps/workflow/models.py` — AuditLog model (already exists; add viewset/serializer)
- `apps/workflow/services.py` — WorkflowService.transition() (do not change; signal fires post-save on AuditLog)
- `apps/workflow/views.py` — add AuditLogViewSet here
- `apps/workflow/serializers.py` — add AuditLogSerializer
- Frontend: `frontend/src/api/` — new API files for bulk and audit endpoints
- Frontend: `frontend/src/utils/constants.ts` — any new status strings

</canonical_refs>

<specifics>
## Specific Ideas

- DRF `@action(detail=False, methods=['post'], url_path='bulk-workflow')` is the cleanest pattern for bulk endpoint on an existing ModelViewSet
- For notifications, using a signal on `AuditLog.post_save` is safer than modifying `WorkflowService` directly — it keeps the service clean and email failure can't break the transaction
- `django-filter` package for audit log filtering (`filterset_class = AuditLogFilter`) — check if already installed; if not, DRF's built-in `SearchFilter` + `OrderingFilter` are sufficient
- Frontend bulk selection: Ant Design's Table `rowSelection` prop with a "Bulk Action" dropdown in the page header

</specifics>

<deferred>
## Deferred Ideas

- Webhook system for external integrations (beyond email — backlog)
- In-app real-time notifications via WebSocket (beyond email — backlog)
- Bulk export/download of multiple PDFs (backlog)

</deferred>

---

*Phase: 05-critical-features*
*Context gathered: 2026-06-20 via codebase audit*
