"""
CIF Client Invoice PDF generator.

Produces a combined PDF:
  Section 1 — CIF-adjusted Commercial Invoice
  Section 2 — Packing List / Weight Note  (same as the standard combined PDF)

The CI section mirrors the standard layout but replaces each line item's
rate and amount with CIF-adjusted values:
  - Freight allocated proportionally to net_material_weight per item_code
  - Insurance allocated proportionally to FOB value per item_code
  - Rate (CIF) = original_rate + (freight_share + insurance_share) / qty
  - Amount (CIF) = original_amount + freight_share + insurance_share

Constraint #20: Returns a BytesIO buffer — never writes to disk.
"""
from decimal import Decimal, ROUND_HALF_UP
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfgen import canvas

# Reuse all shared helpers from the standard CI generator.
from pdf.commercial_invoice_generator import (
    safe,
    fmt_date,
    _fmt_money,
    _fmt_rate,
    _fmt_qty,
    _amount_to_words,
    _party_cell_html,
    _make_ci_styles,
    _INCOTERM_VISIBLE_FIELDS,
    _ALL_CI_FIELDS,
)

_GRID = [
    ("BOX",           (0, 0), (-1, -1), 1.2, colors.black),
    ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.black),
    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ("TOPPADDING",    (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]


def _exp_cell(label: str, addr, exp) -> str:
    """Build exporter address cell HTML (same logic as in build_ci_story)."""
    parts = []
    if exp:
        parts.append(safe(getattr(exp, "name", "")))
    if addr:
        if getattr(addr, "line1", ""):
            parts.append(addr.line1)
        if getattr(addr, "line2", ""):
            parts.append(addr.line2)
        city_parts = [v for v in (getattr(addr, "city", ""), getattr(addr, "pin", ""),
                                  getattr(addr, "state", "")) if v]
        if getattr(addr, "country", None):
            city_parts.append(addr.country.name)
        if city_parts:
            parts.append(", ".join(city_parts))
        phone_cc = getattr(addr, "phone_country_code", "")
        phone_no = getattr(addr, "phone_number", "")
        if phone_cc and phone_no:
            parts.append(f"Ph: {phone_cc} {phone_no}")
        elif phone_no:
            parts.append(f"Ph: {phone_no}")
        if getattr(addr, "email", ""):
            parts.append(addr.email)
        iec = getattr(addr, "iec_code", "")
        if iec:
            parts.append(f"IEC: {iec}")
        tax_type = getattr(addr, "tax_type", "")
        tax_code_v = getattr(addr, "tax_code", "")
        if tax_type and tax_code_v:
            parts.append(f"{tax_type}: {tax_code_v}")
    body = "<br/>".join(parts)
    return f"<b>{label}</b><br/>{body}" if body else f"<b>{label}</b>"


def build_cif_client_story(ci, styles) -> list:
    """
    Build the ReportLab story for a CIF Client Invoice.

    Identical layout to the standard CI but with CIF-adjusted rates/amounts:
    freight allocated by weight, insurance allocated by FOB value.
    """
    style_company_header, style_title, style_label, style_text, style_small, style_table_header = styles
    story = []

    pl = getattr(ci, "packing_list", None)
    exp = getattr(pl, "exporter", None) if pl else None
    cons = getattr(pl, "consignee", None) if pl else None
    buyer = getattr(pl, "buyer", None) if pl else None
    notify_party_org = getattr(pl, "notify_party", None) if pl else None

    pi = getattr(pl, "proforma_invoice", None) if pl else None
    currency_code = pi.currency.code if pi else "USD"

    story.append(Paragraph(safe(getattr(exp, "name", "")), style_company_header))
    story.append(Paragraph("COMMERCIAL INVOICE", style_title))

    line_table = Table([[""]], colWidths=[180 * mm])
    line_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 10))

    col_4 = 180 * mm / 4
    col_3 = 180 * mm / 3
    col_2 = 90 * mm

    # --- exporter addresses ---
    corp_addr = (
        (exp.addresses.filter(address_type="OFFICE").first()
         or exp.addresses.filter(address_type="REGISTERED").first())
        if exp else None
    )
    reg_addr = (exp.addresses.filter(address_type="REGISTERED").first() if exp else None)
    factory_addr = (exp.addresses.filter(address_type="FACTORY").first() if exp else None)

    # --- reference lines ---
    ref_lines = []
    if pl:
        po_no = safe(getattr(pl, "po_number", ""))
        po_date = fmt_date(getattr(pl, "po_date", None))
        lc_no = safe(getattr(pl, "lc_number", ""))
        lc_date = fmt_date(getattr(pl, "lc_date", None))
        bl_no = safe(getattr(pl, "bl_number", ""))
        bl_date = fmt_date(getattr(pl, "bl_date", None))
        so_no = safe(getattr(pl, "so_number", ""))
        so_date = fmt_date(getattr(pl, "so_date", None))
        other_ref = safe(getattr(pl, "other_references", ""))
        other_ref_date = fmt_date(getattr(pl, "other_references_date", None))
        if po_no:
            ref_lines.append(f"<b>PO No/Date:</b> {po_no}{(' / ' + po_date) if po_date else ''}")
        if lc_no:
            ref_lines.append(f"<b>LC No/Date:</b> {lc_no}{(' / ' + lc_date) if lc_date else ''}")
        if bl_no:
            ref_lines.append(f"<b>BL No/Date:</b> {bl_no}{(' / ' + bl_date) if bl_date else ''}")
        if so_no:
            ref_lines.append(f"<b>SO No/Date:</b> {so_no}{(' / ' + so_date) if so_date else ''}")
        if other_ref:
            ref_lines.append(
                f"<b>Other Ref/Date:</b> {other_ref}"
                f"{(' / ' + other_ref_date) if other_ref_date else ''}"
            )
    refs_cell_html = (
        "<b>Other References</b><br/>" + "<br/>".join(ref_lines)
        if ref_lines else "<b>Other References</b>"
    )

    pi_obj = getattr(pl, "proforma_invoice", None) if pl else None
    pi_number = safe(getattr(pi_obj, "pi_number", "")) if pi_obj else ""
    ci_number = safe(getattr(ci, "ci_number", ""))

    pi_number_with_date = pi_number
    if pi_obj:
        pi_date = getattr(pi_obj, "pi_date", None)
        if pi_date:
            pi_number_with_date = f"{pi_number} {fmt_date(pi_date)}"

    from apps.workflow.constants import APPROVED
    ci_status = getattr(ci, "status", None)
    if ci_status == APPROVED:
        ci_date_display = ""
        try:
            from apps.workflow.models import AuditLog
            approval_log = AuditLog.objects.filter(
                document_type="commercial_invoice",
                document_id=ci.id,
                action="APPROVE"
            ).order_by("-created_at").first()
            if approval_log:
                ci_date_display = fmt_date(approval_log.created_at.date())
        except Exception:
            pass
    else:
        from datetime import date
        ci_date_display = fmt_date(date.today())

    ci_number_with_date = f"{ci_number} {ci_date_display}" if ci_date_display else ci_number

    header_tbl = Table(
        [[
            Paragraph("<b>Exporter</b>", style_label),
            "",
            Paragraph(f"<b>Proforma Invoice No.</b><br/>{pi_number_with_date}", style_text),
            Paragraph(f"<b>Commercial Invoice No.</b><br/>{ci_number_with_date}", style_text),
        ]],
        colWidths=[col_4, col_4, col_4, col_4],
    )
    header_tbl.hAlign = "LEFT"
    header_tbl.setStyle(TableStyle(_GRID + [
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A2B4B")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
    ]))
    story.append(header_tbl)

    if factory_addr:
        exp_tbl = Table(
            [[Paragraph(_exp_cell("Corporate Office", corp_addr, exp), style_text),
              Paragraph(_exp_cell("Registered Office Address", reg_addr, exp), style_text),
              Paragraph(_exp_cell("Factory Address", factory_addr, exp), style_text)]],
            colWidths=[col_3, col_3, col_3],
        )
    else:
        exp_tbl = Table(
            [[Paragraph(_exp_cell("Corporate Office", corp_addr, exp), style_text),
              Paragraph(_exp_cell("Registered Office Address", reg_addr, exp), style_text)]],
            colWidths=[col_2, col_2],
        )
    exp_tbl.hAlign = "LEFT"
    exp_tbl.setStyle(TableStyle(_GRID))
    story.append(exp_tbl)

    buyer_cell = _party_cell_html("Buyer", buyer if buyer else cons)
    cons_cell = _party_cell_html("Consignee", cons)
    if notify_party_org:
        notify_cell = _party_cell_html("Notify Party", notify_party_org)
        party_tbl = Table(
            [[Paragraph(buyer_cell, style_text), Paragraph(cons_cell, style_text),
              Paragraph(notify_cell, style_text)]],
            colWidths=[col_3, col_3, col_3],
        )
    else:
        party_tbl = Table(
            [[Paragraph(buyer_cell, style_text), Paragraph(cons_cell, style_text)]],
            colWidths=[col_2, col_2],
        )
    party_tbl.hAlign = "LEFT"
    party_tbl.setStyle(TableStyle(_GRID))
    story.append(party_tbl)

    pre_carriage_obj = getattr(pl, "pre_carriage_by", None) if pl else None
    pre_carriage_val = safe(getattr(pre_carriage_obj, "name", "")) if pre_carriage_obj else ""
    place_receipt_obj = getattr(pl, "place_of_receipt_by_pre_carrier", None) if pl else None
    place_receipt_val = safe(getattr(place_receipt_obj, "name", "")) if place_receipt_obj else ""
    port_loading_obj = getattr(pl, "port_of_loading", None) if pl else None
    port_loading_val = safe(getattr(port_loading_obj, "name", "")) if port_loading_obj else ""
    port_discharge_obj = getattr(pl, "port_of_discharge", None) if pl else None
    port_discharge_val = safe(getattr(port_discharge_obj, "name", "")) if port_discharge_obj else ""
    final_dest_obj = getattr(pl, "final_destination", None) if pl else None
    final_dest_val = safe(getattr(final_dest_obj, "name", "")) if final_dest_obj else ""
    dest_country_obj = getattr(pl, "country_of_final_destination", None) if pl else None
    dest_country_val = safe(getattr(dest_country_obj, "name", "")) if dest_country_obj else ""
    origin_country_obj = getattr(pl, "country_of_origin", None) if pl else None
    origin_country_val = safe(getattr(origin_country_obj, "name", "")) if origin_country_obj else ""
    vessel_flight_val = safe(getattr(pl, "vessel_flight_no", "")) if pl else ""

    shipping_tbl = Table(
        [
            [
                Paragraph(f"<b>Pre-carriage by</b><br/>{pre_carriage_val}", style_text),
                Paragraph(f"<b>Place of Receipt by Pre-Carrier</b><br/>{place_receipt_val}", style_text),
                Paragraph(f"<b>Port of Loading</b><br/>{port_loading_val}", style_text),
                Paragraph(f"<b>Port of Discharge</b><br/>{port_discharge_val}", style_text),
            ],
            [
                Paragraph(f"<b>Final Destination</b><br/>{final_dest_val}", style_text),
                Paragraph(f"<b>Country of Final Destination</b><br/>{dest_country_val}", style_text),
                Paragraph(f"<b>Country of Origin of Goods</b><br/>{origin_country_val}", style_text),
                Paragraph(f"<b>Vessel / Flight No.</b><br/>{vessel_flight_val}", style_text),
            ],
        ],
        colWidths=[col_4, col_4, col_4, col_4],
    )
    shipping_tbl.hAlign = "LEFT"
    shipping_tbl.setStyle(TableStyle(_GRID))
    story.append(shipping_tbl)

    incoterm_obj = getattr(pl, "incoterms", None) if pl else None
    incoterm_str = safe(getattr(incoterm_obj, "code", "")) if incoterm_obj else ""
    payment_term_obj = getattr(pl, "payment_terms", None) if pl else None
    payment_term_str = safe(getattr(payment_term_obj, "name", "")) if payment_term_obj else ""
    terms_tbl = Table(
        [[
            Paragraph(f"<b>Payment Terms</b><br/>{payment_term_str}", style_text),
            Paragraph(f"<b>Incoterms</b><br/>{incoterm_str}", style_text),
            Paragraph(refs_cell_html, style_text),
        ]],
        colWidths=[col_3, col_3, col_3],
    )
    terms_tbl.hAlign = "LEFT"
    terms_tbl.setStyle(TableStyle(_GRID))
    story.append(terms_tbl)
    story.append(Spacer(1, 12))

    # ---- CIF allocation setup -----------------------------------------------

    visible_fields = _INCOTERM_VISIBLE_FIELDS.get(incoterm_str, _ALL_CI_FIELDS)

    freight_amount = Decimal("0.00")
    insurance_amount = Decimal("0.00")
    if "freight" in visible_fields and getattr(ci, "freight", None) is not None:
        try:
            freight_amount = Decimal(str(ci.freight))
        except Exception:
            pass
    if "insurance" in visible_fields and getattr(ci, "insurance", None) is not None:
        try:
            insurance_amount = Decimal(str(ci.insurance))
        except Exception:
            pass

    # Aggregate net_material_weight per item_code across all containers
    weight_map: dict = {}
    if pl:
        try:
            for cont in pl.containers.all().order_by("id"):
                for cont_item in cont.items.all():
                    ic = safe(getattr(cont_item, "item_code", ""))
                    try:
                        wt = Decimal(str(cont_item.net_material_weight or 0))
                    except Exception:
                        wt = Decimal("0")
                    weight_map[ic] = weight_map.get(ic, Decimal("0")) + wt
        except Exception:
            pass

    total_weight = sum(weight_map.values(), Decimal("0"))

    # Pre-compute FOB total for insurance proportion
    fob_total = Decimal("0.00")
    for it in ci.line_items.all().order_by("id"):
        try:
            fob_total += Decimal(str(getattr(it, "amount", None) or 0))
        except Exception:
            pass

    # ---- CIF-adjusted line items table --------------------------------------

    li_header = [
        Paragraph("<b>Sr.</b>", style_table_header),
        Paragraph("<b>HSN Code</b>", style_table_header),
        Paragraph("<b>No &amp; Kind of Packages</b>", style_table_header),
        Paragraph("<b>Item Code</b>", style_table_header),
        Paragraph("<b>Description of Goods</b>", style_table_header),
        Paragraph("<b>Qty</b>", style_table_header),
        Paragraph(f"<b>Rate ({currency_code}) CIF</b>", style_table_header),
        Paragraph(f"<b>Amount ({currency_code}) CIF</b>", style_table_header),
    ]
    li_rows = [li_header]
    cif_total = Decimal("0.00")

    idx = 0
    for it in ci.line_items.all().order_by("id"):
        idx += 1
        item_code = safe(getattr(it, "item_code", ""))
        item_weight = weight_map.get(item_code, Decimal("0"))

        item_fob = Decimal("0.00")
        try:
            item_fob = Decimal(str(getattr(it, "amount", None) or 0))
        except Exception:
            pass

        qty = Decimal("1")
        try:
            qty_raw = getattr(it, "total_quantity", None)
            if qty_raw:
                qty = Decimal(str(qty_raw))
        except Exception:
            pass

        # Freight: proportional to net material weight
        freight_share = Decimal("0.00")
        if total_weight > 0 and freight_amount > 0:
            freight_share = (
                item_weight / total_weight * freight_amount
            ).quantize(Decimal("0.01"), ROUND_HALF_UP)

        # Insurance: proportional to FOB value
        insurance_share = Decimal("0.00")
        if fob_total > 0 and insurance_amount > 0:
            insurance_share = (
                item_fob / fob_total * insurance_amount
            ).quantize(Decimal("0.01"), ROUND_HALF_UP)

        cif_amount = item_fob + freight_share + insurance_share
        cif_rate = Decimal("0.00")
        if qty > 0:
            cif_rate = (cif_amount / qty).quantize(Decimal("0.0001"), ROUND_HALF_UP)

        cif_total += cif_amount

        pkg_text = safe(getattr(it, "packages_kind", ""))
        uom_obj = getattr(it, "uom", None)
        uom_display = safe(getattr(uom_obj, "abbreviation", "")) if uom_obj else ""

        li_rows.append([
            Paragraph(str(idx), style_text),
            Paragraph(safe(it.hsn_code), style_text),
            Paragraph(pkg_text, style_text),
            Paragraph(item_code, style_text),
            Paragraph(safe(it.description), style_text),
            Paragraph(f"{_fmt_qty(qty)} {uom_display}".strip(), style_text),
            Paragraph(_fmt_rate(cif_rate), style_text),
            Paragraph(_fmt_money(cif_amount), style_text),
        ])

    # Sr(10) + HSN(22) + Packages(24) + ItemCode(20) + Desc(46) + Qty(18) + Rate(20) + Amt(20) = 180mm
    li_table = Table(
        li_rows,
        colWidths=[10 * mm, 22 * mm, 24 * mm, 20 * mm, 46 * mm, 18 * mm, 20 * mm, 20 * mm],
    )
    li_table.hAlign = "LEFT"
    li_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1A2B4B")),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
        ("ALIGN",        (6, 1), (7, -1), "RIGHT"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (0, 0), 6),
        ("BOTTOMPADDING",(0, 0), (0, 0), 6),
        ("TOPPADDING",   (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 4),
    ]))
    story.append(li_table)
    story.append(Spacer(1, 12))

    # ---- Totals (weights left, CIF breakdown right) -------------------------

    total_net_val = Decimal("0.000")
    total_gross_val = Decimal("0.000")
    if pl:
        try:
            for cont in pl.containers.all().order_by("id"):
                for item in cont.items.all():
                    net_mat_wt = getattr(item, "net_material_weight", None)
                    if net_mat_wt is not None:
                        try:
                            total_net_val += Decimal(str(net_mat_wt))
                        except Exception:
                            pass
                gw = getattr(cont, "gross_weight", None)
                if gw is not None:
                    try:
                        total_gross_val += Decimal(str(gw))
                    except Exception:
                        pass
        except Exception:
            pass

    lc_details_val = safe(getattr(ci, "lc_details", ""))

    left_inner_rows = [
        [Paragraph(f"<b>Total Net Weight:</b> {_fmt_qty(total_net_val)} KGS", style_text)],
    ]
    if lc_details_val:
        left_inner_rows.append(
            [Paragraph(f"<b>L/C Details:</b> {lc_details_val}", style_text)]
        )
    left_inner = Table(left_inner_rows, colWidths=[78 * mm])
    left_inner.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    # Right cell: Total Gross Weight
    right_inner = Table(
        [[Paragraph(f"<b>Total Gross Weight:</b> {_fmt_qty(total_gross_val)} KGS", style_text)]],
        colWidths=[78 * mm],
    )
    right_inner.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    totals_charges_tbl = Table(
        [[left_inner, right_inner]],
        colWidths=[90 * mm, 90 * mm],
    )
    totals_charges_tbl.hAlign = "LEFT"
    totals_charges_tbl.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(totals_charges_tbl)

    cif_total_tbl = Table(
        [[
            Paragraph("<b>CIF Total (Amount Payable)</b>", style_label),
            Paragraph(f"<b>{currency_code} {_fmt_money(cif_total)}</b>", style_label),
        ]],
        colWidths=[140 * mm, 40 * mm],
    )
    cif_total_tbl.hAlign = "LEFT"
    cif_total_tbl.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 1.2, colors.black),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#1A2B4B")),
        ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
    ]))
    story.append(cif_total_tbl)
    story.append(Spacer(1, 6))

    amount_in_words_str = _amount_to_words(cif_total, currency=currency_code)
    if amount_in_words_str:
        style_text_center = ParagraphStyle("CIFTextCenter", parent=style_text, alignment=TA_CENTER)
        words_table = Table(
            [[Paragraph(f"<b>Amount in Words:</b> {amount_in_words_str}", style_text_center)]],
            colWidths=[180 * mm],
        )
        words_table.setStyle(TableStyle([
            ("BOX",          (0, 0), (-1, -1), 1.2, colors.black),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ]))
        words_table.hAlign = "LEFT"
        story.append(words_table)

    story.append(Spacer(1, 12))

    decl_table = Table(
        [[Paragraph(
            "<b>Declaration:</b> We declare that this invoice shows actual price of the goods "
            "described and that all particulars are true and correct.",
            style_text,
        )]],
        colWidths=[180 * mm],
    )
    decl_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 1.2, colors.black),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    decl_table.hAlign = "LEFT"
    story.append(decl_table)
    story.append(Spacer(1, 12))

    bank = getattr(ci, "bank", None)
    if bank:
        bank_lines = []
        bank_lines.append(f"<b>BENEFICIARY NAME:</b> {safe(getattr(bank, 'beneficiary_name', ''))}")
        bank_lines.append(f"<b>BANK NAME:</b> {safe(getattr(bank, 'bank_name', ''))}")
        bank_lines.append(f"<b>BRANCH NAME:</b> {safe(getattr(bank, 'branch_name', ''))}")
        bank_lines.append(f"<b>BRANCH ADDRESS:</b> {safe(getattr(bank, 'branch_address', ''))}")
        bank_lines.append(f"<b>A/C NO.:</b> {safe(getattr(bank, 'account_number', ''))}")
        if getattr(bank, "routing_number", None):
            bank_lines.append(f"<b>IFSC CODE:</b> {safe(bank.routing_number)}")
        if getattr(bank, "swift_code", None):
            bank_lines.append(f"<b>SWIFT CODE:</b> {safe(bank.swift_code)}")
        if getattr(bank, "iban", None):
            bank_lines.append(f"<b>IBAN:</b> {safe(bank.iban)}")
        if safe(getattr(bank, "intermediary_bank_name", "")):
            intermediary_currency_code = (
                safe(getattr(bank.intermediary_currency, "code", ""))
                if getattr(bank, "intermediary_currency", None) else ""
            )
            bank_lines.append(
                f"<b>Intermediary Institution Routing for Currency</b> {intermediary_currency_code} "
                f"<b>A/C No.:</b> {safe(bank.intermediary_account_number)} "
                f"The Bank of {safe(bank.intermediary_bank_name)} "
                f"<b>SWIFT Code:</b> {safe(bank.intermediary_swift_code)}"
            )
        bank_lines.append(
            "Request your bank to send MT 103 Message to our bank and send us copy of this "
            "message to trace &amp; claim the payment from our bank."
        )
        bank_rows = [[Paragraph(line, style_text)] for line in bank_lines]
        bank_box = Table(bank_rows, colWidths=[180 * mm])
        bank_box.setStyle(TableStyle([
            ("LINEABOVE",    (0, 0),  (-1, 0),  1.2, colors.black),
            ("LINEBELOW",    (0, -1), (-1, -1), 1.2, colors.black),
            ("LINEBEFORE",   (0, 0),  (0, -1),  1.2, colors.black),
            ("LINEAFTER",    (-1, 0), (-1, -1), 1.2, colors.black),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ]))
        bank_box.hAlign = "LEFT"
        story.append(bank_box)
        story.append(Spacer(1, 10))

    return story


def generate_cif_client_invoice_pdf(pl) -> io.BytesIO:
    """
    Generate a combined CIF Client Invoice + Packing List PDF.
    Returns an in-memory BytesIO buffer — constraint #20: never writes to disk.
    """
    try:
        ci = pl.commercial_invoice
    except Exception:
        ci = None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )

    story = []

    if ci is not None:
        try:
            ci_styles = _make_ci_styles()
            story = build_cif_client_story(ci, ci_styles)
        except Exception:
            pass

    try:
        from pdf.packing_list_generator import _make_pl_styles, build_pl_story
        pl_styles = _make_pl_styles()
        if story:
            story.append(PageBreak())
        story += build_pl_story(pl, pl_styles)
    except ImportError:
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        styles = getSampleStyleSheet()
        if story:
            story.append(PageBreak())
        story += [
            Paragraph("PACKING LIST", styles["Title"]),
            Spacer(1, 12),
            Paragraph("Packing list content would appear here.", styles["Normal"]),
        ]

    from apps.workflow.constants import APPROVED as _APPROVED
    from reportlab.lib.colors import HexColor as _HexColor
    is_draft = getattr(pl, "status", None) != _APPROVED

    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total_pages = len(self._saved_page_states)
            for page_num, state in enumerate(self._saved_page_states, start=1):
                self.__dict__.update(state)
                self._draw_footer(page_num, total_pages)
                super().showPage()
            super().save()

        def _draw_footer(self, page_num, total_pages):
            if is_draft:
                self.saveState()
                self.setFont("Helvetica-Bold", 80)
                self.setFillColor(_HexColor("#CC0000"), alpha=0.15)
                self.translate(A4[0] / 2, A4[1] / 2)
                self.rotate(45)
                self.drawCentredString(0, 0, "DRAFT")
                self.restoreState()

            self.saveState()
            self.setStrokeColor(_HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(15 * mm, 17 * mm, A4[0] - 15 * mm, 17 * mm)
            self.setFont("Helvetica", 8)
            self.drawCentredString(
                A4[0] / 2, 12 * mm,
                "This is a computer generated document and does not require signature",
            )
            self.setFont("Helvetica", 7)
            self.drawCentredString(
                A4[0] / 2, 8 * mm,
                f"Page {page_num} of {total_pages}",
            )
            self.restoreState()

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
