# TradeDocs — Project Context

**Type:** Single-tenant trade document platform for an export trading house  
**Status:** Active development — core feature set complete, maintenance + enhancements in progress  
**GSD Initialized:** 2026-06-20

---

## What This Project Does

TradeDocs produces three export trade documents in a maker–checker approval workflow:

1. **Proforma Invoice (PI)** — preliminary invoice sent to buyers before shipment
2. **Packing List + Commercial Invoice (PL+CI)** — created together from an approved PI
3. **Certificate of Analysis (COA)** — product quality document, independent workflow

Documents flow through: `DRAFT → PENDING_APPROVAL → APPROVED` (or `REWORK / PERMANENTLY_REJECTED`)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 / Django 5 / DRF / PostgreSQL |
| Auth | JWT via simplejwt |
| PDF | ReportLab (in-memory only — never written to disk) |
| Frontend | React 18 / TypeScript / Vite / Ant Design / TanStack Query |
| Testing | pytest + factory-boy (605 tests as of 2026-06-20) |
| Hosting | Railway (backend + managed PostgreSQL + frontend static) |

---

## What Is Already Built (Complete)

- **Layer 1 — Master Data:** accounts, organisations, banks, countries, ports, incoterms, UOM, payment terms, TCTemplates, TypeOfPackage
- **Layer 2 — Documents:** Proforma Invoice, Packing List + Commercial Invoice, Purchase Order, Certificate of Analysis
- **Layer 2 — Workflow:** WorkflowService, AuditLog, all state transitions
- **Layer 2 — PDFs:** All document types, in-memory generation, DRAFT watermark, currency-aware
- **Layer 3 — Multi-currency:** Dynamic currency on PI/PL/CI (migrated from hardcoded USD)
- **Layer 3 — COA spec fields:** Changed from DecimalField to CharField to support values like "< 5.0"

---

## Authoritative Reference Files

| File | Purpose |
|---|---|
| `requirements/requirements.md` | Full PRD v1.5 — functional requirements |
| `requirements/technical_architecture.md` | Tech stack, DB schema, **Section 9 constraints (law)** |
| `requirements/coa.md` | COA feature requirements |
| `requirements/fr14m_requirements.md` | PL+CI combined form requirements |
| `memory/MEMORY.md` | Session-to-session memory (patterns, gotchas, active tasks) |
| `.planning/phases/phase-0-reference/` | Permissions matrix, architectural decisions, bug analyses |

---

## Dev Commands

```bash
# PostgreSQL (Docker)
docker-compose up -d

# Backend
source .venv/bin/activate && python manage.py runserver 8000

# Frontend
cd frontend && npm run dev  # http://localhost:5173

# Tests (always run before committing)
pytest
```

---

## Roles

| Role | What They Do |
|---|---|
| MAKER | Creates/edits documents in DRAFT or REWORK |
| CHECKER | Approves, rejects, or sends back for rework |
| COMPANY_ADMIN | Full access including master data and user management |
