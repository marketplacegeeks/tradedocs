"""
Shared design-system constants and drawing utilities for all TradeDocs PDF generators.

Import colours, fonts, and helpers from here — never hardcode them in individual
generators.  All canvas-drawing helpers receive a ReportLab Canvas instance.
"""
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Table, TableStyle

# ---- Colour palette (Black & White Professional) -----------------------------
COLOR_NAVY        = HexColor('#000000')   # Pure black for headers
COLOR_BLUE_ACCENT = HexColor('#000000')   # Black accent bars
COLOR_LIGHT_BG    = HexColor('#E8E8E8')   # Light gray backgrounds
COLOR_BORDER      = HexColor('#000000')   # Black borders
COLOR_TEXT_DARK   = HexColor('#000000')   # Black text
COLOR_TEXT_MUTED  = HexColor('#4A4A4A')   # Dark gray for labels
COLOR_DRAFT_RED   = HexColor('#000000')   # Black watermark (alpha 0.05)
COLOR_WHITE       = white

# ---- Fonts (ReportLab built-ins — no external files required) ----------------
FONT_HEADING = 'Times-Bold'       # company name, document title
FONT_LABEL   = 'Helvetica-Bold'   # section labels, table headers
FONT_BODY    = 'Helvetica'        # body text, data cells
FONT_ITALIC  = 'Helvetica-Oblique'
FONT_MONO    = 'Courier'          # batch numbers, reference codes

# ---- Type sizes (pt) ---------------------------------------------------------
SIZE_COMPANY   = 18
SIZE_DOC_TITLE = 13
SIZE_SECTION   =  9
SIZE_BODY      =  9
SIZE_SMALL     =  8
SIZE_TABLE     =  9
SIZE_TABLE_HDR =  9

# ---- Page geometry -----------------------------------------------------------
PAGE_W, PAGE_H = A4
MARGIN_H       = 15 * mm    # left / right margin
MARGIN_TOP     = 15 * mm    # gap between paper edge and header top
MARGIN_BOTTOM  = 20 * mm    # gap between paper edge and footer bottom
CONTENT_W      = PAGE_W - 2 * MARGIN_H
HEADER_H       = 30 * mm    # height of the canvas-drawn page header

# Platypus SimpleDocTemplate topMargin must clear the physical margin + header.
DOC_TOP_MARGIN = MARGIN_TOP + HEADER_H


# ---- Paragraph style helpers -------------------------------------------------

_BODY = ParagraphStyle(
    'td_body', fontName=FONT_BODY, fontSize=SIZE_TABLE,
    leading=12, textColor=COLOR_TEXT_DARK,
)
_BOLD = ParagraphStyle(
    'td_bold', fontName=FONT_LABEL, fontSize=SIZE_TABLE,
    leading=12, textColor=COLOR_TEXT_DARK,
)
_LABEL = ParagraphStyle(
    'td_label', fontName=FONT_BODY, fontSize=SIZE_SECTION,
    leading=11, textColor=COLOR_TEXT_MUTED,
)
_RIGHT = ParagraphStyle(
    'td_right', fontName=FONT_BODY, fontSize=SIZE_TABLE,
    leading=12, alignment=TA_RIGHT, textColor=COLOR_TEXT_DARK,
)
_RIGHT_BOLD = ParagraphStyle(
    'td_right_bold', fontName=FONT_LABEL, fontSize=SIZE_TABLE,
    leading=12, alignment=TA_RIGHT, textColor=COLOR_TEXT_DARK,
)
_ITALIC = ParagraphStyle(
    'td_italic', fontName=FONT_ITALIC, fontSize=SIZE_TABLE,
    leading=12, textColor=COLOR_TEXT_DARK,
)
_SECTION_STYLE = ParagraphStyle(
    'td_section', fontName=FONT_LABEL, fontSize=SIZE_SECTION,
    leading=11, textColor=COLOR_TEXT_MUTED, spaceBefore=8, spaceAfter=2,
)
_HDR_WHITE = ParagraphStyle(
    'td_hdr_white', fontName=FONT_LABEL, fontSize=SIZE_TABLE_HDR,
    leading=11, textColor=COLOR_TEXT_DARK,
)
_NAVY_WHITE = ParagraphStyle(
    'td_navy_white', fontName=FONT_LABEL, fontSize=SIZE_SECTION,
    leading=11, textColor=COLOR_TEXT_DARK,
)


def _p(text, style=None):
    """Create a Paragraph; coerce None/empty to a safe empty string."""
    return Paragraph(str(text or ''), style or _BODY)


def section_label(text):
    """Return a Paragraph styled as a section label (ALL CAPS, muted)."""
    return _p(text.upper(), _SECTION_STYLE)


# ---- Canvas drawing helpers --------------------------------------------------

def draw_watermark(canvas):
    """Faint diagonal 'DRAFT' watermark. Call for all non-APPROVED documents."""
    canvas.saveState()
    canvas.setFont(FONT_HEADING, 80)
    canvas.setFillColor(COLOR_DRAFT_RED, alpha=0.05)
    canvas.translate(PAGE_W / 2, PAGE_H / 2)
    canvas.rotate(35)
    canvas.drawCentredString(0, 0, 'DRAFT')
    canvas.restoreState()


def draw_footer(canvas, doc_number):
    """Hairline rule + document reference (center) + page number (center bottom)."""
    canvas.saveState()
    y_rule = MARGIN_BOTTOM - 5 * mm
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_H, y_rule + 8, PAGE_W - MARGIN_H, y_rule + 8)

    canvas.setFont(FONT_BODY, 8)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    canvas.drawCentredString(
        PAGE_W / 2, y_rule + 3,
        'This is a computer generated document and does not require signature',
    )

    canvas.setFont(FONT_BODY, 7)
    canvas.drawCentredString(
        PAGE_W / 2, y_rule - 3,
        f'Page {canvas.getPageNumber()}',
    )
    canvas.restoreState()


def draw_page_header(canvas, exporter_name, exporter_addr_lines,
                     doc_title_lines, doc_number, doc_date, iec_code=None):
    """
    Canvas-drawn page header: centered company info + document title.
    Called from page callbacks so it appears on every page.
    """
    canvas.saveState()

    y_top    = PAGE_H - MARGIN_TOP          # top of header area
    y_bottom = y_top - HEADER_H             # bottom of header area (where hairline sits)
    x_center = PAGE_W / 2

    # --- Company name (centered, bold) ----------------------------------------
    canvas.setFont(FONT_HEADING, SIZE_COMPANY)
    canvas.setFillColor(COLOR_TEXT_DARK)
    y_cursor = y_top - SIZE_COMPANY - 2
    canvas.drawCentredString(x_center, y_cursor, exporter_name or '')

    # --- IEC code (if present) ------------------------------------------------
    if iec_code:
        y_cursor -= 11
        canvas.setFont(FONT_BODY, SIZE_SMALL)
        canvas.setFillColor(COLOR_TEXT_MUTED)
        canvas.drawCentredString(x_center, y_cursor, f'IEC: {iec_code}')

    # --- Address lines (centered, smaller font) ------------------------------
    canvas.setFont(FONT_BODY, SIZE_SMALL)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    for line in (exporter_addr_lines or [])[:3]:  # Limit to 3 lines for space
        y_cursor -= 10
        canvas.drawCentredString(x_center, y_cursor, line)

    # --- Horizontal separator line --------------------------------------------
    y_cursor -= 8
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN_H, y_cursor, PAGE_W - MARGIN_H, y_cursor)

    # --- Document title (centered, bold) --------------------------------------
    y_cursor -= 6
    canvas.setFont(FONT_HEADING, SIZE_DOC_TITLE)
    canvas.setFillColor(COLOR_TEXT_DARK)
    for title_line in (doc_title_lines or []):
        y_cursor -= SIZE_DOC_TITLE + 2
        canvas.drawCentredString(x_center, y_cursor, title_line.upper())

    # --- Doc number + date (centered, smaller) --------------------------------
    canvas.setFont(FONT_BODY, SIZE_SMALL)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    y_cursor -= 12
    canvas.drawCentredString(x_center, y_cursor, f'No: {doc_number}')
    if doc_date:
        y_cursor -= 10
        canvas.drawCentredString(x_center, y_cursor, f'Date: {doc_date}')

    canvas.restoreState()


# ---- Platypus table builders -------------------------------------------------

def build_items_table(headers, rows, col_widths, right_cols=None):
    """
    Styled line-items table.
    headers   : list[str]
    rows      : list[list[Paragraph | str]]  — each inner list is one data row
    col_widths: list[float]  (pt)
    right_cols: list[int]    — 0-based column indices to right-align
    """
    right_cols = set(right_cols or [])
    header_row = [_p(h, _HDR_WHITE) for h in headers]
    all_rows = [header_row] + rows

    cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1.2, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('FONTNAME', (0, 0), (-1, -1), FONT_BODY),
        ('FONTSIZE', (0, 0), (-1, -1), SIZE_TABLE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (0, 0), 6),
        ('BOTTOMPADDING', (0, 0), (0, 0), 6),
        ('TOPPADDING',    (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]

    for c in right_cols:
        cmds.append(('ALIGN', (c, 1), (c, -1), 'RIGHT'))

    tbl = Table(all_rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(cmds))
    return tbl


def build_info_grid(cells, cols=4):
    """
    Grid of labelled info boxes (shipping details, reference numbers, etc.).
    cells: list of (label, value) tuples.  Padded to fill complete rows.
    """
    cell_w = CONTENT_W / cols
    pad_count = (-len(cells)) % cols
    cells = list(cells) + [('', '')] * pad_count

    def _cell(label, value):
        content = Table(
            [[_p(label.upper(), _LABEL)], [_p(value or '—', _BOLD)]],
            colWidths=[cell_w - 14],
        )
        content.setStyle(TableStyle([
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        outer = Table([[content]], colWidths=[cell_w])
        outer.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), COLOR_LIGHT_BG),
            ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('LEFTPADDING',   (0, 0), (-1, -1), 7),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        return outer

    rows = []
    for i in range(0, len(cells), cols):
        rows.append([_cell(lbl, val) for lbl, val in cells[i:i + cols]])

    grid = Table(rows, colWidths=[cell_w] * cols)
    grid.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return grid


def build_party_grid(parties, gap=6):
    """
    Row of party boxes (Consignee, Buyer, Notify Party, etc.).
    parties: list of (label, name, [detail_line, ...]) tuples.
    All boxes share equal width across CONTENT_W.
    """
    n = len(parties)
    box_w = (CONTENT_W - gap * (n - 1)) / n

    def _box(label, name, detail_lines):
        content_rows = [[_p(label.upper(), _LABEL)], [_p(name or '—', _BOLD)]]
        for line in (detail_lines or []):
            if line:
                content_rows.append([_p(line, _BODY)])
        inner = Table(content_rows, colWidths=[box_w - 18])
        inner.setStyle(TableStyle([
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        outer = Table([[inner]], colWidths=[box_w])
        outer.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), COLOR_LIGHT_BG),
            ('BOX',           (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('LEFTPADDING',   (0, 0), (-1, -1), 9),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 9),
            ('TOPPADDING',    (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        return outer

    boxes = [_box(lbl, name, lines) for lbl, name, lines in parties]
    col_widths = []
    for i, _ in enumerate(boxes):
        col_widths.append(box_w)
        if i < n - 1:
            col_widths.append(gap)

    row = []
    for i, box in enumerate(boxes):
        row.append(box)
        if i < n - 1:
            row.append('')

    tbl = Table([row], colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return tbl


def build_banking_box(bank):
    """
    Returns a Table styled as the banking details box.
    Black border with light gray background.
    Returns None if bank is None.
    """
    if not bank:
        return None

    pairs = [
        ('Beneficiary Name', bank.beneficiary_name),
        ('Bank Name',        bank.bank_name),
        ('Branch',           bank.branch_name),
        ('Branch Address',   bank.branch_address or '—'),
        ('Account No.',      bank.account_number),
        ('IFSC / Routing',   bank.routing_number or '—'),
        ('SWIFT Code',       bank.swift_code or '—'),
    ]
    if bank.iban:
        pairs.append(('IBAN', bank.iban))
    if bank.intermediary_bank_name:
        ccy = bank.intermediary_currency.code if bank.intermediary_currency else ''
        pairs.extend([
            (f'Intermediary Institution ({ccy})', ''),
            ('  A/C No.',   bank.intermediary_account_number or '—'),
            ('  Bank',      bank.intermediary_bank_name),
            ('  SWIFT',     bank.intermediary_swift_code or '—'),
        ])

    LABEL_W = CONTENT_W * 0.35
    VALUE_W = CONTENT_W - LABEL_W

    title_row = [_p('BENEFICIARY BANK INFORMATION', _NAVY_WHITE), '']
    data_rows = [[_p(lbl, _LABEL), _p(str(val or '—'), _BODY)] for lbl, val in pairs]
    all_rows = [title_row] + data_rows

    tbl = Table(all_rows, colWidths=[LABEL_W, VALUE_W])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (1, 0),  COLOR_LIGHT_BG),
        ('BACKGROUND',    (0, 1), (1, -1), COLOR_LIGHT_BG),
        ('BOX',           (0, 0), (-1, -1), 1.2, COLOR_BORDER),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('SPAN',          (0, 0), (1, 0)),
    ]))
    return tbl
