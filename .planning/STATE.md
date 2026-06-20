# TradeDocs — GSD State

**Updated:** 2026-06-20

---

## Current Phase

**Phase 1 — CI Quantity Calculation Bug Fix**  
Status: **Blocked — awaiting business decision (Option A vs B)**

See `.planning/phases/phase-1-ci-quantity-fix/PLAN.md` for full details.

---

## Last Completed Work (2026-06-20)

- COA spec/result fields changed from `DecimalField` → `CharField` to support text values like `"< 5.0"`, `"> 99"`, `"NMT 5 ppm"`
- Migration `0005_coaparameter_text_spec_fields` created and committed
- `container_ref` made optional in PL serializer
- PDF layout fixes: `splitByRow=False` on all ReportLab tables, `KeepTogether` on PI header block
- Committed as: `fix(coa): change spec/result fields to CharField to support text values like '< 5.0'`

---

## Test Suite Status

605 tests, 0 failures (as of 2026-06-20 commit)

---

## Known Issues

| Issue | Severity | Status |
|---|---|---|
| CI `total_quantity` uses `net_material_weight` instead of `no_of_packages` | Critical | Awaiting business decision — Phase 1 |
