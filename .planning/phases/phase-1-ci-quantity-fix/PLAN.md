# Phase 1 — CI Quantity Calculation Bug Fix

**Status:** BLOCKED — awaiting business decision  
**Severity:** Critical — affects all financial amounts on the Commercial Invoice when a PL has more than one container  
**Estimated effort:** 1-line backend fix + test update (30 min)

---

## The Bug

**File:** `apps/commercial_invoice/services.py`  
**Function:** `rebuild_ci_line_items(packing_list)` — around line 45

```python
# CURRENT (WRONG):
groups[key]["total_quantity"] += item.net_material_weight

# This accumulates KGS, not the item count the Maker entered.
```

When a PL has 2 containers each with 100 bags of Item A at 25 KGS/bag:
- Code stores: `total_quantity = 5,000` (KGS)
- Maker enters: Rate = USD 500 per MT
- Computed amount: `5,000 × $500 = $2,500,000` ← **WRONG by 1,000×**
- Correct amount: `5 MT × $500 = $2,500`

When UOM = KG the bug is hidden (KGS = KGS), which is why it went unnoticed initially.

---

## Business Decision Required

**Question:** How does your team price items on the Commercial Invoice?

| Option | What it means | Fix |
|---|---|---|
| **A** (Recommended) | Price by item count — `no_of_packages` (bags, cartons, PCS). Rate = USD per bag/carton. | 1-line change |
| **B** | Price by net weight in UOM — `net_material_weight` but relabelled. Rate = USD per MT/KG. Requires UI label changes. | Larger change |
| **C** | Show both: item count for pricing + weight in summary section. | Medium change |

**Recommendation: Option A** — directly matches FR-14M.8B which says "Sum of **Quantity**", and the only field labelled "Quantity" in the form is `no_of_packages`.

---

## Fix (Option A)

### Step 1 — Backend fix

**File:** `apps/commercial_invoice/services.py` (~line 45)

```python
# BEFORE:
groups[key]["total_quantity"] += item.net_material_weight

# AFTER:
groups[key]["total_quantity"] += item.no_of_packages
```

Update the comment above it:
```python
# total_quantity is the sum of no_of_packages (item count: bags, cartons, PCS)
# across all containers for this item_code + uom combination.
```

### Step 2 — Tests

**File:** `apps/commercial_invoice/tests/test_views.py`

Add two tests:
1. Two containers with same `item_code` → CI `total_quantity` = sum of `no_of_packages` across both
2. `amount` = `total_quantity × rate` (using Decimal arithmetic)

Check existing tests for any that used `net_material_weight` as the expected `total_quantity` — update those quantities.

### Step 3 — Run tests and commit

```bash
pytest apps/commercial_invoice/ -v
pytest  # full suite
```

```bash
git add apps/commercial_invoice/services.py apps/commercial_invoice/tests/test_views.py
git commit -m "fix(ci): sum no_of_packages (item count) not net_material_weight for CI total_quantity

When a PL has multiple containers, total_quantity on CI line items was
accumulating net_material_weight (KGS) instead of no_of_packages (item count).
This caused amounts to be wrong by a large factor when UOM != KG.
"
```

---

## Impact

- **Approved documents:** Unaffected — `rebuild_ci_line_items` only runs when PL is editable.
- **Draft/Rework CIs:** Will self-correct on the next container edit (rebuild is called automatically).
- **Weight summary section:** Unaffected — net/gross weight totals come from `net_material_weight` separately.

---

## Files to Touch

| File | Change |
|---|---|
| `apps/commercial_invoice/services.py` | Line ~45: `net_material_weight` → `no_of_packages` + comment update |
| `apps/commercial_invoice/tests/test_views.py` | Add 2 tests; update any broken existing tests |

No migration needed — model fields are unchanged.
