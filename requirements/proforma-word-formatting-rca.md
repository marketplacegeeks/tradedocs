# RCA — Proforma Invoice Word (.docx) does not match its PDF layout

**Date:** 2026-07-15
**Reported by:** Aniket
**Scope:** Only the Proforma Invoice Word export is affected. Commercial Invoice,
Packing List, and COA Word exports already match their PDFs.

---

## 1. Symptom (plain English)

When you download the Proforma Invoice as a **Word document**, the top
information grid is split into two pieces with a visible blank gap between them:

- **Block A** (Exporter / Consignee / Proforma Invoice No / Buyer Order No /
  Country of Origin / Country of Final Destination / Other reference(s))
- *...blank gap...*
- **Block B** (Pre-Carriaged By / Place of Receipt / Vessel No / No & Kind of
  Packages / Marks & Nos / Payment Terms / Port of Loading / Port of Discharge /
  Final Destination / Incoterms)

In the **PDF**, Block A and Block B are joined into one continuous bordered grid
with no gap. So the Word version looks "broken apart" compared to the PDF.

> Note: the empty line-items table and the `USD 0.00` totals in the sample are
> because the test invoice (`PI-2026-TESTF60645`) has no line items entered —
> that is missing data, **not** a formatting bug. The formatting bug is the gap.

---

## 2. Root cause

The Word generator inserts one extra empty paragraph between the top info table
and the bottom info table. The PDF does not — in the PDF the two tables are
appended back-to-back (flush) so they render as a single continuous grid.

**PDF (correct, flush) — `pdf/proforma_invoice.py` lines 491–494:**

```python
story.append(main_info_table_top)   # Block A
story.append(info_rows_b)           # Block B (top rows)  <- flush, no spacer
story.append(info_row_a)            # Block B (ports row) <- flush, no spacer
story.append(Spacer(1, 12))         # single spacer AFTER all three
```

**Word (buggy, gapped) — `pdf/proforma_invoice_word.py` line 217:**

```python
build_grid_table(document, main_info_rows, [col_w4] * 4, spans=[...])  # Block A
document.add_paragraph()   # <-- SPURIOUS GAP. PDF has no spacer here.
# ... Section 3 builds info_rows_b then info_row_a (these two ARE flush)
```

That single `document.add_paragraph()` on line 217 is the extra spacer that the
PDF does not have. It pushes Block B down and creates the visible gap.

---

## 3. Why the other documents are NOT affected

The Commercial Invoice Word generator (`pdf/commercial_invoice_word_generator.py`,
lines ~215–313) stacks all of its top sub-tables — `header_tbl`, `exp_tbl`,
`party_tbl`, `shipping_tbl`, `terms_tbl` — **with no `add_paragraph()` between
them**, exactly matching its PDF where those tables are appended flush. It only
adds a paragraph (line 314) *after* the whole header block, before the line
items. Packing List and COA follow the same flush pattern.

The Proforma Invoice generator is the only one that inserted a paragraph *inside*
the header block, so it is the only one whose Word output diverges from its PDF.

---

## 4. Change required (single fix, low risk)

**File:** `pdf/proforma_invoice_word.py`
**Line:** 217

**Remove** the `document.add_paragraph()` call that sits between the top info
table (Section 2) and the bottom info table (Section 3):

```python
    build_grid_table(
        document, main_info_rows, [col_w4] * 4,
        spans=[(0, 0, 1, 1), (2, 0, 3, 1), (2, 2, 3, 2), (2, 3, 3, 3)],
    )
    document.add_paragraph()   # <-- DELETE THIS LINE
```

Leaving the two `build_grid_table` calls back-to-back makes Word render them as
one continuous grid, matching the PDF (this is exactly how the Commercial Invoice
generator already does it).

**Do NOT** remove the other `document.add_paragraph()` calls in the file (after
the line-items table, totals, amount-in-words, validity, declaration, bank box).
Those are legitimate — each one mirrors a `Spacer(1, 12)`/`Spacer(1, 6)` that the
PDF genuinely has between those major sections.

---

## 5. How to verify after the fix

1. Regenerate the Proforma Invoice Word export for `PI-2026-TESTF60645`.
2. Confirm the Exporter/Consignee grid (Block A) and the Pre-Carriaged By /
   Ports grid (Block B) now touch with a shared border and no blank gap —
   i.e. the Word top section looks the same as the PDF top section.
3. Confirm the spacing between all the *later* sections (line items → totals →
   amount in words → validity → declaration → bank) is unchanged.

---

## 6. Related note (separate, do not conflate)

The uncommitted change in `pdf/docx_base.py` (`setup_page` now zeroes the Normal
style's `space_before` / `space_after` and sets `line_spacing = 1.0`) is a
*global* fix that reduces cell height across **all** Word documents so they don't
overflow onto extra pages. It is complementary to this fix, not a substitute for
it — it does not remove the PI-specific gap described above, because that gap is
caused by an explicit extra paragraph, not by default paragraph padding.
