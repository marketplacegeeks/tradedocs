---
phase: 05-critical-features
plan: "03"
subsystem: workflow/notifications
tags: [email, signals, notifications, django, workflow]
dependency_graph:
  requires:
    - apps/workflow/models.py (AuditLog model)
    - apps/accounts/models.py (User, UserRole)
    - apps/workflow/constants.py (SUBMIT, APPROVE, REWORK_ACTION, PERMANENTLY_REJECT)
  provides:
    - AuditLog post_save signal that sends email notifications on status changes
    - FRONTEND_BASE_URL setting for deep links in notification emails
  affects:
    - apps/workflow/ (new signal registration via WorkflowConfig.ready())
    - tradetocs/settings.py (new FRONTEND_BASE_URL setting)
tech_stack:
  added: []
  patterns:
    - Django post_save signal registered in AppConfig.ready() to avoid import-time side effects
    - Lazy imports inside signal handler to prevent circular import chains
    - try/except around send_mail so email failure never blocks the workflow transaction
    - django.core.mail.locmem.EmailBackend for test isolation (mail.outbox)
key_files:
  created:
    - apps/workflow/signals.py
    - apps/workflow/tests/test_signals.py
  modified:
    - apps/workflow/apps.py
    - tradetocs/settings.py
decisions:
  - Email sent synchronously in post_save signal (fires after WorkflowService transaction commits); no Celery needed per constraint #30
  - Email failure caught in on_audit_log_saved with logger.exception; never re-raised
  - SUBMIT notifies all active Checkers + Company Admins; APPROVE/REWORK/PERMANENTLY_REJECT notify document creator
  - Deep link format: {FRONTEND_BASE_URL}/{document-type-kebab-case}/{document_id}
  - User.full_name used (a @property) — not get_full_name() which does not exist on the custom User model
metrics:
  duration: "~15 minutes"
  completed: "2026-06-20"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 4
---

# Phase 05 Plan 03: Email Notifications for Document Status Changes Summary

**One-liner:** Django post_save signal on AuditLog sends plain-text emails with deep links when documents are submitted, approved, reworked, or permanently rejected — failures are swallowed so workflow is never blocked.

---

## What Was Built

A new `apps/workflow/signals.py` module registers a `post_save` receiver on `AuditLog`. The signal fires after `WorkflowService` commits each status transition (post_save fires outside the transaction, so email send is safe to skip without losing data). The signal:

1. Returns immediately for non-INSERT saves and unknown actions.
2. Dispatches to `_dispatch_notification()` which builds recipient list, email subject/body, and deep link.
3. Calls `django.core.mail.send_mail()` wrapped in a top-level `try/except` in `on_audit_log_saved` — any SMTP or runtime error is logged via `logger.exception` and silently swallowed.

**Recipient rules:**
- `SUBMIT` → all `is_active=True` Users with role `CHECKER` or `COMPANY_ADMIN`
- `APPROVE` / `REWORK` / `PERMANENTLY_REJECT` → document creator (fetched via lazy import of the relevant document model)

**Email body contains:**
- Document type + number
- Action label (human-readable)
- New status (human-readable)
- Performer name (via `User.full_name` property)
- Deep link: `{FRONTEND_BASE_URL}/{document-type-kebab-case}/{document_id}`
- Comment (only if non-empty)

`FRONTEND_BASE_URL` was added to `tradetocs/settings.py` directly below `DEFAULT_FROM_EMAIL`, configurable via `TRADETOCS_FRONTEND_BASE_URL` env var (defaults to `http://localhost:5173`).

Signal registration is in `WorkflowConfig.ready()` — no import-time side effects.

---

## Tasks Completed

| # | Name | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Add FRONTEND_BASE_URL, create signals.py, update apps.py | `15c97cd` | tradetocs/settings.py, apps/workflow/signals.py, apps/workflow/apps.py |
| 2 | Write signal tests using Django's mail.outbox | `df3d053` | apps/workflow/tests/test_signals.py |

---

## Test Results

- `pytest apps/workflow/tests/test_signals.py -v` → **8 passed, 0 failed**
- `pytest apps/workflow/ -v` → **14 passed, 0 failed** (8 new + 6 pre-existing)

Tests verified:
1. `test_submit_notifies_checkers_and_admins` — Checker and Admin both receive email on SUBMIT
2. `test_approve_notifies_document_creator` — Maker receives email on APPROVE
3. `test_rework_notifies_document_creator` — Maker receives email on REWORK
4. `test_permanently_reject_notifies_document_creator` — Maker receives email on PERMANENTLY_REJECT
5. `test_email_failure_does_not_raise` — mocked SMTP failure does not propagate
6. `test_no_email_for_unknown_action` — unknown action produces no email
7. `test_submit_skips_inactive_checkers` — inactive checker excluded from recipients
8. `test_email_body_contains_deep_link` — "proforma-invoice" and document pk present in email body

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Known Stubs

None. The signal sends real emails (to console in dev, to locmem backend in tests). No stubs or placeholder data.

---

## Threat Flags

No new threat surface beyond what is documented in the plan's STRIDE register. The signal reads only existing AuditLog fields and queries existing User emails — no new network endpoints or auth paths introduced.

---

## Self-Check: PASSED

Files created:
- apps/workflow/signals.py — exists
- apps/workflow/tests/test_signals.py — exists

Files modified:
- apps/workflow/apps.py — `def ready()` present
- tradetocs/settings.py — `FRONTEND_BASE_URL` present

Commits:
- `15c97cd` — feat(05-03): add AuditLog post_save signal for email notifications
- `df3d053` — test(05-03): add 8 signal tests verifying email notification behavior
