
# TradeDocs — Project Rules for Claude Code

## What This Project Is
Single-tenant trade document platform for an export trading house.
Three document types: Proforma Invoice → Packing List → Commercial Invoice.
Maker creates, Checker approves, Company Admin manages everything.

## Authoritative Documents (Read Before Any Task)
- `requirements.md` — PRD v1.2. All functional requirements, user stories, validation rules.
- `technical_architecture.md` — Tech stack, DB schema, API structure, 30 hard constraints. **Section 9 is law.**

## Non-Negotiable Technical Rules
These come from technical_architecture.md Section 9. Never violate them:

1. All monetary amounts: `DecimalField(max_digits=15, decimal_places=2)`. Never FloatField.
2. All weights: `DecimalField(max_digits=12, decimal_places=3)`. Never FloatField.
3. All FK references to master data: `on_delete=PROTECT`.
4. Organisation records are never hard-deleted — set `is_active=False`.
5. ALL document status transitions go through `WorkflowService` in `apps/workflow/services.py`. Never update `status` anywhere else.
6. `WorkflowService` must write an `AuditLog` entry in the same `transaction.atomic()` as the status update.
7. REJECT, REWORK, PERMANENTLY_REJECT, and DISABLE actions must block if comment is empty.
8. Document numbers (PI/PL/CI) are generated with `select_for_update()` to prevent duplicates.
9. PDF generation always happens in memory and is streamed. Never write a PDF to disk.
10. Every DRF view must explicitly declare `permission_classes`.
11. All Axios calls live in `src/api/*.ts`. No component calls Axios directly.
12. Status strings in the frontend come from `src/utils/constants.ts`. Never hardcode "DRAFT", "APPROVED", etc.

## Folder Structure (Quick Reference)
Backend apps live under `apps/`:
- `apps/accounts/` — Users, roles, JWT auth
- `apps/master_data/` — Organisations, Banks, Countries, Ports, etc.
- `apps/proforma_invoice/` — PI model, line items, charges
- `apps/packing_list/` — PL, containers, container items
- `apps/commercial_invoice/` — CI, aggregated line items
- `apps/workflow/` — WorkflowService, AuditLog
- `pdf/` — ReportLab PDF generation utilities

Frontend pages live under `frontend/src/pages/`.

## Document Number Formats
- Proforma Invoice: `PI-YYYY-NNNN`
- Packing List: `PL-YYYY-NNNN`
- Commercial Invoice: `CI-YYYY-NNNN`

## Current Status
Project is bootstrapped. No feature code written yet.
