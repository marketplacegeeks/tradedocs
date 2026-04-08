# Packing List — Weight & Packaging Fields Redesign

## Context
This replaces the current `ContainerItem` field set with a structured packaging model
that separates physical package count, type, and material quantity — the way
international trade packing lists are actually filled out.

---

## 1. Master Data — New Entity: Type of Package

Add a new master data entity called **Type of Package** alongside the existing
Reference Data entities (UOM, Country, Port, etc.).

| Attribute | Detail |
|-----------|--------|
| Model name | `TypeOfPackage` |
| Table | `master_data_typeofpackage` |
| Fields | `name` (CharField max 100), `is_active` (BooleanField default True) |
| Soft-delete | Yes — same pattern as all other ReferenceData entities |
| Pre-populate | Seed with common international packaging types on migration: Drums, Bags, Boxes, Cartons, Pallets, Crates, Bales, Bundles, Cylinders, Bottles, Jerricans, Rolls, Tins, Cases |

### Frontend — Master Data page
- Add a **"Type of Package"** tab to the existing Reference Data tabbed page
  (same pattern as UOM, Country, Port tabs).
- Rename the existing **"UOM"** tab to **"Material Unit"** throughout the master
  data admin page (label only — the model/URL/API key stays `uom`).

---

## 2. ContainerItem Model — Field Changes

### Remove these fields entirely
| Field to remove | Current column label |
|-----------------|----------------------|
| `packages_kind` | No & Kind of Pkgs |
| `quantity` | Qty |
| `net_weight` | Net Weight |
| `inner_packing_weight` | Inner Pkg Wt |

### Add these fields
| New field | Type | Notes |
|-----------|------|-------|
| `no_of_packages` | `DecimalField(max_digits=12, decimal_places=3)` | Number of physical packages (e.g. 10 drums) |
| `type_of_package` | `ForeignKey("master_data.TypeOfPackage", on_delete=PROTECT)` | FK to new master data entity |
| `qty_per_package` | `DecimalField(max_digits=12, decimal_places=3)` | Material quantity inside each package |
| `weight_per_unit_packaging` | `DecimalField(max_digits=12, decimal_places=3)` | Weight of one empty package unit |
| `net_material_weight` | `DecimalField(max_digits=12, decimal_places=3, editable=False)` | **Computed**: `no_of_packages × qty_per_package` |
| `item_gross_weight` | `DecimalField(max_digits=12, decimal_places=3, editable=False)` | **Computed** (renamed behaviour): `net_material_weight + (no_of_packages × weight_per_unit_packaging)` |

### Keep unchanged
- `hsn_code`, `item_code`, `description`, `batch_details`
- `uom` FK (this is now labelled **"Material Unit"** in UI; model field name stays `uom`)
- `item_gross_weight` stays stored/computed on `save()`

### Computation logic (on `ContainerItem.save()`)
```python
self.net_material_weight = self.no_of_packages * self.qty_per_package
self.item_gross_weight = self.net_material_weight + (self.no_of_packages * self.weight_per_unit_packaging)
```
Container `gross_weight` rollup stays the same: `SUM(item.item_gross_weight) + tare_weight`.

---

## 3. Create / Edit Wizard — Step 3 (Containers & Items)

### Item row field order (left to right)
| # | Column label | Source |
|---|--------------|--------|
| 1 | # | Row number |
| 2 | HSN Code | `hsn_code` |
| 3 | Item Code | `item_code` |
| 4 | Description | `description` |
| 5 | Batch No. | `batch_details` |
| 6 | No. of Package | `no_of_packages` |
| 7 | Type of Package | `type_of_package` (dropdown — TypeOfPackage master data) |
| 8 | Material Unit | `uom` (dropdown — UOM master data, now labelled "Material Unit") |
| 9 | Qty Per Package | `qty_per_package` |
| 10 | Wt Per Unit Pkg | `weight_per_unit_packaging` |
| 11 | Net Material Wt | `net_material_weight` (read-only, computed) |
| 12 | Gross Weight | `item_gross_weight` (read-only, computed) |

### Validation rules (same strictness as current)
- `no_of_packages` > 0 (required)
- `type_of_package` required
- `uom` required (Material Unit)
- `qty_per_package` ≥ 0 (required)
- `weight_per_unit_packaging` ≥ 0 (required)
- `hsn_code`, `batch_details` remain optional
- `item_code`, `description` remain required

### "Item ready" gate (before row can be saved)
Required: `item_code`, `uom`, `no_of_packages`, `type_of_package`, `qty_per_package`,
`weight_per_unit_packaging`, `description`.

---

## 4. PDF — Packing List Section

### Remove these columns
- No & Kind of Pkgs
- Qty
- Net Weight
- Inner Pkg Wt

### New column sequence in the items table
| # | Header |
|---|--------|
| 1 | # |
| 2 | HSN Code |
| 3 | Item Code |
| 4 | Description |
| 5 | Batch No. |
| 6 | No. of Package |
| 7 | Type of Package |
| 8 | Material Unit |
| 9 | Qty Per Package |
| 10 | Wt Per Unit Pkg |
| 11 | Net Material Wt |
| 12 | Gross Weight |

Container-level totals row continues to show **Total Gross Weight**
(sum of all `item_gross_weight` + `tare_weight`).

---

## 5. Files to Touch

| Layer | File | Change |
|-------|------|--------|
| Master data model | `apps/master_data/models.py` | Add `TypeOfPackage` model |
| Master data migration | new migration file | Add `master_data_typeofpackage` table + seed data |
| Master data serializer | `apps/master_data/serializers.py` | Add `TypeOfPackageSerializer` |
| Master data views | `apps/master_data/views.py` | Add `TypeOfPackageViewSet` |
| Master data URLs | `apps/master_data/urls.py` | Register `type-of-packages` route |
| PL model | `apps/packing_list/models.py` | Swap fields on `ContainerItem`; update `save()` |
| PL migration | new migration file | Drop old columns, add new columns |
| PL serializer | `apps/packing_list/serializers.py` | Update `ContainerItemSerializer` fields + validation |
| PL tests | `apps/packing_list/tests/test_models.py` | Update factories + model tests |
| PL tests | `apps/packing_list/tests/test_views.py` | Update API tests |
| Frontend API | `frontend/src/api/referenceData.ts` | Add `listTypeOfPackages()` |
| Frontend create | `frontend/src/pages/packing-list/PackingListCreatePage.tsx` | Swap item row fields |
| Frontend edit | `frontend/src/pages/packing-list/PackingListEditPage.tsx` | Same as create |
| Frontend detail | `frontend/src/pages/packing-list/PackingListDetailPage.tsx` | Update display columns |
| Frontend master data | `frontend/src/pages/master-data/ReferenceDataPage.tsx` | Add "Type of Package" tab; rename "UOM" tab to "Material Unit" |
| PDF generator | `pdf/packing_list_generator.py` | Swap item table columns |
