# Bug Status — client bugs.md audit (2026-07-12)

| # | Bug | Verdict | Evidence |
|---|---|---|---|
| 1.1 | CI: CIF term but FOB total value | ✅ Solved | `commercial_invoice_generator.py` — label/total now Incoterm-aware ("Total CIF Amount (Payable)" etc.), fixed in commits b4754c4/41f7c74/9d903db |
| 1.2 | CI: MT quantity but KGS weights | ✅ Solved | commit f780936 — weights now use `weight_unit_for_packing_list()` instead of hardcoded "KGS" |
| 2 | PL: MT unit but KGS weights | ✅ Solved | same commit f780936 — `packing_list_generator.py` weight labels/totals now dynamic |
| 3a | COA: add "Based on factory results" | ✅ Solved | `pdf/certificate_of_analysis.py:428` |
| 3b | COA: remove analyst/QC in-charge fields | ✅ Solved | Removed from form + PDF; remaining display in `COADetailPage.tsx:501–502` deleted |
| 3c | COA: repeat company details on page 2+ | ✅ Solved | `BaseDocTemplate`/`PageTemplate` repeat header, commit 5c79287 |
| 4 | PI: date format for Validity fields | ✅ Solved | `fmt_date()` uses `%d/%b/%Y` → e.g. 12/Jul/2026 |
| 5 | PI: rename title to "PROFORMA INVOICE CUM SALES CONTRACT.INV & PACKING LIST" | ✅ Solved (per user) | Marked solved on user confirmation — current title "PROFORMA INVOICE CUM SALES CONTRACT" accepted as-is, no code change made |
| 6 | PI: can't create CI/PL, fails to pull PI details | ✅ Solved (per user) | Marked solved on user confirmation — no code change made |
| 7 | "Container Number" required error persists | ✅ Solved | commit 6f15161 — field made optional in model/serializer/frontend |
| 8 | CI: multi-container quantities not summing into pricing | ✅ Solved | commit 4b878da fixed aggregation logic; minor test gap noted (no test on rate×qty after aggregation) |
| 9 | *(blank entry in bugs.md)* | — | Nothing to investigate |
| 10 | "review final output below" (image.png only) | ❓ Unable to verify | No text content, only a client-attached image not available to us |
| 11 | Tables should shift to next page, not split mid-row | ❌ Not solved — regressed | Commit 4766d7b (Jul 10) removed `splitByRow=False` on PI/CI to fix header-repeat (#12-adjacent), which reintroduced mid-row splitting across PI, CI, CIF, COA, PO. Only Packing List still protected. |
| 12 | All documents should fit on a single page | ✅ Solved (per user) | Marked solved on user confirmation — no adaptive/dynamic sizing code change made |
| 13 | COA: allow special characters (`<`, `>`, `*`) | ✅ Solved | commit 0f9f133 — fields converted to CharField, HTML-escaped in PDF |

13 solved, 1 not solved, 1 unverifiable.

## Plan for open items

### Remaining
| Bug | Fix | Files |
|---|---|---|
| 11 | Wrap each document's line-item table in `KeepTogether(...)` so a split table shifts entirely to the next page | `pdf/proforma_invoice.py`, `pdf/proforma_invoice_generator.py`, `pdf/commercial_invoice_generator.py`, `pdf/cif_client_invoice_generator.py`, `pdf/certificate_of_analysis.py`, `pdf/purchase_order.py` |

**#10** — can't assess without the image the client attached to that bug entry.
