# Phase 3: Security & Permission Hardening — Context

**Gathered:** 2026-06-20
**Status:** Ready for planning
**Source:** Codebase audit — `.planning/codebase/CONCERNS.md`

<domain>
## Phase Boundary

Two security gaps to close: (1) Inconsistent permission classes that may allow Checkers to edit documents they shouldn't, (2) No rate limiting on document creation endpoints. Both are hardening tasks — no new document features or workflow changes.

</domain>

<decisions>
## Implementation Decisions

### Permission Model Audit & Fix
- Problem: `IsDocumentOwner` exists in `apps/accounts/permissions.py` line 44 but most document views use `IsAnyRole` instead. Manual role checks in `perform_update()` (line 202-203) are the only guard.
- Decision: Document which views must use `IsDocumentOwner` vs `IsAnyRole` for write operations, and enforce consistently. Makers can only edit their own DRAFT/REWORK documents; Checkers cannot edit.
- Files to audit and fix:
  - `apps/proforma_invoice/views.py` — all write viewset methods
  - `apps/packing_list/views.py` — all write viewset methods
  - `apps/commercial_invoice/views.py` — all write viewset methods
  - `apps/certificate_of_analysis/views.py` — all write viewset methods
- Approach: Use DRF `get_permissions()` on viewsets to apply different permission classes per action (list/retrieve vs create/update/destroy)

### Rate Limiting on Document Creation
- Apply `ScopedRateThrottle` to document creation endpoints (PI, PL, CI, COA)
- Suggested rate: `100/day` per user for document creation (generous for legitimate use, blocks spam)
- Configure in `settings.py`: `DEFAULT_THROTTLE_CLASSES`, `DEFAULT_THROTTLE_RATES`
- Apply at viewset level with `throttle_scope = "document_creation"` on create actions
- Files: `tradetocs/settings.py`, all document viewsets

### No Self-Approval Enforcement
- FR-08.2 requirement: A Checker cannot approve a document they created
- Current state: Unclear if this is enforced in `WorkflowService` or only in UI
- Decision: Add explicit check in `WorkflowService.transition()` — if `performed_by == document.created_by` and action is APPROVE → raise `PermissionDenied`
- File: `apps/workflow/services.py`

### Claude's Discretion
- Exact throttle rate numbers (can tune based on expected usage)
- Whether to use `UserRateThrottle` vs `ScopedRateThrottle` for simplicity
- Whether to add throttling to workflow transition endpoints too

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Audit Findings
- `.planning/codebase/CONCERNS.md` — Security Considerations section (Maker-Checker Bypass, Rate Limiting)

### Project Rules
- `CLAUDE.md` — constraint #10 (every DRF view must declare permission_classes)
- `requirements/requirements.md` — FR-08.2 (no self-approval)
- `.planning/phases/phase-0-reference/NOTES.md` — permissions matrix

### Files to Fix
- `apps/accounts/permissions.py`
- `apps/proforma_invoice/views.py`
- `apps/packing_list/views.py`
- `apps/commercial_invoice/views.py`
- `apps/certificate_of_analysis/views.py`
- `apps/workflow/services.py`
- `tradetocs/settings.py`

</canonical_refs>

<specifics>
## Specific Ideas

- DRF's `get_permissions()` override pattern:
  ```python
  def get_permissions(self):
      if self.action in ['create', 'update', 'partial_update', 'destroy']:
          return [IsAuthenticated(), IsMakerOrAdmin()]
      return [IsAuthenticated(), IsAnyRole()]
  ```
- For throttling, DRF `ScopedRateThrottle` is the cleanest solution — lets each viewset declare its own scope
- Self-approval check should be in WorkflowService (the single source of truth for transitions) not in views

</specifics>

<deferred>
## Deferred Ideas

- PDF generation memory risk / OOM protection (backlog — engineering concern, not security breach)
- Audit trail search for compliance (Phase 5)

</deferred>

---

*Phase: 03-security-permissions*
*Context gathered: 2026-06-20 via codebase audit*
