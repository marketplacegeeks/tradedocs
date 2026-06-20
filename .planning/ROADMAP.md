# TradeDocs — GSD Roadmap

**Last Updated:** 2026-06-20

---

## Phase 0 — Reference Notes & Completed History ✅

**Purpose:** Permanent reference. All notes, permissions, architectural decisions, and completed-feature history that Claude needs to look up when working on TradeDocs.

**Contents:** `.planning/phases/phase-0-reference/`
- `NOTES.md` — permissions matrix, key architectural decisions, known gotchas
- `ci-bug-analysis.md` — CI quantity calculation bug root-cause analysis (pending business decision for fix)

**Status:** Complete (reference only — no implementation tasks)

---

## Phase 1 — CI Quantity Calculation Bug Fix 🔴 PENDING

**Goal:** Fix the Commercial Invoice `total_quantity` calculation so it sums `no_of_packages` (item count) instead of `net_material_weight` (KGS), then update tests.

**Requires:** User business decision — Option A (by item count) or Option B (by weight in UOM). Recommendation is **Option A**.

**Contents:** `.planning/phases/phase-1-ci-quantity-fix/PLAN.md`

**Status:** Awaiting sign-off, then 1-line backend fix + test update

---

## Backlog (Not Yet Phased)

| Item | Source | Priority |
|---|---|---|
| Reports page (currently placeholder) | `requirements/reports.md` | Medium |
| Signed copy upload / download | `technical_architecture.md` Section 5 | Low |
| Email notifications in WorkflowService | Constraint #30 — currently a stub | Low |
