"""
Proforma Invoice PDF generator (FR-09.6).

Constraint #20: Returns an in-memory BytesIO buffer — never writes to disk.
Uses WeasyPrint (HTML → PDF) for production-quality output following the
trade-docs design system (deep navy palette, Georgia headings, Arial body).
"""

import html as html_module
import io
from decimal import Decimal

from apps.proforma_invoice.serializers import INCOTERM_SELLER_FIELDS, FOB_ONLY_INCOTERMS


# ---- Helpers ----------------------------------------------------------------

def _esc(value):
    """HTML-escape a value; return empty string for None."""
    if value is None:
        return ""
    return html_module.escape(str(value))


def _fmt_usd(value):
    """Format a Decimal as comma-separated USD (no symbol)."""
    if value is None:
        return "0.00"
    return f"{value:,.2f}"


def _fmt_qty(value):
    """Format a Decimal quantity with 3 decimal places."""
    if value is None:
        return "0.000"
    return f"{value:,.3f}"


def _amount_in_words(amount):
    """Convert a Decimal amount to English words (e.g. 'One Hundred Dollars Only')."""
    try:
        cents = int(amount * 100)
    except (TypeError, ValueError):
        return "Zero Dollars Only"

    dollars = cents // 100
    if dollars == 0:
        return "Zero Dollars Only"

    def _ones(n):
        words = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
                 "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
                 "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        return words[n] if n < 20 else ""

    def _tens(n):
        words = ["", "", "Twenty", "Thirty", "Forty", "Fifty",
                 "Sixty", "Seventy", "Eighty", "Ninety"]
        t, o = n // 10, n % 10
        if n < 20:
            return _ones(n)
        return (words[t] + (" " + _ones(o) if o else "")).strip()

    def _hundreds(n):
        if n < 100:
            return _tens(n)
        h, r = n // 100, n % 100
        return (_ones(h) + " Hundred" + (" " + _tens(r) if r else "")).strip()

    parts = []
    for chunk, label in [
        (dollars // 1_000_000_000, "Billion"),
        ((dollars % 1_000_000_000) // 1_000_000, "Million"),
        ((dollars % 1_000_000) // 1_000, "Thousand"),
        (dollars % 1_000, ""),
    ]:
        if chunk:
            parts.append(_hundreds(chunk) + (f" {label}" if label else ""))

    return " ".join(parts).strip() + " Dollars Only"


def _org_address_html(org):
    """Return an HTML address block for an Organisation's primary address."""
    if not org:
        return ""
    addr = org.addresses.first()
    if not addr:
        return _esc(org.name)
    lines = []
    if addr.line1:
        lines.append(_esc(addr.line1))
    if addr.line2:
        lines.append(_esc(addr.line2))
    city_state = ", ".join(filter(None, [addr.city, addr.state]))
    if city_state:
        pin = f" – {_esc(addr.pin)}" if addr.pin else ""
        lines.append(_esc(city_state) + pin)
    if addr.country:
        lines.append(_esc(addr.country.name))
    contact = " · ".join(filter(None, [addr.email, addr.phone_number]))
    if contact:
        lines.append(_esc(contact))
    return "<br>".join(lines)


def _ship_cell(label, value):
    """Return a shipping grid cell HTML, or empty string if value is falsy."""
    if not value:
        return ""
    return (
        f'<div class="ship-cell">'
        f'<div class="slabel">{label}</div>'
        f'<div class="sval">{_esc(str(value))}</div>'
        f'</div>'
    )


# ---- CSS --------------------------------------------------------------------

def _build_css(pi_number: str) -> str:
    """Return the full CSS block with the PI number embedded in the page footer."""
    return f"""
@page {{
  size: A4;
  margin: 15mm 18mm 20mm 18mm;
  @bottom-left {{
    content: "{pi_number} · This is a computer-generated document.";
    font-family: Arial, Helvetica, sans-serif;
    font-size: 6.5pt;
    color: #999;
    border-top: 1px solid #D0DCE8;
    padding-top: 3px;
  }}
  @bottom-right {{
    content: "Page " counter(page) " of " counter(pages);
    font-family: Arial, Helvetica, sans-serif;
    font-size: 6.5pt;
    color: #999;
    border-top: 1px solid #D0DCE8;
    padding-top: 3px;
  }}
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: Arial, Helvetica, sans-serif;
  font-size: 9pt;
  color: #1A1A2E;
  background: white;
  line-height: 1.4;
}}

/* Draft watermark */
.draft-watermark {{
  position: fixed;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%) rotate(-35deg);
  font-size: 90pt;
  color: rgba(200, 0, 0, 0.07);
  font-family: Georgia, 'Times New Roman', serif;
  font-weight: 700;
  z-index: 0;
  letter-spacing: 12px;
  pointer-events: none;
}}
.doc-wrapper {{ position: relative; z-index: 1; }}

/* Header */
.doc-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-left: 4px solid #1E88E5;
  padding-left: 14px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #D0DCE8;
}}
.company-name {{
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 15pt;
  color: #0A1628;
  font-weight: 700;
  margin-bottom: 3px;
}}
.company-sub {{ font-size: 7.5pt; color: #5A7A9F; line-height: 1.6; }}
.doc-title-block {{ text-align: right; }}
.doc-title {{
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 11pt;
  color: #0A3D62;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}
.doc-meta {{ font-size: 8pt; color: #5A7A9F; margin-top: 5px; line-height: 1.8; }}
.doc-meta strong {{ color: #1A1A2E; }}

/* Section labels */
.section-label {{
  font-size: 7pt;
  font-weight: 700;
  letter-spacing: 1.4px;
  text-transform: uppercase;
  color: #5A7A9F;
  margin-bottom: 5px;
  margin-top: 14px;
  border-bottom: 1px solid #D0DCE8;
  padding-bottom: 2px;
}}

/* Party boxes */
.parties-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 6px 0; }}
.party-box {{
  background: #F4F7FB;
  border: 0.5px solid #D0DCE8;
  border-radius: 3px;
  padding: 9px 11px;
}}
.party-box .plabel {{
  font-size: 6.5pt; color: #5A7A9F;
  text-transform: uppercase; letter-spacing: 1px; margin-bottom: 3px;
}}
.party-box .pname {{ font-weight: 700; font-size: 9.5pt; color: #0A1628; margin-bottom: 3px; }}
.party-box .pdetail {{ font-size: 8pt; color: #3A3A5C; line-height: 1.5; }}

/* Shipping grid */
.ship-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 6px 0; }}
.ship-cell {{
  background: #F4F7FB;
  border: 0.5px solid #D0DCE8;
  border-radius: 3px;
  padding: 6px 9px;
}}
.ship-cell .slabel {{
  font-size: 6pt; color: #5A7A9F;
  text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 2px;
}}
.ship-cell .sval {{ font-size: 8.5pt; font-weight: 600; color: #0A1628; }}

/* Line items table */
table {{ width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 8pt; }}
thead tr {{ background: #0A3D62; color: white; }}
thead th {{
  padding: 6px 7px;
  text-align: left;
  font-weight: 600;
  font-size: 7pt;
  letter-spacing: 0.4px;
}}
thead th.right, tbody td.right {{ text-align: right; }}
tbody tr:nth-child(even) {{ background: #F4F7FB; }}
tbody td {{ padding: 5px 7px; border-bottom: 0.5px solid #D0DCE8; vertical-align: top; }}

/* Totals table */
.totals-table {{
  width: 46%;
  margin-left: auto;
  margin-top: 8px;
  border: 0.5px solid #D0DCE8;
  border-radius: 3px;
  overflow: hidden;
}}
.totals-table td {{ padding: 5px 10px; font-size: 8.5pt; border-bottom: 0.5px solid #D0DCE8; }}
.totals-table tr:last-child td {{ border-bottom: none; }}
.totals-table .tlabel {{ color: #5A7A9F; }}
.totals-table .tval {{ text-align: right; font-weight: 600; }}
.totals-table .grand-row td {{
  background: #EBF2FB;
  font-weight: 700;
  color: #0A3D62;
  font-size: 9pt;
}}
.totals-table .breakdown-head td {{
  background: #0A3D62;
  color: white;
  font-size: 7pt;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  font-weight: 600;
}}
.totals-table .invoice-total-row td {{
  background: #0A3D62;
  color: white;
  font-weight: 700;
  font-size: 9.5pt;
}}

/* Amount in words */
.amount-words {{
  font-style: italic;
  color: #0A3D62;
  font-size: 8.5pt;
  margin: 8px 0 12px 0;
  padding: 6px 10px;
  background: #F4F7FB;
  border-left: 3px solid #1E88E5;
  border-radius: 2px;
}}

/* Info boxes (MT103, declaration) */
.info-box {{
  font-size: 7.5pt;
  color: #5A7A9F;
  margin-top: 10px;
  font-style: italic;
  border-top: 1px solid #D0DCE8;
  padding-top: 7px;
  line-height: 1.6;
}}

/* Banking */
.banking-box {{
  background: #F4F7FB;
  border: 0.5px solid #D0DCE8;
  border-left: 3px solid #1E88E5;
  border-radius: 3px;
  padding: 9px 13px;
  margin-top: 8px;
  font-size: 8pt;
  line-height: 1.7;
}}
.banking-box .btitle {{
  font-weight: 700;
  font-size: 7.5pt;
  color: #0A3D62;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 5px;
}}

/* T&C page */
.tc-page {{ page-break-before: always; }}
.tc-body {{ font-size: 8pt; color: #3A3A5C; line-height: 1.7; margin-top: 8px; }}
"""


# ---- HTML builder -----------------------------------------------------------

def generate_pi_html(pi) -> str:
    """Build the complete HTML string for a Proforma Invoice PDF."""
    from apps.workflow.constants import APPROVED

    is_draft = pi.status != APPROVED

    # Totals
    line_items = list(pi.line_items.select_related("uom").all())
    charges = list(pi.charges.all())
    line_total = sum((item.amount_usd for item in line_items), Decimal("0.00"))
    charges_total = sum((c.amount_usd for c in charges), Decimal("0.00"))
    grand_total = line_total + charges_total

    incoterm_code = pi.incoterms.code if pi.incoterms else None
    seller_fields = INCOTERM_SELLER_FIELDS.get(incoterm_code, set())
    shows_cost_breakdown = (
        incoterm_code
        and incoterm_code not in ("EXW",)
        and incoterm_code not in FOB_ONLY_INCOTERMS
    )

    invoice_total = grand_total
    if shows_cost_breakdown:
        for field in ("freight", "insurance_amount", "import_duty", "destination_charges"):
            if field in seller_fields:
                invoice_total += getattr(pi, field) or Decimal("0.00")

    # Exporter address for header subtitle
    exporter_sub = ""
    if pi.exporter:
        addr = pi.exporter.addresses.first()
        if addr:
            parts = [p for p in [addr.line1, addr.city, addr.country.name if addr.country else ""] if p]
            exporter_sub = " &nbsp;|&nbsp; ".join(_esc(p) for p in parts)
            if addr.email:
                exporter_sub += f"<br>{_esc(addr.email)}"

    inv_date = pi.pi_date.strftime("%-d %b %Y") if pi.pi_date else "—"

    def fmt_date(d):
        return d.strftime("%-d %b %Y") if d else "—"

    h = []

    # ---- Boilerplate --------------------------------------------------------
    h.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Proforma Invoice {_esc(pi.pi_number)}</title>
<style>{_build_css(pi.pi_number)}</style>
</head>
<body>""")

    if is_draft:
        h.append('<div class="draft-watermark">DRAFT</div>')

    h.append('<div class="doc-wrapper">')

    # ---- Header -------------------------------------------------------------
    meta_rows = [
        f'PI No: <strong>{_esc(pi.pi_number)}</strong>',
        f'Date: <strong>{inv_date}</strong>',
    ]
    if pi.buyer_order_no:
        meta_rows.append(f'Buyer Order No: <strong>{_esc(pi.buyer_order_no)}</strong>')
    if pi.buyer_order_date:
        meta_rows.append(f'Buyer Order Date: <strong>{fmt_date(pi.buyer_order_date)}</strong>')
    if pi.other_references:
        meta_rows.append(f'Other Ref: <strong>{_esc(pi.other_references)}</strong>')

    h.append(f"""
  <div class="doc-header">
    <div>
      <div class="company-name">{_esc(pi.exporter.name if pi.exporter else "")}</div>
      <div class="company-sub">{exporter_sub}</div>
    </div>
    <div class="doc-title-block">
      <div class="doc-title">Proforma Invoice Cum Sales Contract</div>
      <div class="doc-meta">{"<br>".join(meta_rows)}</div>
    </div>
  </div>""")

    # ---- Parties ------------------------------------------------------------
    h.append('<div class="section-label">Parties</div>')
    h.append('<div class="parties-grid">')
    h.append(f"""
    <div class="party-box">
      <div class="plabel">Consignee</div>
      <div class="pname">{_esc(pi.consignee.name if pi.consignee else "—")}</div>
      <div class="pdetail">{_org_address_html(pi.consignee)}</div>
    </div>""")
    if pi.buyer:
        h.append(f"""
    <div class="party-box">
      <div class="plabel">Buyer (if other than Consignee)</div>
      <div class="pname">{_esc(pi.buyer.name)}</div>
      <div class="pdetail">{_org_address_html(pi.buyer)}</div>
    </div>""")
    h.append('</div>')

    # ---- Shipping & Logistics -----------------------------------------------
    h.append('<div class="section-label">Shipping &amp; Logistics</div>')
    h.append('<div class="ship-grid">')
    h.append(_ship_cell("Country of Origin", pi.country_of_origin.name if pi.country_of_origin else None))
    h.append(_ship_cell("Country of Final Dest.", pi.country_of_final_destination.name if pi.country_of_final_destination else None))
    h.append(_ship_cell("Incoterms", str(pi.incoterms) if pi.incoterms else None))
    h.append(_ship_cell("Payment Terms", pi.payment_terms.name if pi.payment_terms else None))
    h.append(_ship_cell("Port of Loading", str(pi.port_of_loading) if pi.port_of_loading else None))
    h.append(_ship_cell("Port of Discharge", str(pi.port_of_discharge) if pi.port_of_discharge else None))
    h.append(_ship_cell("Final Destination", str(pi.final_destination) if pi.final_destination else None))
    h.append(_ship_cell("Pre-Carriage By", pi.pre_carriage_by.name if pi.pre_carriage_by else None))
    h.append(_ship_cell("Place of Receipt", str(pi.place_of_receipt) if pi.place_of_receipt else None))
    h.append(_ship_cell("Vessel / Flight No.", pi.vessel_flight_no or None))
    h.append('</div>')

    # ---- Line Items ---------------------------------------------------------
    h.append("""
  <div class="section-label">Goods Description</div>
  <table>
    <thead>
      <tr>
        <th style="width:4%">#</th>
        <th style="width:11%">HSN Code</th>
        <th style="width:10%">Item Code</th>
        <th style="width:33%">Description</th>
        <th style="width:10%" class="right">Qty</th>
        <th style="width:6%">UOM</th>
        <th style="width:12%" class="right">Rate (USD)</th>
        <th style="width:14%" class="right">Amount (USD)</th>
      </tr>
    </thead>
    <tbody>""")

    for idx, item in enumerate(line_items, start=1):
        uom_abbr = item.uom.abbreviation if item.uom else ""
        h.append(f"""
      <tr>
        <td>{idx}</td>
        <td>{_esc(item.hsn_code)}</td>
        <td>{_esc(item.item_code)}</td>
        <td>{_esc(item.description)}</td>
        <td class="right">{_fmt_qty(item.quantity)}</td>
        <td>{_esc(uom_abbr)}</td>
        <td class="right">{_fmt_usd(item.rate_usd)}</td>
        <td class="right">{_fmt_usd(item.amount_usd)}</td>
      </tr>""")

    h.append("    </tbody>\n  </table>")

    # ---- Totals block -------------------------------------------------------
    h.append('<table class="totals-table">')

    if charges:
        h.append(f'<tr><td class="tlabel">Sub Total</td><td class="tval">{_fmt_usd(line_total)}</td></tr>')
        for charge in charges:
            h.append(f'<tr><td class="tlabel">{_esc(charge.description)}</td><td class="tval">{_fmt_usd(charge.amount_usd)}</td></tr>')

    h.append(f'<tr class="grand-row"><td>Grand Total Amount</td><td class="tval">USD&nbsp;{_fmt_usd(grand_total)}</td></tr>')

    if shows_cost_breakdown:
        h.append(f'<tr class="breakdown-head"><td colspan="2">Cost Breakdown ({_esc(incoterm_code)})</td></tr>')
        h.append(f'<tr><td class="tlabel">FOB Value</td><td class="tval">{_fmt_usd(grand_total)}</td></tr>')

        cost_labels = {
            "freight": "Freight",
            "insurance_amount": "Insurance Amount" + (" (All-risk)" if incoterm_code == "CIP" else ""),
            "import_duty": "Import Duty / Taxes",
            "destination_charges": "Destination Charges",
        }
        for field, label in cost_labels.items():
            if field in seller_fields:
                value = getattr(pi, field) or Decimal("0.00")
                h.append(f'<tr><td class="tlabel">{_esc(label)}</td><td class="tval">{_fmt_usd(value)}</td></tr>')

        if invoice_total != grand_total:
            h.append(f'<tr class="invoice-total-row"><td>Invoice Total (Amount Payable)</td><td class="tval">USD&nbsp;{_fmt_usd(invoice_total)}</td></tr>')

    h.append('</table>')

    # ---- Amount in words ----------------------------------------------------
    h.append(f'<div class="amount-words"><strong>Amount in Words:</strong> {_esc(_amount_in_words(invoice_total))}</div>')

    # ---- Validity & Terms ---------------------------------------------------
    h.append('<div class="section-label">Terms</div>')
    h.append('<div class="ship-grid">')
    h.append(f'<div class="ship-cell"><div class="slabel">Validity for Acceptance</div><div class="sval">{fmt_date(pi.validity_for_acceptance)}</div></div>')
    h.append(f'<div class="ship-cell"><div class="slabel">Validity for Shipment</div><div class="sval">{fmt_date(pi.validity_for_shipment)}</div></div>')
    partial = pi.partial_shipment.replace("_", " ") if pi.partial_shipment else "—"
    h.append(f'<div class="ship-cell"><div class="slabel">Partial Shipment</div><div class="sval">{_esc(partial)}</div></div>')
    transship = pi.transshipment.replace("_", " ") if pi.transshipment else "—"
    h.append(f'<div class="ship-cell"><div class="slabel">Transshipment</div><div class="sval">{_esc(transship)}</div></div>')
    h.append('</div>')

    # ---- MT103 + Declaration ------------------------------------------------
    h.append("""
  <div class="info-box">
    Request your bank to send MT 103 Message to our bank and send us copy of this message
    to trace &amp; claim the payment from our bank.<br><br>
    We declare that this invoice shows the actual price of the goods described and that all
    particulars are true and correct.
  </div>""")

    # ---- Banking details ----------------------------------------------------
    if pi.bank:
        bank = pi.bank
        intermediary_html = ""
        if bank.intermediary_bank_name:
            currency_code = bank.intermediary_currency.code if bank.intermediary_currency else ""
            intermediary_html = (
                f"<br><br><strong>Intermediary Institution</strong> ({_esc(currency_code)}): "
                f"{_esc(bank.intermediary_bank_name)} &nbsp;|&nbsp; "
                f"A/C: {_esc(bank.intermediary_account_number or '—')} &nbsp;|&nbsp; "
                f"SWIFT: {_esc(bank.intermediary_swift_code or '—')}"
            )
        h.append(f"""
  <div class="section-label">Banking Details</div>
  <div class="banking-box">
    <div class="btitle">Beneficiary Bank Information</div>
    Beneficiary: <strong>{_esc(bank.beneficiary_name)}</strong> &nbsp;|&nbsp;
    Bank: {_esc(bank.bank_name)} &nbsp;|&nbsp; Branch: {_esc(bank.branch_name or '—')}<br>
    Address: {_esc(bank.branch_address or '—')}<br>
    A/C No.: <strong>{_esc(bank.account_number)}</strong> &nbsp;|&nbsp;
    IFSC / Routing: {_esc(bank.routing_number or '—')} &nbsp;|&nbsp;
    SWIFT: <strong>{_esc(bank.swift_code or '—')}</strong>{intermediary_html}
  </div>""")

    # ---- Terms & Conditions (new page) --------------------------------------
    if pi.tc_content:
        h.append(f"""
  <div class="tc-page">
    <div class="section-label">Terms &amp; Conditions</div>
    <div class="tc-body">{pi.tc_content}</div>
  </div>""")

    h.append("</div>")  # .doc-wrapper
    h.append("</body></html>")

    return "\n".join(h)


# ---- Main entry point -------------------------------------------------------

def generate_pi_pdf(pi) -> io.BytesIO:
    """
    Generate a Proforma Invoice PDF and return an in-memory BytesIO buffer.
    Constraint #20: never writes to disk.
    """
    from weasyprint import HTML

    html_string = generate_pi_html(pi)
    pdf_bytes = HTML(string=html_string).write_pdf()
    return io.BytesIO(pdf_bytes)
