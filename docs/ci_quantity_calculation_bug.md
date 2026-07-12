# CI Calculation Bug — Root Cause & Fix

**Document:** Commercial Invoice quantity & amount calculation error  
**Severity:** Critical — affects all financial amounts on the Commercial Invoice  
**Date:** 2026-06-20  

---

## 1. What the User Reported

> "There appears to a calculation error where the multiple container details and quantities were not added to the final invoice pricing."

When a Packing List has more than one container, the Commercial Invoice line item amounts do not correctly reflect the combined quantities across all containers.

---

## 2. Where the Bug Lives

**File:** `apps/commercial_invoice/services.py`  
**Function:** `rebuild_ci_line_items(packing_list)` — line 45

```python
# CURRENT (WRONG):
groups[key]["total_quantity"] += item.net_material_weight
```

This function is the engine that calculates what gets shown in the **Final Rates table** and what drives all amounts on the **Commercial Invoice PDF**. It runs every time a container or container item is added, edited, or deleted.

---

## 3. Why It Is Wrong — The Full Chain

### 3.1 How Container Items Are Structured (after Migration 0004)

When the packaging model was redesigned, the old simple `quantity` field was replaced with a structured model:

| Field | Label in UI | What It Stores |
|---|---|---|
| `no_of_packages` | "Quantity of Items" | Number of bags / cartons / units (e.g., 100 bags) |
| `qty_per_package` | "Net Weight Per Item" | Weight per bag **in KGS** (e.g., 50 KGS/bag) |
| `weight_per_unit_packaging` | "Weight per empty package" | Packaging weight per unit in KGS |
| `net_material_weight` | Computed, read-only | `no_of_packages × qty_per_package` = **total net weight in KGS** |

The PDF column header in `packing_list_generator.py` confirms this: the column is labelled **"NET WT /ITEM (KGS)"** — `qty_per_package` is always in KGS.

### 3.2 What `total_quantity` Should Be

Per the requirements (FR-14M.8B):

> **Total Quantity** = Sum of **Quantity** across all containers for this Item Code + UOM  
> **Amount (USD)** = Total Quantity × Rate (USD per UOM)

"Quantity" here is the `no_of_packages` field — the count of items the Maker entered per container row.

### 3.3 The Unit Mismatch

The current code uses `net_material_weight` (in KGS) as `total_quantity`. But the rate the Maker enters is "USD per **[UOM]**", where UOM can be MT, KG, PCS, Litres, etc.

**Example — two containers, UOM = MT:**

| | Container 1 | Container 2 |
|---|---|---|
| `no_of_packages` | 100 bags | 100 bags |
| `qty_per_package` | 25 KGS/bag | 25 KGS/bag |
| `net_material_weight` | 2,500 KGS | 2,500 KGS |

**What the code stores:**
- `total_quantity = 2,500 + 2,500 = 5,000` (labelled as "5,000 MT" in the Final Rates table)

**What the Maker enters:**
- Rate = USD 500 per MT

**Computed amount:**
- `5,000 × $500 = $2,500,000` ← **WRONG by 1,000×**

**What the amount should be:**
- Actual weight = 5,000 KGS = 5 MT → `5 × $500 = $2,500` ← **CORRECT**

**When UOM = KG**, the bug is hidden: `net_material_weight` is already in KGS, so `total_quantity` in KGS × rate per KG = correct result. This is why the bug may have gone unnoticed initially.

### 3.4 The "Not Added" Effect

When the user has **2 containers** each with 100 bags of Item A:

- The code correctly sums: `5,000 + 5,000 = 10,000`
- But that sum is KGS, not bags — so the number shown as "Total Qty" is 10,000, not 200
- At a rate per MT, the resulting amount is **2,000× what it should be**

The user sees a number that doesn't match what they entered as "Quantity of Items" (100 per container = 200 total), and the pricing is wildly wrong — which they describe as quantities "not being added to the pricing."

---

## 4. Business Process Alignment Required

Before writing the fix, we need to confirm **one business decision**:

### Question: How does your team think about quantity on the Commercial Invoice?

**Option A — Price by item count (bags, cartons, PCS)**
- The Maker enters 100 bags per container
- Rate = USD per bag
- Final Rates should show: Total Qty = 200 (bags), Amount = 200 × rate

→ Fix: use `no_of_packages` as the aggregation quantity.  
→ UOM on the CI line item = the physical package type (Bags, Cartons, MT Bags, etc.)

**Option B — Price by net weight in the chosen UOM (MT, KG, etc.)**
- The Maker thinks in tonnes: 100 bags × 0.025 MT/bag = 2.5 MT per container
- Rate = USD per MT
- Final Rates should show: Total Qty = 5 (MT), Amount = 5 × rate

→ Fix: store `qty_per_package` in **UOM units** (not always KGS), so `net_material_weight` = total in UOM.  
→ The UI label "Net Weight Per Item (KGS)" would need to change to "Qty per Package (in selected UOM)".

**Option C — Show both: item count AND weight**
- Keep `no_of_packages` as the CI quantity for pricing
- Show net weight separately in the weight summary section (which already exists)

→ Most consistent with how the PL weight note works and how export CIs are typically drafted.

### Recommendation

Based on the requirements (FR-14M.8B says "Sum of **Quantity**", and the only field labelled "Quantity" in the item form is `no_of_packages`), **Option A** aligns most directly with the written requirements. It also prevents the unit ambiguity that caused this bug.

---

## 5. Proposed Fix (pending business confirmation)

### Fix for Option A — Quantity = `no_of_packages`

**File:** `apps/commercial_invoice/services.py`

```python
# BEFORE (line 45):
groups[key]["total_quantity"] += item.net_material_weight

# AFTER:
groups[key]["total_quantity"] += item.no_of_packages
```

**Also update the comment above (lines 32–34):**

```python
# Before:
# total_quantity is the sum of net_material_weight (no_of_packages × qty_per_package)

# After:
# total_quantity is the sum of no_of_packages (count of items)
# across all items with the same item_code + uom.
```

### Fix for Option B — Quantity = weight in UOM units

This requires a larger change:
1. Rename `qty_per_package` label in UI from "Net Weight Per Item (KGS)" → "Qty per Package (in UOM)"
2. Remove the hardcoded KGS assumption from `packing_list_generator.py` column headers
3. Keep `rebuild_ci_line_items` using `net_material_weight`, but the Maker must understand they are entering UOM-unit quantities, not KGS

---

## 6. Impact of the Fix

### Data already in the system
Any existing CI line items in **Draft or Rework** state will have their `total_quantity` and `amount` recomputed correctly the next time the Packing List is saved or a container item is edited (because `rebuild_ci_line_items` is called on every such event).

**Approved documents are unaffected** — `rebuild_ci_line_items` only runs when the document is editable.

### What changes for the Maker
- "Total Qty" in the Final Rates table will now show the **number of items** (bags/cartons) — matching what they entered per container
- The Rate they enter should be "per bag/carton/UOM-unit"
- Amount = Total Items × Rate per Item

### Weight summary (unaffected)
The net weight and gross weight totals in the bottom section of the CI PDF are computed separately (from `net_material_weight`) and are not affected by this fix.

---

## 7. Files to Modify

| File | Change |
|---|---|
| `apps/commercial_invoice/services.py` | Line 45: `net_material_weight` → `no_of_packages`; update comment |

That is the only code change required for Option A. No migration needed (model fields are unchanged).

---

## 8. Tests to Update / Add

**File:** `apps/commercial_invoice/tests/test_views.py`

- Add a test: two containers with the same item_code → CI `total_quantity` = sum of `no_of_packages` across both
- Add a test: amount = total_quantity × rate (using Decimal arithmetic, no float)
- Existing tests may need quantities updated if they relied on `net_material_weight` behaviour

---

## 9. Open Questions for Business Sign-off

1. **Option A or B?** (pricing by count vs pricing by weight-in-UOM)
2. If Option A: what UOM should be set on CI line items? Currently it inherits from the container item's UOM dropdown. Does the Maker want to keep that, or should it default to the package type?
3. For existing Draft documents that have wrong amounts: should we provide a "recalculate" button, or will the next edit to a container item trigger the rebuild automatically?

---

*Prepared by: Claude Code analysis, 2026-06-20*  
*Review required before implementation.*
