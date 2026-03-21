"""
Commercial Invoice PDF generator — pdf1/ reference layout, mapped to actual model fields.

Field mapping summary (pdf1/ attribute → actual model field):
  invoice.exporter           → invoice.packing_list.exporter   (via PL)
  invoice.consignee          → invoice.packing_list.consignee  (via PL)
  invoice.invoice_number     → invoice.ci_number
  invoice.date               → invoice.ci_date
  invoice.incoterm.code      → invoice.packing_list.incoterms.code
  invoice.payment_term.name  → invoice.packing_list.payment_terms.name
  invoice.port_loading       → invoice.packing_list.port_of_loading
  invoice.port_discharge     → invoice.packing_list.port_of_discharge
  invoice.pre_carriage       → invoice.packing_list.pre_carriage_by
  it.hs_code                 → it.hsn_code
  it.quantity                → it.total_quantity
  it.unit_price_usd          → it.rate_usd
  it.unit (string)           → it.uom.abbreviation  (UOM FK)
  pitem.packages_number_and_kind → pitem.packages_kind
  invoice.total_amount_usd   → computed: sum(li.amount_usd for li in ci.line_items.all())
  containers (is_active)     → no is_active on Container; use .all().order_by("id")

Constraint #20: generate_commercial_invoice_pdf_bytes() returns bytes in-memory — never
writes to disk.
"""
from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# Mirrors INCOTERM_PL_FIELDS in frontend/src/utils/constants.ts.
# Keys are Incoterm codes; values are the set of CI cost fields that should be printed.
# L/C Details is always shown and is NOT in these sets (FR-14M.8B).
_INCOTERM_VISIBLE_FIELDS: dict = {
    "EXW": set(),
    "FCA": {"fob_rate"},
    "FOB": {"fob_rate"},
    "CFR": {"fob_rate", "freight"},
    "CIF": {"fob_rate", "freight", "insurance"},
    "CPT": {"fob_rate", "freight"},
    "CIP": {"fob_rate", "freight", "insurance"},
    "DAP": {"fob_rate", "freight", "insurance"},
    "DPU": {"fob_rate", "freight", "insurance"},
    "DDP": {"fob_rate", "freight", "insurance"},
}
_ALL_CI_FIELDS = {"fob_rate", "freight", "insurance"}


def safe(v: Any, default: str = "") -> str:
    return default if v is None else str(v)


def _fmt_money(v: Any) -> str:
    try:
        # Strip trailing zeros: 12.00 → "12", 12.50 → "12.5"
        s = f"{float(v):,.2f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s
    except Exception:
        return safe(v)


def _fmt_qty(v: Any) -> str:
    try:
        # Strip trailing zeros: 12.000 → "12", 12.500 → "12.5"
        s = f"{float(v):,.3f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s
    except Exception:
        return safe(v)


def _amount_to_words(n: Any, currency: str = "USD") -> str:
    try:
        from num2words import num2words
        n = int(float(n or 0))
        words = num2words(n).title()
        return f"{words} {currency} Only"
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Organisation address helpers
# (Organisation has no direct address/email fields; must go via .addresses relation)
# ---------------------------------------------------------------------------

def _org_address_str(org) -> str:
    """Return a single comma-joined address string from the Organisation's first address."""
    if not org:
        return ""
    try:
        addr = org.addresses.first()
        if not addr:
            return ""
        parts = []
        if addr.line1:
            parts.append(addr.line1)
        if addr.line2:
            parts.append(addr.line2)
        city_state = ", ".join(filter(None, [addr.city, addr.state]))
        if city_state:
            parts.append(city_state)
        if getattr(addr, "pin", ""):
            parts.append(addr.pin)
        if getattr(addr, "country", None):
            parts.append(addr.country.name)
        return ", ".join(parts)
    except Exception:
        return ""


def _org_email(org) -> str:
    if not org:
        return ""
    try:
        addr = org.addresses.first()
        return addr.email if addr else ""
    except Exception:
        return ""


def _org_registered_address(org):
    """Return the REGISTERED OrganisationAddress instance, or None."""
    if not org:
        return None
    try:
        return org.addresses.filter(address_type="REGISTERED").first()
    except Exception:
        return None


def _make_ci_styles():
    """
    Build and return paragraph styles for the CI section.
    Names are prefixed 'CI' to avoid collisions when combined with PL story.
    """
    base = getSampleStyleSheet()

    style_company_header = ParagraphStyle(
        "CICompanyHeader", parent=base["Normal"],
        fontSize=16, leading=20, spaceAfter=6,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_title = ParagraphStyle(
        "CITitle", parent=base["Normal"],
        fontSize=12, leading=15, spaceAfter=10,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    style_label = ParagraphStyle(
        "CILabel", parent=base["Normal"],
        fontSize=9, leading=11, fontName="Helvetica-Bold",
    )
    style_text = ParagraphStyle(
        "CIText", parent=base["Normal"],
        fontSize=9, leading=11,
    )
    style_small = ParagraphStyle(
        "CISmall", parent=base["Normal"],
        fontSize=8, leading=10,
    )
    return style_company_header, style_title, style_label, style_text, style_small


# ---------------------------------------------------------------------------
# Story builder — used by generate_pl_ci_pdf to embed CI in a combined document.
# ---------------------------------------------------------------------------

def build_ci_story(ci, styles) -> list:
    """
    Build and return the list of story flowables for the Commercial Invoice section.

    Args:
        ci: CommercialInvoice model instance.
        styles: tuple returned by _make_ci_styles().

    Returns:
        list of ReportLab flowables (does NOT include a leading PageBreak).
    """
    style_company_header, style_title, style_label, style_text, style_small = styles
    story = []

    # Access the linked packing list for all shipping / party fields.
    pl = getattr(ci, "packing_list", None)

    # Exporter / Consignee / Buyer are on the PL, not directly on CI.
    exp = getattr(pl, "exporter", None) if pl else None
    cons = getattr(pl, "consignee", None) if pl else None
    buyer = getattr(pl, "buyer", None) if pl else None
    notify_party_org = getattr(pl, "notify_party", None) if pl else None

    # ---- Header ----------------------------------------------------------------
    story.append(Paragraph(safe(getattr(exp, "name", "")), style_company_header))
    story.append(Paragraph("COMMERCIAL INVOICE", style_title))
    story.append(Spacer(1, 8))

    # ---- Exporter details (Corporate address + Registered address columns) ----
    exp_address = _org_address_str(exp)
    exp_email = _org_email(exp)
    iec_code = safe(getattr(exp, "iec_code", ""))

    exp_lines = [safe(getattr(exp, "name", ""))]
    if iec_code:
        exp_lines.append(f"IEC Code: {iec_code}")
    if exp_address:
        exp_lines.append(exp_address)
    if exp_email:
        exp_lines.append(exp_email)
    exporter_html = "<b>Corporate Office</b><br/>" + "<br/>".join(ln for ln in exp_lines if ln)

    reg = _org_registered_address(exp)
    reg_html_parts = []
    if reg:
        addr_bits = []
        if getattr(reg, "line1", ""):
            addr_bits.append(reg.line1)
        if getattr(reg, "line2", ""):
            addr_bits.append(reg.line2)
        city_state = ", ".join(filter(None, [getattr(reg, "city", ""), getattr(reg, "state", "")]))
        if city_state:
            addr_bits.append(city_state)
        if getattr(reg, "country", None):
            addr_bits.append(reg.country.name)
        if addr_bits:
            reg_html_parts.append(", ".join(addr_bits))
        contact_bits = []
        if getattr(reg, "phone_country_code", "") and getattr(reg, "phone_number", ""):
            contact_bits.append(f"Phone: {reg.phone_country_code} {reg.phone_number}")
        elif getattr(reg, "phone_number", ""):
            contact_bits.append(f"Phone: {reg.phone_number}")
        if getattr(reg, "email", ""):
            contact_bits.append(f"Email: {reg.email}")
        if contact_bits:
            reg_html_parts.append(" • ".join(contact_bits))
    reg_html = "<b>Registered Office</b><br/>" + "<br/>".join(reg_html_parts)

    # ---- Order references (sourced from PL) ------------------------------------
    ref_lines = []
    if pl:
        po_no = safe(getattr(pl, "po_number", ""))
        po_date = safe(getattr(pl, "po_date", "")) if getattr(pl, "po_date", None) else ""
        lc_no = safe(getattr(pl, "lc_number", ""))
        lc_date = safe(getattr(pl, "lc_date", "")) if getattr(pl, "lc_date", None) else ""
        bl_no = safe(getattr(pl, "bl_number", ""))
        bl_date = safe(getattr(pl, "bl_date", "")) if getattr(pl, "bl_date", None) else ""
        so_no = safe(getattr(pl, "so_number", ""))
        so_date = safe(getattr(pl, "so_date", "")) if getattr(pl, "so_date", None) else ""
        other_ref = safe(getattr(pl, "other_references", ""))
        other_ref_date = (
            safe(getattr(pl, "other_references_date", ""))
            if getattr(pl, "other_references_date", None) else ""
        )
        if po_no:
            ref_lines.append(f"<b>PO No/Date:</b> {po_no}{(' / ' + po_date) if po_date else ''}")
        if lc_no:
            ref_lines.append(f"<b>LC No/Date:</b> {lc_no}{(' / ' + lc_date) if lc_date else ''}")
        if bl_no:
            ref_lines.append(f"<b>B/L No/Date:</b> {bl_no}{(' / ' + bl_date) if bl_date else ''}")
        if so_no:
            ref_lines.append(f"<b>SO No/Date:</b> {so_no}{(' / ' + so_date) if so_date else ''}")
        if other_ref:
            ref_lines.append(
                f"<b>Other Ref/Date:</b> {other_ref}"
                f"{(' / ' + other_ref_date) if other_ref_date else ''}"
            )

    ci_number = safe(getattr(ci, "ci_number", ""))
    ci_date = safe(getattr(ci, "ci_date", ""))

    # ---- Summary Top (Exporter | Registered | Invoice Date | Invoice No | Refs) -
    summary_top_data = [
        [
            Paragraph("<b>Exporter:</b>", style_label),  # spans col 0-1
            "",
            Paragraph(f"<b>Invoice Date:</b><br/>{ci_date}", style_text),
            Paragraph(f"<b>Invoice No:</b><br/>{ci_number}", style_text),
        ],
        [
            Paragraph(exporter_html, style_text),
            Paragraph(reg_html, style_text),
            Paragraph("<br/>".join(ref_lines), style_text),
            "",  # merged with col 2
        ],
    ]
    summary_top = Table(summary_top_data, colWidths=[60 * mm, 60 * mm, 30 * mm, 30 * mm])
    summary_top.hAlign = "LEFT"
    summary_top.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("SPAN",         (0, 0), (1, 0)),  # "Exporter:" spans col 0-1
        ("SPAN",         (2, 1), (3, 1)),  # References spans col 2-3
    ]))
    story.append(summary_top)
    story.append(Spacer(1, 0))

    # ---- Consignee + Buyer block ----------------------------------------------
    cons_lines = [safe(getattr(cons, "name", ""))]
    cons_address = _org_address_str(cons)
    cons_email = _org_email(cons)
    if cons_address:
        cons_lines.append(cons_address)
    if cons_email:
        cons_lines.append(cons_email)
    cons_html = "<b>Consignee</b><br/>" + "<br/>".join(ln for ln in cons_lines if ln)

    buyer_lines = []
    if buyer:
        buyer_lines.append(safe(getattr(buyer, "name", "")))
        buyer_address = _org_address_str(buyer)
        buyer_email = _org_email(buyer)
        if buyer_address:
            buyer_lines.append(buyer_address)
        if buyer_email:
            buyer_lines.append(buyer_email)
    buyer_html = "<b>Buyer</b><br/>" + "<br/>".join(ln for ln in buyer_lines if ln)

    cons_buyer_tbl = Table(
        [[Paragraph(cons_html, style_text), Paragraph(buyer_html, style_text)]],
        colWidths=[90 * mm, 90 * mm],
    )
    cons_buyer_tbl.hAlign = "LEFT"
    cons_buyer_tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(cons_buyer_tbl)
    story.append(Spacer(1, 0))

    # ---- Notify Party + Countries row ----------------------------------------
    notify_text = safe(getattr(notify_party_org, "name", "")) if notify_party_org else ""
    origin_country_obj = getattr(pl, "country_of_origin", None) if pl else None
    dest_country_obj = getattr(pl, "country_of_final_destination", None) if pl else None
    origin_name = safe(getattr(origin_country_obj, "name", "")) if origin_country_obj else ""
    dest_name = safe(getattr(dest_country_obj, "name", "")) if dest_country_obj else ""

    notify_countries_tbl = Table(
        [[
            Paragraph(f"<b>Notify Party</b><br/>{notify_text}", style_text),
            Paragraph(f"<b>Country of Origin of Goods</b><br/>{origin_name}", style_text),
            Paragraph(f"<b>Country of Final Destination</b><br/>{dest_name}", style_text),
        ]],
        colWidths=[90 * mm, 45 * mm, 45 * mm],
    )
    notify_countries_tbl.hAlign = "LEFT"
    notify_countries_tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(notify_countries_tbl)
    story.append(Spacer(1, 0))

    # ---- Shipping info (2 rows × 6 cols; last 3 cols merged for terms) --------
    pre_carriage_obj = getattr(pl, "pre_carriage_by", None) if pl else None
    pre_carriage_val = safe(getattr(pre_carriage_obj, "name", "")) if pre_carriage_obj else ""

    place_receipt_obj = getattr(pl, "place_of_receipt_by_pre_carrier", None) if pl else None
    place_receipt_val = safe(getattr(place_receipt_obj, "name", "")) if place_receipt_obj else ""

    vessel_flight_val = safe(getattr(pl, "vessel_flight_no", "")) if pl else ""

    port_loading_obj = getattr(pl, "port_of_loading", None) if pl else None
    port_loading_val = safe(getattr(port_loading_obj, "name", "")) if port_loading_obj else ""

    port_discharge_obj = getattr(pl, "port_of_discharge", None) if pl else None
    port_discharge_val = safe(getattr(port_discharge_obj, "name", "")) if port_discharge_obj else ""

    final_dest_obj = getattr(pl, "final_destination", None) if pl else None
    final_destination_val = safe(getattr(final_dest_obj, "name", "")) if final_dest_obj else ""

    incoterm_obj = getattr(pl, "incoterms", None) if pl else None
    incoterm_str = safe(getattr(incoterm_obj, "code", "")) if incoterm_obj else ""
    payment_term_obj = getattr(pl, "payment_terms", None) if pl else None
    payment_term_str = safe(getattr(payment_term_obj, "name", "")) if payment_term_obj else ""
    terms_merged_html = (
        "<b>Incoterms:</b> " + incoterm_str
        + ("<br/>" if incoterm_str or payment_term_str else "")
        + "<b>Payment Terms:</b> " + payment_term_str
    )

    shipping_data = [
        [
            Paragraph(f"<b>Pre-carriage by</b><br/>{pre_carriage_val}", style_text),
            Paragraph(f"<b>Place of Receipt by Pre-Carrier</b><br/>{place_receipt_val}", style_text),
            Paragraph(f"<b>Vessel/Flight No.</b><br/>{vessel_flight_val}", style_text),
            Paragraph(terms_merged_html, style_text),  # spans (3,0)→(5,1)
            "", "",
        ],
        [
            Paragraph(f"<b>Port of Loading</b><br/>{port_loading_val}", style_text),
            Paragraph(f"<b>Port of Discharge</b><br/>{port_discharge_val}", style_text),
            Paragraph(f"<b>Final Destination</b><br/>{final_destination_val}", style_text),
            "", "", "",
        ],
    ]
    shipping_tbl = Table(shipping_data, colWidths=[30 * mm] * 6)
    shipping_tbl.hAlign = "LEFT"
    shipping_tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("SPAN",         (3, 0), (5, 1)),  # Incoterms+Payment merged across last 3 cols × 2 rows
    ]))
    story.append(shipping_tbl)
    story.append(Spacer(1, 6))

    # ---- Build packages lookup: item_code → set of packages_kind strings -----
    packages_map: dict = {}
    if pl:
        try:
            for cont in pl.containers.all().order_by("id"):
                for pitem in cont.items.all().order_by("id"):
                    key = safe(getattr(pitem, "item_code", ""))
                    val = safe(getattr(pitem, "packages_kind", ""))
                    if not key:
                        continue
                    if key not in packages_map:
                        packages_map[key] = set()
                    if val:
                        packages_map[key].add(val)
        except Exception:
            pass

    # ---- Line items table ------------------------------------------------------
    li_header = [
        Paragraph("<b>Sr.</b>", style_label),
        Paragraph("<b>HSN Code</b>", style_label),
        Paragraph("<b>No &amp; Kind of Packages</b>", style_label),
        Paragraph("<b>Item Code</b>", style_label),
        Paragraph("<b>Description of Goods</b>", style_label),
        Paragraph("<b>Qty</b>", style_label),
        Paragraph("<b>Rate (USD)</b>", style_label),
        Paragraph("<b>Amount (USD)</b>", style_label),
    ]
    li_rows = [li_header]
    total_amount_usd = Decimal("0.00")

    idx = 0
    for it in ci.line_items.all().order_by("id"):
        idx += 1
        pkg_text = ""
        try:
            pkset = packages_map.get(safe(getattr(it, "item_code", "")), None)
            if pkset:
                pkg_text = " ; ".join(sorted(pkset))
        except Exception:
            pass

        uom_obj = getattr(it, "uom", None)
        uom_display = safe(getattr(uom_obj, "abbreviation", "")) if uom_obj else ""
        qty_val = getattr(it, "total_quantity", None)
        rate_val = getattr(it, "rate_usd", None)
        amount_val = getattr(it, "amount_usd", None)

        if amount_val is not None:
            try:
                total_amount_usd += Decimal(str(amount_val))
            except Exception:
                pass

        li_rows.append([
            Paragraph(str(idx), style_text),
            Paragraph(safe(it.hsn_code), style_text),
            Paragraph(pkg_text, style_text),
            Paragraph(safe(it.item_code), style_text),
            Paragraph(safe(it.description), style_text),
            Paragraph(f"{_fmt_qty(qty_val)} {uom_display}".strip(), style_text),
            Paragraph(_fmt_money(rate_val), style_text),
            Paragraph(_fmt_money(amount_val), style_text),
        ])

    # Col widths: 10+22+28+22+52+20+13+13 = 180mm
    li_table = Table(
        li_rows,
        colWidths=[10 * mm, 22 * mm, 28 * mm, 22 * mm, 52 * mm, 20 * mm, 13 * mm, 13 * mm],
    )
    li_table.hAlign = "LEFT"
    li_table.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND",   (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("ALIGN",        (6, 1), (7, -1), "RIGHT"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(li_table)
    story.append(Spacer(1, 6))

    # ---- Weight totals + LC Details + FOB/Freight/Insurance ------------------
    total_net_val = Decimal("0.000")
    total_gross_val = Decimal("0.000")
    if pl:
        try:
            for cont in pl.containers.all().order_by("id"):
                # Net weight computed from items (Container has no .net_weight field)
                for item in cont.items.all():
                    if item.net_weight is not None and item.quantity is not None:
                        try:
                            total_net_val += (
                                Decimal(str(item.net_weight)) * Decimal(str(item.quantity))
                            )
                        except Exception:
                            pass
                # Gross weight is stored on Container
                gw = getattr(cont, "gross_weight", None)
                if gw is not None:
                    try:
                        total_gross_val += Decimal(str(gw))
                    except Exception:
                        pass
        except Exception:
            pass

    lc_details_val = safe(getattr(ci, "lc_details", ""))
    fob_rate_val = _fmt_money(getattr(ci, "fob_rate", 0))
    freight_val = _fmt_money(getattr(ci, "freight", 0))
    insurance_val = _fmt_money(getattr(ci, "insurance", 0))

    # Only print cost fields that are relevant for the selected Incoterm.
    # If no Incoterm is set, show all three fields (safe default).
    visible_fields = _INCOTERM_VISIBLE_FIELDS.get(incoterm_str, _ALL_CI_FIELDS)

    # Build right-column charge rows — only for visible fields, in fixed order.
    charge_rows: list = []
    if "fob_rate" in visible_fields:
        charge_rows.append(f"<b>FOB Rate:</b> {fob_rate_val}")
    if "freight" in visible_fields:
        charge_rows.append(f"<b>Freight:</b> {freight_val}")
    if "insurance" in visible_fields:
        charge_rows.append(f"<b>Insurance:</b> {insurance_val}")

    # Left column is always: Net Weight, Gross Weight, L/C Details.
    left_rows = [
        f"<b>Total Net Weight:</b> {_fmt_qty(total_net_val)}",
        f"<b>Total Gross Weight:</b> {_fmt_qty(total_gross_val)}",
        f"<b>L/C Details:</b> {lc_details_val}",
    ]

    # Pair rows; pad the shorter side with empty strings so the table is rectangular.
    n_rows = max(len(left_rows), len(charge_rows))
    charges_table_data = [
        [
            Paragraph(left_rows[i] if i < len(left_rows) else "", style_text),
            Paragraph(charge_rows[i] if i < len(charge_rows) else "", style_text),
        ]
        for i in range(n_rows)
    ]

    totals_charges_tbl = Table(charges_table_data, colWidths=[90 * mm, 90 * mm])
    totals_charges_tbl.hAlign = "LEFT"
    totals_charges_tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(totals_charges_tbl)
    story.append(Spacer(1, 6))

    # ---- Total Amount (USD) row -----------------------------------------------
    totals_table = Table(
        [[
            Paragraph("<b>Amount (Local):</b>", style_text),
            Paragraph("", style_text),  # No local-amount field on CI model
            Paragraph("<b>Total Amount (USD):</b>", style_text),
            Paragraph(f"${_fmt_money(total_amount_usd)}", style_text),
        ]],
        colWidths=[50 * mm, 40 * mm, 60 * mm, 30 * mm],
    )
    totals_table.hAlign = "LEFT"
    totals_table.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 6))

    # ---- Amount in words -------------------------------------------------------
    amount_in_words_str = _amount_to_words(total_amount_usd, currency="USD")
    if amount_in_words_str:
        story.append(Paragraph(f"<b>Amount in Words:</b> {amount_in_words_str}", style_text))
        story.append(Spacer(1, 6))

    # ---- Declaration -----------------------------------------------------------
    story.append(Paragraph(
        "Declaration: We declare that this invoice shows actual price of the goods "
        "described and that all particulars are true and correct.",
        style_text,
    ))
    story.append(Spacer(1, 6))

    # ---- Bank details ----------------------------------------------------------
    bank = getattr(ci, "bank", None)
    if bank:
        beneficiary_data = [
            [Paragraph(
                f"<b>BENEFICIARY NAME:</b> {safe(getattr(bank, 'beneficiary_name', ''))}",
                style_text,
            )],
            [Paragraph(f"<b>BANK NAME:</b> {safe(getattr(bank, 'bank_name', ''))}", style_text)],
            [Paragraph(f"<b>BRANCH NAME:</b> {safe(getattr(bank, 'branch_name', ''))}", style_text)],
            [Paragraph(
                f"<b>BRANCH ADDRESS:</b> {safe(getattr(bank, 'branch_address', ''))}",
                style_text,
            )],
            [Paragraph(f"<b>A/C NO.:</b> {safe(getattr(bank, 'account_number', ''))}", style_text)],
            [Paragraph(f"<b>SWIFT CODE:</b> {safe(getattr(bank, 'swift_code', ''))}", style_text)],
        ]
        beneficiary_table = Table(beneficiary_data, colWidths=[180 * mm])
        beneficiary_table.hAlign = "LEFT"
        beneficiary_table.setStyle(TableStyle([
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING",   (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ]))
        story.append(beneficiary_table)
        story.append(Spacer(1, 10))

    return story


def generate_commercial_invoice_pdf_bytes(ci) -> bytes:
    """
    Generate a standalone Commercial Invoice PDF.
    Constraint #20: built entirely in-memory; never written to disk.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=10 * mm,
        bottomMargin=15 * mm,
    )

    def add_footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(
            A4[0] / 2, 10 * mm,
            "This is a computer-generated document. Signature is not required.",
        )
        canvas.restoreState()

    styles = _make_ci_styles()
    story = build_ci_story(ci, styles)
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
