"""
Proforma Invoice PDF generator (FR-09.6).

Constraint #20: Returns an in-memory BytesIO buffer — never writes to disk.
Uses ReportLab (canvas + Platypus) with the shared design system from pdf/base.py.

PDF title: "PROFORMA INVOICE / CUM SALES CONTRACT"
"""
import io
from decimal import Decimal

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from apps.proforma_invoice.serializers import INCOTERM_SELLER_FIELDS, FOB_ONLY_INCOTERMS
from pdf.base import (
    COLOR_BLUE_ACCENT, COLOR_BORDER, COLOR_LIGHT_BG, COLOR_NAVY, COLOR_TEXT_MUTED,
    COLOR_WHITE,
    CONTENT_W, DOC_TOP_MARGIN, FONT_BODY, FONT_ITALIC, FONT_LABEL, FONT_HEADING,
    MARGIN_BOTTOM, MARGIN_H, PAGE_W,
    SIZE_BODY, SIZE_SECTION, SIZE_TABLE, SIZE_TABLE_HDR,
    _BOLD, _BODY, _ITALIC, _LABEL, _RIGHT, _RIGHT_BOLD, _SECTION_STYLE,
    _p,
    build_banking_box,
    build_info_grid,
    build_items_table,
    build_party_grid,
    draw_footer,
    draw_page_header,
    draw_watermark,
    section_label,
)
from pdf.utils import currency_to_words, format_decimal, safe_str, strip_html


# ---- Internal helpers --------------------------------------------------------

def _org_address_lines(org):
    """Return a list of address strings for an Organisation's primary address."""
    if not org:
        return []
    addr = org.addresses.first()
    if not addr:
        return [org.name]
    lines = []
    if addr.line1:
        lines.append(addr.line1)
    if addr.line2:
        lines.append(addr.line2)
    city_state = ', '.join(filter(None, [addr.city, addr.state]))
    if city_state:
        pin = f' – {addr.pin}' if addr.pin else ''
        lines.append(f'{city_state}{pin}')
    if addr.country:
        lines.append(addr.country.name)
    contact = ', '.join(filter(None, [addr.email, addr.phone_number]))
    if contact:
        lines.append(contact)
    return lines


def _fmt(value, dp=2):
    """Shorthand: format Decimal as comma-separated string."""
    return format_decimal(value, dp=dp)


def _date(d):
    """Format a date as '17 Mar 2026', or '—' if None."""
    if d is None:
        return '—'
    try:
        return d.strftime('%-d %b %Y')
    except ValueError:
        return d.strftime('%d %b %Y')


# ---- Page callback builder ---------------------------------------------------

def _make_page_callback(pi, is_draft):
    """Return an onPage callable that draws header, optional watermark, and footer."""
    exporter = pi.exporter
    exporter_addr = _org_address_lines(exporter) if exporter else []
    iec = getattr(exporter, 'iec_code', None) if exporter else None

    def on_page(canvas, doc):
        draw_page_header(
            canvas,
            exporter_name=exporter.name if exporter else '',
            exporter_addr_lines=exporter_addr,
            doc_title_lines=['PROFORMA INVOICE', 'CUM SALES CONTRACT'],
            doc_number=pi.pi_number,
            doc_date=_date(pi.pi_date),
            iec_code=iec,
        )
        if is_draft:
            draw_watermark(canvas)
        draw_footer(canvas, pi.pi_number)

    return on_page


# ---- Section builders --------------------------------------------------------

def _build_reference_grid(pi):
    """4-cell grid: Buyer Order No / Buyer Order Date / PO No / Other Refs."""
    cells = [
        ('Buyer Order No.',  safe_str(pi.buyer_order_no)),
        ('Buyer Order Date', _date(pi.buyer_order_date)),
        ('Other References', safe_str(pi.other_references)),
        ('PI Date',          _date(pi.pi_date)),
    ]
    return build_info_grid(cells, cols=4)


def _build_parties(pi):
    """Consignee + Buyer party boxes."""
    parties = [
        ('Consignee', pi.consignee.name if pi.consignee else '—',
         _org_address_lines(pi.consignee)),
    ]
    if pi.buyer:
        parties.append(
            ('Buyer (if other than Consignee)', pi.buyer.name,
             _org_address_lines(pi.buyer))
        )
    return build_party_grid(parties)


def _build_shipping_grid(pi):
    """8-cell grid covering origin, routing, and trade terms."""
    def _name(obj):
        return obj.name if obj else '—'

    incoterms_str = '—'
    if pi.incoterms:
        code = pi.incoterms.code or ''
        full = pi.incoterms.full_name or ''
        incoterms_str = f'{code} – {full}' if full else code

    cells = [
        ('Country of Origin',         _name(pi.country_of_origin)),
        ('Country of Destination',    _name(pi.country_of_final_destination)),
        ('Pre-Carriage By',           _name(pi.pre_carriage_by)),
        ('Place of Receipt',          safe_str(pi.place_of_receipt)),
        ('Port of Loading',           safe_str(pi.port_of_loading)),
        ('Port of Discharge',         safe_str(pi.port_of_discharge)),
        ('Incoterms',                 incoterms_str),
        ('Payment Terms',             _name(pi.payment_terms)),
    ]
    return build_info_grid(cells, cols=4)


def _build_line_items(pi):
    """Styled line items table. Returns (table, line_total)."""
    items = list(pi.line_items.select_related('uom').all())
    line_total = Decimal('0.00')

    headers = ['#', 'HSN Code', 'Item Code', 'Description',
               'Qty', 'UOM', 'Rate (USD)', 'Amount (USD)']

    # Column widths per skill layout spec (pt), total ≈ CONTENT_W
    col_widths = [18, 55, 55, 130, 55, 40, 60, 65]
    # Distribute any remaining width into Description column
    col_widths[3] += CONTENT_W - sum(col_widths)

    rows = []
    for idx, item in enumerate(items, start=1):
        uom = item.uom.abbreviation if item.uom else ''
        rows.append([
            _p(str(idx)),
            _p(safe_str(item.hsn_code)),
            _p(safe_str(item.item_code)),
            _p(safe_str(item.description)),
            _p(_fmt(item.quantity, dp=3), _RIGHT),
            _p(uom),
            _p(_fmt(item.rate_usd), _RIGHT),
            _p(_fmt(item.amount_usd), _RIGHT),
        ])
        line_total += item.amount_usd or Decimal('0.00')

    tbl = build_items_table(headers, rows, col_widths, right_cols=[4, 6, 7])
    return tbl, line_total


def _build_totals(pi, line_total):
    """
    Right-aligned totals block with Sub Total, Grand Total, Cost Breakdown,
    and Invoice Total (Amount Payable) — all conditional as per FR-09.7.
    Returns (totals_table, invoice_total).
    """
    charges = list(pi.charges.all())
    charges_total = sum((c.amount_usd for c in charges), Decimal('0.00'))
    grand_total = line_total + charges_total

    incoterm_code = pi.incoterms.code if pi.incoterms else None
    seller_fields = INCOTERM_SELLER_FIELDS.get(incoterm_code, set())

    # Cost breakdown is skipped for EXW (no seller costs) and FCA/FOB (buyer
    # bears freight; showing FOB Value = Grand Total adds no information).
    shows_cost_breakdown = (
        incoterm_code
        and incoterm_code not in ('EXW',)
        and incoterm_code not in FOB_ONLY_INCOTERMS
        and bool(seller_fields)
    )

    invoice_total = grand_total

    W_LABEL = CONTENT_W * 0.70
    W_VALUE = CONTENT_W * 0.30

    # Style helpers for totals rows
    _tl = ParagraphStyle('tot_label', fontName=FONT_BODY, fontSize=SIZE_TABLE,
                         leading=11, textColor=COLOR_TEXT_MUTED)
    _tv = ParagraphStyle('tot_val', fontName=FONT_LABEL, fontSize=SIZE_TABLE,
                         leading=11, textColor=COLOR_TEXT_MUTED)
    _tbl_b = ParagraphStyle('tot_bold', fontName=FONT_LABEL, fontSize=SIZE_TABLE,
                            leading=11)
    _tbv_b = ParagraphStyle('tot_val_bold', fontName=FONT_LABEL, fontSize=SIZE_TABLE,
                            leading=11)
    _tbl_hdr = ParagraphStyle('tot_hdr', fontName=FONT_LABEL, fontSize=SIZE_SECTION,
                              leading=9, textColor=COLOR_WHITE)
    _tbl_inv = ParagraphStyle('tot_inv', fontName=FONT_HEADING, fontSize=SIZE_BODY,
                              leading=12, textColor=COLOR_WHITE)

    rows = []
    cmds = [
        ('GRID',          (0, 0), (-1, -1), 0, COLOR_BORDER),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN',         (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]

    def _row(label, value, label_style=None, value_style=None):
        return [_p(label, label_style or _tl), _p(value, value_style or _tv)]

    # "Amount Chargeable in: USD" header row
    rows.append([_p('Amount Chargeable in: USD', _tbl_b), _p('')])
    cmds.append(('SPAN', (0, 0), (1, 0)))
    cmds.append(('LINEBELOW', (0, 0), (1, 0), 0.5, COLOR_BORDER))

    # Sub Total (only when additional charges exist)
    if charges:
        rows.append(_row('Sub Total', f'USD {_fmt(line_total)}'))
        for charge in charges:
            rows.append(_row(charge.description, _fmt(charge.amount_usd)))

    # Grand Total (always shown)
    grand_row_idx = len(rows)
    rows.append([_p('Grand Total Amount', _tbl_b), _p(f'USD {_fmt(grand_total)}', _tbv_b)])
    cmds.append(('BACKGROUND', (0, grand_row_idx), (-1, grand_row_idx), COLOR_LIGHT_BG))
    cmds.append(('LINEABOVE',  (0, grand_row_idx), (-1, grand_row_idx), 0.5, COLOR_BORDER))

    # Cost Breakdown
    if shows_cost_breakdown:
        breakdown_row_idx = len(rows)
        rows.append([_p(f'COST BREAKDOWN ({incoterm_code})', _tbl_hdr), _p('')])
        cmds.append(('SPAN',       (0, breakdown_row_idx), (1, breakdown_row_idx)))
        cmds.append(('BACKGROUND', (0, breakdown_row_idx), (-1, breakdown_row_idx), COLOR_NAVY))

        rows.append(_row('FOB Value', _fmt(grand_total)))

        for field, label, key in [
            ('freight',             'Freight',                    'freight'),
            ('insurance_amount',    'Insurance Amount',           'insurance_amount'),
            ('import_duty',         'Import Duty / Taxes',        'import_duty'),
            ('destination_charges', 'Destination Charges',        'destination_charges'),
        ]:
            if field in seller_fields:
                val = getattr(pi, key, None) or Decimal('0.00')
                suffix = ' (All-risk coverage)' if field == 'insurance_amount' and incoterm_code == 'CIP' else ''
                rows.append(_row(f'{label}{suffix}', _fmt(val)))
                invoice_total += val

        # Invoice Total (Amount Payable) — only when it exceeds Grand Total
        if invoice_total > grand_total:
            inv_row_idx = len(rows)
            rows.append([
                _p('Invoice Total (Amount Payable)', _tbl_inv),
                _p(f'USD {_fmt(invoice_total)}', _tbl_inv),
            ])
            cmds.append(('BACKGROUND', (0, inv_row_idx), (-1, inv_row_idx), COLOR_NAVY))

    tbl = Table(rows, colWidths=[W_LABEL, W_VALUE])
    tbl.setStyle(TableStyle(cmds))
    return tbl, invoice_total


def _build_validity_grid(pi):
    """4-cell grid: validity, shipment, partial shipment, transshipment."""
    def _choice(val):
        return val.replace('_', ' ').title() if val else '—'

    cells = [
        ('Validity for Acceptance', _date(pi.validity_for_acceptance)),
        ('Validity for Shipment',   _date(pi.validity_for_shipment)),
        ('Partial Shipment',        _choice(pi.partial_shipment)),
        ('Transshipment',           _choice(pi.transshipment)),
    ]
    return build_info_grid(cells, cols=4)


def _build_amount_words_box(amount):
    """Italic paragraph with blue left accent, showing amount in words."""
    text = f'<b>Amount in Words:</b> <i>{currency_to_words(amount)}</i>'
    p = _p(text, ParagraphStyle(
        'amt_words', fontName=FONT_BODY, fontSize=SIZE_TABLE, leading=12,
        textColor=COLOR_NAVY,
    ))
    tbl = Table([[p]], colWidths=[CONTENT_W])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ('LEFTBORDER',    (0, 0), (-1, -1), 3, COLOR_BLUE_ACCENT),
        ('LINEBEFORE',    (0, 0), (0, -1),  3, COLOR_BLUE_ACCENT),
        ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return tbl


# ---- Main generator ----------------------------------------------------------

def generate_pi_pdf(pi) -> io.BytesIO:
    """
    Generate a Proforma Invoice PDF and return an in-memory BytesIO buffer.
    Constraint #20: never writes to disk.
    """
    from apps.workflow.constants import APPROVED

    is_draft = pi.status != APPROVED
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=(PAGE_W, __import__('reportlab').lib.pagesizes.A4[1]),
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=DOC_TOP_MARGIN,
        bottomMargin=MARGIN_BOTTOM,
    )

    on_page = _make_page_callback(pi, is_draft)
    story = []

    # 1. Reference numbers grid -----------------------------------------------
    story.append(section_label('Reference Numbers'))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_reference_grid(pi))
    story.append(Spacer(1, 3 * mm))

    # 2. Parties ---------------------------------------------------------------
    story.append(section_label('Parties'))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_parties(pi))
    story.append(Spacer(1, 3 * mm))

    # 3. Shipping & logistics --------------------------------------------------
    story.append(section_label('Shipping & Logistics'))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_shipping_grid(pi))
    story.append(Spacer(1, 3 * mm))

    # 4. Goods description (line items) ----------------------------------------
    story.append(section_label('Goods Description'))
    story.append(Spacer(1, 2 * mm))
    li_table, line_total = _build_line_items(pi)
    story.append(li_table)
    story.append(Spacer(1, 3 * mm))

    # 5. Totals block ----------------------------------------------------------
    totals_tbl, invoice_total = _build_totals(pi, line_total)
    story.append(totals_tbl)
    story.append(Spacer(1, 3 * mm))

    # 6. Amount in words -------------------------------------------------------
    story.append(_build_amount_words_box(invoice_total))
    story.append(Spacer(1, 3 * mm))

    # 7. Validity & terms grid -------------------------------------------------
    story.append(section_label('Terms'))
    story.append(Spacer(1, 2 * mm))
    story.append(_build_validity_grid(pi))
    story.append(Spacer(1, 3 * mm))

    # 8. MT103 payment instruction + declaration -------------------------------
    notice_style = ParagraphStyle(
        'notice', fontName=FONT_BODY, fontSize=SIZE_TABLE - 0.5,
        leading=11, textColor=COLOR_TEXT_MUTED,
    )
    story.append(_p(
        'Request your bank to send MT 103 Message to our bank and send us a copy '
        'of this message to trace &amp; claim the payment from our bank.',
        notice_style,
    ))
    story.append(Spacer(1, 2 * mm))
    story.append(_p(
        'We declare that this invoice shows the actual price of the goods described '
        'and that all particulars are true and correct.',
        notice_style,
    ))
    story.append(Spacer(1, 3 * mm))

    # 9. Banking details -------------------------------------------------------
    if pi.bank:
        story.append(section_label('Beneficiary Bank Details'))
        story.append(Spacer(1, 2 * mm))
        story.append(build_banking_box(pi.bank))
        story.append(Spacer(1, 3 * mm))

    # 10. Terms & Conditions (new page) ----------------------------------------
    if pi.tc_content:
        story.append(PageBreak())
        story.append(section_label('Terms & Conditions'))
        story.append(Spacer(1, 3 * mm))
        tc_style = ParagraphStyle(
            'tc', fontName=FONT_BODY, fontSize=SIZE_TABLE - 0.5,
            leading=13, textColor='#3A3A5C',
        )
        # strip_html converts Tiptap HTML to plain paragraphs
        for paragraph in strip_html(pi.tc_content).split('\n\n'):
            if paragraph.strip():
                story.append(_p(paragraph.strip(), tc_style))
                story.append(Spacer(1, 2 * mm))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    return buffer
