"""
Proforma Invoice PDF generator (FR-09.6).

Constraint #20: Returns an in-memory BytesIO buffer — never writes to disk.
Uses ReportLab for layout.

PDF title: "PROFORMA INVOICE CUM SALES CONTRACT"
"""

import io
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from apps.proforma_invoice.serializers import INCOTERM_SELLER_FIELDS, FOB_ONLY_INCOTERMS

# ---- Dimensions -------------------------------------------------------------
PAGE_W, PAGE_H = A4
MARGIN = 15 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# ---- Colours ----------------------------------------------------------------
BORDER_COLOR = colors.HexColor("#333333")
HEADER_BG = colors.HexColor("#f0f0f0")
LIGHT_BG = colors.HexColor("#f8f8f8")

# ---- Styles -----------------------------------------------------------------
styles = getSampleStyleSheet()

STYLE_NORMAL = ParagraphStyle(
    "Normal", fontName="Helvetica", fontSize=8, leading=11, spaceAfter=2
)
STYLE_BOLD = ParagraphStyle(
    "Bold", fontName="Helvetica-Bold", fontSize=8, leading=11
)
STYLE_TITLE = ParagraphStyle(
    "Title", fontName="Helvetica-Bold", fontSize=11, leading=14, alignment=TA_CENTER
)
STYLE_ORG = ParagraphStyle(
    "Org", fontName="Helvetica-Bold", fontSize=13, leading=16, alignment=TA_CENTER
)
STYLE_SECTION = ParagraphStyle(
    "Section", fontName="Helvetica-Bold", fontSize=8, leading=11, alignment=TA_CENTER
)
STYLE_RIGHT = ParagraphStyle(
    "Right", fontName="Helvetica", fontSize=8, leading=11, alignment=TA_RIGHT
)
STYLE_RIGHT_BOLD = ParagraphStyle(
    "RightBold", fontName="Helvetica-Bold", fontSize=8, leading=11, alignment=TA_RIGHT
)
STYLE_FOOTER = ParagraphStyle(
    "Footer", fontName="Helvetica-Oblique", fontSize=7, leading=9, alignment=TA_CENTER
)
STYLE_WATERMARK = ParagraphStyle(
    "Watermark", fontName="Helvetica-Bold", fontSize=60, textColor=colors.Color(0.8, 0.8, 0.8, alpha=0.4)
)


def _fmt_decimal(value, prefix="$"):
    """Format a Decimal or None as a USD string."""
    if value is None:
        return f"{prefix}0.00"
    return f"{prefix}{value:,.2f}"


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
        words = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
                 "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
                 "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        return words[n] if n < 20 else ""

    def _tens(n):
        words = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        t = n // 10
        o = n % 10
        if n < 20:
            return _ones(n)
        return (words[t] + (" " + _ones(o) if o else "")).strip()

    def _hundreds(n):
        if n < 100:
            return _tens(n)
        h = n // 100
        r = n % 100
        return (_ones(h) + " Hundred" + (" " + _tens(r) if r else "")).strip()

    def _chunk(n, label):
        if n == 0:
            return ""
        return _hundreds(n) + (f" {label}" if label else "")

    billions = dollars // 1_000_000_000
    millions = (dollars % 1_000_000_000) // 1_000_000
    thousands = (dollars % 1_000_000) // 1_000
    remainder = dollars % 1_000

    parts = []
    if billions:
        parts.append(_chunk(billions, "Billion"))
    if millions:
        parts.append(_chunk(millions, "Million"))
    if thousands:
        parts.append(_chunk(thousands, "Thousand"))
    if remainder:
        parts.append(_chunk(remainder, ""))

    return " ".join(parts).strip() + " Dollars Only"


def _p(text, style=None):
    """Convenience: create a Paragraph, treating empty/None text as an empty string."""
    return Paragraph(str(text or ""), style or STYLE_NORMAL)


def _org_address_lines(org):
    """Return a multi-line address string for an Organisation's primary address."""
    if not org:
        return ""
    addr = org.addresses.first()
    if not addr:
        return org.name
    lines = [org.name]
    if addr.line1:
        lines.append(addr.line1)
    if addr.line2:
        lines.append(addr.line2)
    city_state = ", ".join(filter(None, [addr.city, addr.state]))
    if city_state:
        lines.append(city_state)
    if addr.pin:
        lines[-1] += f" – {addr.pin}"
    if addr.country:
        lines.append(addr.country.name)
    contact = ", ".join(filter(None, [addr.email, addr.phone_number]))
    if contact:
        lines.append(contact)
    return "\n".join(lines)


def _table_style(extra=None):
    base = [
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if extra:
        base.extend(extra)
    return TableStyle(base)


# ---- Footer callback --------------------------------------------------------

def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Oblique", 7)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(
        PAGE_W / 2,
        10 * mm,
        "This is a computer-generated document. Signature is not required.",
    )
    canvas.restoreState()


def _draft_watermark(canvas, doc):
    _footer(canvas, doc)
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 80)
    canvas.setFillColor(colors.Color(0.85, 0.85, 0.85, alpha=0.35))
    canvas.translate(PAGE_W / 2, PAGE_H / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "DRAFT")
    canvas.restoreState()


# ---- Main generator ---------------------------------------------------------

def generate_pi_pdf(pi) -> io.BytesIO:
    """
    Generate a Proforma Invoice PDF and return an in-memory BytesIO buffer.
    Constraint #20: never writes to disk.
    """
    from apps.workflow.constants import APPROVED

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=18 * mm,
    )

    # Use draft watermark for non-Approved documents (FR-08.3)
    on_page = _draft_watermark if pi.status != APPROVED else _footer

    story = []

    # -- 1. Exporter name (centred, large, bold) ------------------------------
    exporter_name = pi.exporter.name if pi.exporter else ""
    story.append(_p(exporter_name, STYLE_ORG))
    story.append(Spacer(1, 3 * mm))

    # Exporter address line below the name
    if pi.exporter:
        addr = pi.exporter.addresses.first()
        if addr:
            addr_parts = filter(None, [addr.line1, addr.city, addr.state, addr.country.name if addr.country else ""])
            story.append(_p(", ".join(addr_parts), ParagraphStyle("ExporterAddr", fontName="Helvetica", fontSize=8, alignment=TA_CENTER)))
    story.append(Spacer(1, 3 * mm))

    # -- 2. Document title ----------------------------------------------------
    story.append(_p("PROFORMA INVOICE CUM SALES CONTRACT", STYLE_TITLE))
    story.append(Spacer(1, 4 * mm))

    # -- 3. Main information table (8 rows) -----------------------------------
    col_l = CONTENT_W * 0.5
    col_r = CONTENT_W * 0.5

    def cell(text, bold=False):
        return _p(text, STYLE_BOLD if bold else STYLE_NORMAL)

    def label_value(label, value):
        return _p(f"<b>{label}:</b> {value or ''}", STYLE_NORMAL)

    # Row 1: Exporter details | Invoice No & Date
    exporter_addr = _org_address_lines(pi.exporter)
    inv_date = pi.pi_date.strftime("%-d %b %Y") if pi.pi_date else ""
    buyer_order_info = f"Buyer Order No: {pi.buyer_order_no or '—'}\nBuyer Order Date: {pi.buyer_order_date.strftime('%-d %b %Y') if pi.buyer_order_date else '—'}"
    other_refs = f"Other References: {pi.other_references or '—'}"

    info_data = [
        [
            _p(exporter_addr.replace("\n", "<br/>")),
            _p(f"<b>Proforma Invoice No:</b> {pi.pi_number}<br/><b>Date:</b> {inv_date}<br/>{buyer_order_info.replace(chr(10), '<br/>')}<br/>{other_refs}"),
        ],
        [
            _p((_org_address_lines(pi.consignee) or "—").replace("\n", "<br/>")),
            _p(
                (f"<b>Buyer (if other than Consignee):</b><br/>{(_org_address_lines(pi.buyer) or '—').replace(chr(10), '<br/>')}")
                + f"<br/><b>Country of Origin:</b> {pi.country_of_origin.name if pi.country_of_origin else '—'}"
                + f"<br/><b>Country of Final Destination:</b> {pi.country_of_final_destination.name if pi.country_of_final_destination else '—'}"
            ),
        ],
        [
            _p(
                f"<b>Pre-Carriage By:</b> {pi.pre_carriage_by.name if pi.pre_carriage_by else '—'}<br/>"
                f"<b>Place of Receipt:</b> {str(pi.place_of_receipt) if pi.place_of_receipt else '—'}<br/>"
                f"<b>Vessel / Flight No:</b> {pi.vessel_flight_no or '—'}"
            ),
            _p(
                f"<b>Incoterms:</b> {str(pi.incoterms) if pi.incoterms else '—'}<br/>"
                f"<b>Payment Terms:</b> {pi.payment_terms.name if pi.payment_terms else '—'}"
            ),
        ],
        [
            _p(f"<b>Port of Loading:</b> {str(pi.port_of_loading) if pi.port_of_loading else '—'}"),
            _p(
                f"<b>Port of Discharge:</b> {str(pi.port_of_discharge) if pi.port_of_discharge else '—'}<br/>"
                f"<b>Final Destination:</b> {str(pi.final_destination) if pi.final_destination else '—'}"
            ),
        ],
    ]

    info_table = Table(info_data, colWidths=[col_l, col_r])
    info_table.setStyle(_table_style([
        ("BACKGROUND", (0, 0), (0, 0), LIGHT_BG),
        ("BACKGROUND", (0, 1), (0, 1), LIGHT_BG),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 3 * mm))

    # -- 4. Line items table --------------------------------------------------
    line_items = list(pi.line_items.select_related("uom").all())

    li_header = [
        cell("Sr.", bold=True), cell("HSN Code", bold=True), cell("Item Code", bold=True),
        cell("Description of Goods", bold=True), cell("Qty", bold=True), cell("UOM", bold=True),
        cell("Rate (USD)", bold=True), cell("Amount (USD)", bold=True),
    ]
    li_rows = [li_header]
    line_total = Decimal("0.00")
    for idx, item in enumerate(line_items, start=1):
        uom_abbr = item.uom.abbreviation if item.uom else ""
        li_rows.append([
            _p(str(idx)),
            _p(item.hsn_code),
            _p(item.item_code),
            _p(item.description),
            _p(f"{item.quantity:,.3f}"),
            _p(uom_abbr),
            _p(_fmt_decimal(item.rate_usd, "")),
            _p(_fmt_decimal(item.amount_usd, "")),
        ])
        line_total += item.amount_usd

    # Summary row
    li_rows.append([
        _p(""), _p(""), _p(""), _p(""), _p(""), _p(""),
        _p("Total", STYLE_BOLD),
        _p(_fmt_decimal(line_total, ""), STYLE_BOLD),
    ])

    col_widths = [
        CONTENT_W * 0.04,  # Sr
        CONTENT_W * 0.10,  # HSN
        CONTENT_W * 0.10,  # Item Code
        CONTENT_W * 0.30,  # Description
        CONTENT_W * 0.09,  # Qty
        CONTENT_W * 0.07,  # UOM
        CONTENT_W * 0.15,  # Rate
        CONTENT_W * 0.15,  # Amount
    ]
    li_table = Table(li_rows, colWidths=col_widths, repeatRows=1)
    li_table.setStyle(_table_style([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_BG),
    ]))
    story.append(li_table)
    story.append(Spacer(1, 2 * mm))

    # -- 5. Amount block ------------------------------------------------------
    charges = list(pi.charges.all())
    charges_total = sum((c.amount_usd for c in charges), Decimal("0.00"))
    grand_total = line_total + charges_total

    incoterm_code = pi.incoterms.code if pi.incoterms else None
    seller_fields = INCOTERM_SELLER_FIELDS.get(incoterm_code, set())

    amount_rows = []
    amount_rows.append([_p("Amount Chargeable in: USD", STYLE_BOLD), _p("")])

    # Sub Total row only appears when there are additional charges — avoids
    # showing two identical numbers (Sub Total = Grand Total) when charges = 0.
    if charges:
        amount_rows.append([_p("Sub Total"), _p(_fmt_decimal(line_total, ""), STYLE_RIGHT)])
        for charge in charges:
            amount_rows.append([_p(charge.description), _p(_fmt_decimal(charge.amount_usd, ""), STYLE_RIGHT)])

    amount_rows.append([_p("Grand Total Amount", STYLE_BOLD), _p(_fmt_decimal(grand_total, ""), STYLE_RIGHT_BOLD)])

    # Cost breakdown (FR-09.7) — skipped for EXW (no seller costs) and for
    # FCA/FOB (buyer bears freight; showing only FOB Value = Grand Total adds
    # nothing and is confusing on the document).
    shows_cost_breakdown = (
        incoterm_code
        and incoterm_code not in ("EXW",)
        and incoterm_code not in FOB_ONLY_INCOTERMS
    )

    invoice_total = grand_total
    if shows_cost_breakdown:
        amount_rows.append([_p(f"COST BREAKDOWN ({incoterm_code})", STYLE_SECTION), _p("")])
        amount_rows.append([_p("FOB Value"), _p(_fmt_decimal(grand_total, ""), STYLE_RIGHT)])

        if "freight" in seller_fields:
            amount_rows.append([_p("Freight"), _p(_fmt_decimal(pi.freight or Decimal("0.00"), ""), STYLE_RIGHT)])
            invoice_total += pi.freight or Decimal("0.00")
        if "insurance_amount" in seller_fields:
            tooltip = " (All-risk coverage)" if incoterm_code == "CIP" else ""
            amount_rows.append([_p(f"Insurance Amount{tooltip}"), _p(_fmt_decimal(pi.insurance_amount or Decimal("0.00"), ""), STYLE_RIGHT)])
            invoice_total += pi.insurance_amount or Decimal("0.00")
        if "import_duty" in seller_fields:
            amount_rows.append([_p("Import Duty / Taxes"), _p(_fmt_decimal(pi.import_duty or Decimal("0.00"), ""), STYLE_RIGHT)])
            invoice_total += pi.import_duty or Decimal("0.00")
        if "destination_charges" in seller_fields:
            amount_rows.append([_p("Destination Charges"), _p(_fmt_decimal(pi.destination_charges or Decimal("0.00"), ""), STYLE_RIGHT)])
            invoice_total += pi.destination_charges or Decimal("0.00")

        # Only print Invoice Total (Amount Payable) when it differs from Grand Total —
        # avoids two identical numbers on the document.
        if invoice_total != grand_total:
            amount_rows.append([_p("Invoice Total (Amount Payable)", STYLE_BOLD), _p(_fmt_decimal(invoice_total, ""), STYLE_RIGHT_BOLD)])

    amount_table = Table(amount_rows, colWidths=[CONTENT_W * 0.7, CONTENT_W * 0.3])
    amount_table.setStyle(_table_style([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("SPAN", (0, 0), (1, 0)),  # "Amount Chargeable" spans full width
    ]))
    story.append(amount_table)
    story.append(Spacer(1, 2 * mm))

    # -- 6. Amount in words — always reflects the final payable amount --------
    # When Invoice Total (Amount Payable) is shown it is the payable figure;
    # otherwise Grand Total is the amount the buyer owes.
    story.append(_p(f"<b>Amount in Words:</b> {_amount_in_words(invoice_total)}", STYLE_NORMAL))
    story.append(Spacer(1, 3 * mm))

    # -- 7. Validity & terms block --------------------------------------------
    validity_data = [
        [
            _p(f"<b>Validity for Acceptance:</b> {pi.validity_for_acceptance.strftime('%-d %b %Y') if pi.validity_for_acceptance else '—'}"),
            _p(f"<b>Validity for Shipment:</b> {pi.validity_for_shipment.strftime('%-d %b %Y') if pi.validity_for_shipment else '—'}"),
            _p(f"<b>Partial Shipment:</b> {pi.partial_shipment.replace('_', ' ') if pi.partial_shipment else '—'}"),
            _p(f"<b>Transshipment:</b> {pi.transshipment.replace('_', ' ') if pi.transshipment else '—'}"),
        ]
    ]
    validity_table = Table(validity_data, colWidths=[CONTENT_W / 4] * 4)
    validity_table.setStyle(_table_style())
    story.append(validity_table)
    story.append(Spacer(1, 3 * mm))

    # -- 8. MT103 payment instruction -----------------------------------------
    story.append(_p(
        "Request your bank to send MT 103 Message to our bank and send us copy of this "
        "message to trace & claim the payment from our bank.",
        STYLE_NORMAL,
    ))
    story.append(Spacer(1, 2 * mm))

    # -- 9. Declaration -------------------------------------------------------
    story.append(_p(
        "We declare that this invoice shows the actual price of the goods described and "
        "that all particulars are true and correct.",
        STYLE_NORMAL,
    ))
    story.append(Spacer(1, 3 * mm))

    # -- 10. Beneficiary / Bank details ---------------------------------------
    if pi.bank:
        bank = pi.bank
        bank_lines = [
            f"<b>BENEFICIARY NAME:</b> {bank.beneficiary_name}",
            f"<b>BANK NAME:</b> {bank.bank_name}",
            f"<b>BRANCH NAME:</b> {bank.branch_name}",
            f"<b>BRANCH ADDRESS:</b> {bank.branch_address or '—'}",
            f"<b>A/C NO.:</b> {bank.account_number}",
        ]
        if bank.routing_number:
            bank_lines.append(f"<b>IFSC CODE:</b> {bank.routing_number}")
        bank_lines.append(f"<b>SWIFT CODE:</b> {bank.swift_code or '—'}")
        if bank.intermediary_bank_name:
            bank_lines.extend([
                f"<b>Intermediary Institution Routing for Currency</b> {bank.intermediary_currency.code if bank.intermediary_currency else ''}",
                f"<b>A/C No.:</b> {bank.intermediary_account_number or '—'}",
                bank.intermediary_bank_name,
                f"<b>SWIFT Code:</b> {bank.intermediary_swift_code or '—'}",
            ])
        story.append(_p("<br/>".join(bank_lines), STYLE_NORMAL))
        story.append(Spacer(1, 3 * mm))

    # -- 11. Terms & Conditions (new page if present) -------------------------
    if pi.tc_content:
        story.append(PageBreak())
        story.append(_p("<b>TERMS AND CONDITIONS</b>", STYLE_TITLE))
        story.append(Spacer(1, 4 * mm))
        # tc_content may contain HTML from the rich-text editor
        story.append(_p(pi.tc_content, STYLE_NORMAL))

    # -------------------------------------------------------------------------
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    return buffer
