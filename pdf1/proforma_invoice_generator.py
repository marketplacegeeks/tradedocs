"""
PDF Generation for Proforma Invoices using ReportLab

This module generates professional PDF invoices with complex table layouts.
Key concepts:
- ReportLab uses a coordinate system where (0,0) is bottom-left
- Tables use (column, row) notation, starting from (0,0) at top-left
- Measurements use millimeters (mm) for easy real-world sizing
"""

import re
from io import BytesIO
from typing import Any
from reportlab.lib.pagesizes import A4  # Standard A4 page size (210mm x 297mm)
from reportlab.lib import colors  # Color definitions (colors.black, colors.white, etc.)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # Text styling
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak  # Layout elements
from reportlab.lib.units import mm  # Millimeter unit for measurements (1mm = 2.834645669 points)
from reportlab.lib.enums import TA_CENTER
from num2words import num2words


# ============================================================================
# UTILITY FUNCTIONS - Data Formatting Helpers
# ============================================================================

def safe(v: Any, default: str = "") -> str:
    """Safely convert any value to string, returning empty string if None"""
    return "" if v is None else str(v)


def bool_yn(v: Any) -> str:
    """Convert boolean values to 'Yes' or 'No' strings"""
    try:
        return "Yes" if bool(v) else "No"
    except Exception:
        return "No"


def fmt_money(v: Any) -> str:
    """Format monetary values with comma separators and 2 decimal places
    Example: 1234.56 -> "1,234.56"
    """
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return safe(v)


def fmt_qty(v: Any) -> str:
    """Format quantity values with comma separators and 3 decimal places
    Example: 1234.567 -> "1,234.567"
    """
    try:
        return f"{float(v):,.3f}"
    except Exception:
        return safe(v)


def amount_to_words(n: Any, currency: str = "Dollars") -> str:
    """Convert numeric amount to written words in the specified format.
    Example: 1518355239 -> "One Billion Five Hundred Eighteen Million Three Hundred Fifty-Five Thousand Two Hundred Thirty-Nine Dollars Only"
    """
    try:
        # The currency name is taken from the proforma invoice model
        n = int(float(n or 0))
        # Convert the number to words, capitalize the first letter of each word
        words = num2words(n).title()
        # Append the currency name and "Only"
        return f"{words} {currency} Only"
    except Exception:
        return ""


# ============================================================================
# MAIN PDF GENERATION FUNCTION
# ============================================================================

def generate_proforma_invoice_pdf_bytes(invoice) -> bytes:
    """
    Build Proforma Invoice PDF bytes matching the exact layout of the reference PDF.

    This function creates a complex multi-page PDF with tables, paragraphs, and styling.
    The PDF is built using ReportLab's "story" concept - elements are added sequentially
    and ReportLab handles page breaks and layout automatically.
    """

    # Create an in-memory buffer to store the PDF bytes
    buffer = BytesIO()

    # SimpleDocTemplate handles page layout and flow
    # All margins are in millimeters (mm) for easy measurement
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,  # A4 = 210mm x 297mm
        leftMargin=15*mm,    # 15mm from left edge
        rightMargin=15*mm,   # 15mm from right edge
        topMargin=10*mm,     # 10mm from top edge
        bottomMargin=15*mm   # 15mm from bottom edge
    )

    # Get base stylesheet (provides default styles like "Normal", "Heading1", etc.)
    styles = getSampleStyleSheet()

    # ========================================================================
    # CUSTOM PARAGRAPH STYLES
    # ========================================================================
    # ParagraphStyle controls how text looks inside Paragraph elements
    # Key parameters:
    #   - fontSize: Text size in points
    #   - leading: Line height (space between lines) in points
    #   - spaceAfter: Space after paragraph in points
    #   - alignment: TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    #   - fontName: Font family (Helvetica, Helvetica-Bold, Times-Roman, etc.)

    style_company_header = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Normal"],  # Inherit from base "Normal" style
        fontSize=16,              # Large text for company name
        leading=20,               # Line height (usually 1.2-1.5x fontSize)
        spaceAfter=6,             # Space after this paragraph
        alignment=TA_CENTER,      # Center-aligned text
        fontName="Helvetica-Bold" # Bold font
    )

    style_title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=12,
        leading=15,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold"
    )

    style_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,              # Smaller font for labels
        leading=11,
        fontName="Helvetica-Bold"
    )

    style_text = ParagraphStyle(
        "Text",
        parent=styles["Normal"],
        fontSize=9,              # Body text size
        leading=11
    )

    style_small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,              # Extra small for footer text
        leading=10
    )

    # ========================================================================
    # FOOTER FUNCTION
    # ========================================================================
    # This function is called for each page to add footer text
    def add_footer(canvas, doc):
        """Add centered footer text to each page"""
        canvas.saveState()
        # Calculate center position
        page_width = A4[0]
        footer_text = "This is a computer-generated document. Signature is not required."
        # Draw text centered at bottom (10mm from bottom)
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(page_width / 2, 10*mm, footer_text)
        canvas.restoreState()

    # ========================================================================
    # BUILD THE STORY (PDF Content)
    # ========================================================================
    # The "story" is a list of elements that will be rendered in order.
    # ReportLab flows these elements onto pages, handling page breaks automatically.
    story = []

    # ========================================================================
    # DATA EXTRACTION from Invoice Model
    # ========================================================================
    # Extract related objects and format data for display
    # Using safe() and getattr() to handle None values gracefully

    exp = invoice.exporter           # Company doing the exporting
    cons = invoice.consignee         # Company receiving the goods
    fd = invoice.final_destination   # Final destination location

    # Extract nested attributes safely (object -> country -> name)
    origin_country = safe(getattr(getattr(exp, 'country', None), 'name', None))
    final_country = safe(getattr(getattr(fd, 'country', None), 'name', None))

    # Format Consignee details
    cons_name = safe(getattr(cons, 'name', ''))
    cons_address = safe(getattr(cons, 'address', ''))
    cons_country = safe(getattr(getattr(cons, 'country', None), 'name', ''))
    cons_email = safe(getattr(cons, 'email_id', ''))
    
    address_parts = []
    if cons_address:
        address_parts.append(cons_address)
    if cons_country:
        address_parts.append(cons_country)
    
    address_line = ", ".join(address_parts)

    cons_lines = [
        cons_name,
        address_line,
        cons_email
    ]
    cons_lines = [line for line in cons_lines if line]
    consignee_details_html = "<br/>".join(cons_lines)

    # Get related field names
    incoterm_disp = safe(getattr(invoice.incoterm, "code", ""))
    payment_term_name = safe(getattr(getattr(invoice, "payment_term", None), "name", None))

    # Port and carriage information
    port_loading = safe(getattr(getattr(invoice, "port_loading", None), "name", None))
    port_discharge = safe(getattr(getattr(invoice, "port_discharge", None), "name", None))
    final_dest = safe(getattr(getattr(invoice, "final_destination", None), "name", None))
    pre_carriage = safe(getattr(getattr(invoice, "pre_carriage", None), "name", None))
    por_pre = safe(getattr(getattr(invoice, "place_of_receipt_by_pre_carrier", None), "name", None))

    bank = invoice.bank  # Bank details for payment

    # ========================================================================
    # DOCUMENT HEADER
    # ========================================================================

    # Add company name at the top (centered, large, bold)
    story.append(Paragraph(safe(getattr(exp, "name", "")), style_company_header))

    # Add document title (centered, medium, bold)
    story.append(Paragraph("PROFORMA INVOICE CUM SALES CONTRACT", style_title))

    # Spacer adds vertical space (width=1 means full width, height in points)
    story.append(Spacer(1, 8))

    # ========================================================================
    # MAIN INFORMATION TABLE
    # ========================================================================
    # This is the most complex table with multiple merged cells.
    #
    # TABLE STRUCTURE BASICS:
    # ----------------------
    # A table is defined as a 2D list: [ [row0_col0, row0_col1, ...], [row1_col0, row1_col1, ...], ... ]
    # Each inner list is a ROW, each element in the row is a COLUMN
    #
    # COORDINATE SYSTEM:
    # -----------------
    # Tables use (column, row) coordinates starting from (0, 0) at the TOP-LEFT
    # Example for a 4x3 table:
    #
    #        Col0     Col1     Col2     Col3
    # Row0:  (0,0)    (1,0)    (2,0)    (3,0)
    # Row1:  (0,1)    (1,1)    (2,1)    (3,1)
    # Row2:  (0,2)    (1,2)    (2,2)    (3,2)
    #
    # CELL SPANNING (MERGING):
    # ------------------------
    # SPAN takes two coordinates: (start_col, start_row), (end_col, end_row)
    # The end coordinates are INCLUSIVE (the cell itself is included)
    #
    # Example: ('SPAN', (0, 0), (0, 2)) means:
    #   - Start at column 0, row 0
    #   - End at column 0, row 2
    #   - This merges cells vertically: (0,0), (0,1), (0,2) into ONE cell
    #
    # Example: ('SPAN', (1, 3), (2, 3)) means:
    #   - Start at column 1, row 3
    #   - End at column 2, row 3
    #   - This merges cells horizontally: (1,3), (2,3) into ONE cell
    #
    # EMPTY STRINGS:
    # -------------
    # When a cell will be merged (covered by a SPAN), you still need to include
    # it in the data structure, but use an empty string "" as a placeholder.
    # The SPAN command will cause it to be absorbed by the spanning cell.
    #
    # HTML IN PARAGRAPHS:
    # ------------------
    # Paragraphs support basic HTML tags:
    #   <b>Bold text</b>
    #   <i>Italic text</i>
    #   <br/> or <br> for line breaks
    #   <font color="red">Colored text</font>
    #   <font size="12">Different size</font>
    #
    # ========================================================================

    # Build the table data as a 2D list (9 rows x 4 columns)
    # Each row MUST have exactly 4 elements to match the 4-column structure
    main_info_data = [
        # ----------------------------------------------------------------
        # Row 0: Exporter (cols 0-1) + Invoice info (cols 2-3)
        # ----------------------------------------------------------------
        [
            # Columns 0-1: Exporter name (will span columns 0-1, rows 0-2)
            Paragraph(f"<b>Exporter:</b><br/>{safe(getattr(exp, 'name', ''))}<br/>{safe(getattr(exp, 'address', ''))}, {safe(getattr(exp, 'country', ''))}<br/>{safe(getattr(exp, 'email_id', ''))}", style_text),
            "",  # Placeholder for column 1 (merged with column 0)
            # Columns 2-3: Invoice number and date (will span columns 2-3, row 0)
            Paragraph(f"<b>Proforma Invoice No & Date:</b><br/>{safe(invoice.number)} & {safe(invoice.date)}", style_text),
            ""   # Placeholder for column 3 (merged with column 2)
        ],

        # ----------------------------------------------------------------
        # Row 1: Buyer Order info (cols 2-3)
        # ----------------------------------------------------------------
        [
            # Columns 0-1: Empty because merged with row 0
            "",
            "",
            # Columns 2-3: Buyer order details (will span columns 2-3, row 1)
            Paragraph(f"<b>Buyer Order No and Date:</b><br/>{safe(invoice.buyer_order_no)} & {safe(invoice.buyer_order_date)}", style_text),
            ""   # Placeholder for column 3
        ],

        # ----------------------------------------------------------------
        # Row 2: Other references (cols 2-3)
        # ----------------------------------------------------------------
        [
            # Columns 0-1: Empty because merged with row 0
            "",
            "",
            # Columns 2-3: Other reference information (will span columns 2-3, row 2)
            Paragraph(f"<b>Other reference(s):</b><br/>{safe(invoice.other_references)}", style_text),
            ""   # Placeholder for column 3
        ],

        # ----------------------------------------------------------------
        # Row 3: Consignee (cols 0-1) + Buyer if other (cols 2-3)
        # ----------------------------------------------------------------
        [
            # Columns 0-1: Consignee name (will span columns 0-1, rows 3-5)
            Paragraph(f"<b>Consignee:</b><br/>{consignee_details_html}", style_text),
            "",  # Placeholder for column 1
            # Columns 2-3: Buyer if other than consignee (will span columns 2-3, rows 3-4)
            Paragraph(f"<b>Buyer if other than consignee</b><br/>{safe(getattr(cons, 'name', ''))}", style_text),
            ""   # Placeholder for column 3
        ],

        # ----------------------------------------------------------------
        # Row 4: (Consignee and Buyer continue)
        # ----------------------------------------------------------------
        [
            # Columns 0-3: Empty because merged with row 3
            "",
            "",
            "",
            ""
        ],

        # ----------------------------------------------------------------
        # Row 5: (Consignee continues) + Countries (cols 2-3)
        # ----------------------------------------------------------------
        [
            # Columns 0-1: Empty because merged with row 3
            "",
            "",
            # Column 2: Origin country
            Paragraph(f"<b>Country of Origin of Goods:</b><br/>{origin_country}", style_text),
            # Column 3: Destination country
            Paragraph(f"<b>Country of Final Destination:</b><br/>{final_country}", style_text)
        ],

        # ----------------------------------------------------------------
        # Row 6: Pre-carriage, Place of Receipt, Vessel, Incoterms, Payment Terms
        # ----------------------------------------------------------------
        [
            # Column 0: Pre-carriage info
            Paragraph(f"<b>Pre-Carriaged By:</b><br/>{pre_carriage}", style_text),
            # Column 1: Place of receipt
            Paragraph(f"<b>Place of Receipt<br/>by Pre-Carrier:</b><br/>{por_pre}", style_text),
            # Column 2: Vessel/flight info
            Paragraph(f"<b>Vessel/Flight No:</b><br/>{safe(invoice.vessel_flight_no)}", style_text),
            # Column 3: Incoterms
            Paragraph(f"<b>Incoterms:</b><br/>{incoterm_disp}", style_text),
            # Column 4: Payment terms
            Paragraph(f"<b>Payment terms:</b><br/>{payment_term_name}", style_text)
        ],

        # ----------------------------------------------------------------
        # Row 7: Ports and Marks
        # ----------------------------------------------------------------
        [
            # Column 0: Port of loading
            Paragraph(f"<b>Port of Loading:</b><br/>{port_loading}", style_text),
            # Column 1: Port of discharge
            Paragraph(f"<b>Port of Discharge:</b><br/>{port_discharge}", style_text),
            # Column 2: Final destination
            Paragraph(f"<b>Final Destination:</b><br/>{final_dest}", style_text),
            # Column 3: Marks and container number
            Paragraph(f"<b>Marks & Nos/Container No</b><br/>{safe(invoice.marks_and_nos)}", style_text),
            # Column 4: Package info
            Paragraph(f"<b>No & Kind of Packages</b><br/>{safe(invoice.kind_of_packages)}", style_text)
        ]
    ]

    # ========================================================================
    # CREATE THE TABLE OBJECTS (Split into two tables for different column widths)
    # ========================================================================
    # Table 1 (Rows 0-5): colWidths = [36mm, 36mm, 54mm, 54mm] (4 columns)
    #   - Columns 0-1: 36mm each (80% of original 45mm)
    #   - Columns 2-3: 54mm each (redistributed space from columns 0-1)
    #
    # Table 2 (Rows 6-7): colWidths = [36mm, 36mm, 36mm, 36mm, 36mm] (5 columns)
    #   - All columns: 36mm each (equal widths)
    #   - Total width: 180mm (same as table 1)
    #
    # ========================================================================
    # APPLY TABLE STYLING
    # ========================================================================
    # TableStyle takes a list of style commands
    # Each command is a tuple: (COMMAND, start_coords, end_coords, ...params)
    #
    # COMMON COMMANDS:
    # ---------------
    # GRID: Draw grid lines
    #   Format: ('GRID', (start_col, start_row), (end_col, end_row), line_width, color)
    #   Example: ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    #            -1 means "last column" or "last row"
    #
    # VALIGN: Vertical alignment
    #   Values: 'TOP', 'MIDDLE', 'BOTTOM'
    #
    # ALIGN: Horizontal alignment
    #   Values: 'LEFT', 'CENTER', 'RIGHT'
    #
    # LEFTPADDING, RIGHTPADDING, TOPPADDING, BOTTOMPADDING:
    #   Padding inside cells (in points)
    #
    # BACKGROUND: Cell background color
    #   Format: ('BACKGROUND', (start_col, start_row), (end_col, end_row), color)
    #
    # SPAN: Merge cells (explained above)
    #   Format: ('SPAN', (start_col, start_row), (end_col, end_row))
    #
    # FONTNAME, FONTSIZE, TEXTCOLOR: Text formatting
    #   Usually done via Paragraph styles, but can be applied at table level
    #
    # ========================================================================

    # --------------------------------------------------------------------
    # VISUAL GUIDE TO THE CELL STRUCTURE:
    # --------------------------------------------------------------------
    #
    #     Col 0         Col 1         Col 2                      Col 3
    # ┌─────────────────────────────┬──────────────────────────────────┐
    # │ Exporter:                   │ Proforma Invoice No & Date:      │ Row 0
    # │ Auro                        ├──────────────────────────────────┤
    # │                             │ Buyer Order No and Date:         │ Row 1
    # │                             ├──────────────────────────────────┤
    # │                             │ Other reference(s): Reliance     │ Row 2
    # ├─────────────────────────────┼──────────────────────────────────┤
    # │ Consignee:                  │ Buyer if other than consignee    │ Row 3
    # │ NeXusX                      │ NeXusX                           │
    # │                             │                                  │ Row 4
    # │                             ├──────────────────┬───────────────┤
    # │                             │ Country of       │ Country of    │ Row 5
    # │                             │ Origin of Goods: │ Final Dest:   │
    # │                             │ India            │ USA           │
    # ├──────────────┬──────────────┼──────────────────┼───────────────┼──────────────┐
    # │ Pre-Carriage │ Place of     │ Vessel/Flight No │ Incoterms     │ Payment      │ Row 6
    # │ By: Mazagon  │ Receipt:     │ 3nbf48u          │ Cash not      │ terms        │
    # │              │ Hyderabad    │                  │ accepted      │              │
    # ├──────────────┼──────────────┼──────────────────┼───────────────┼──────────────┤
    # │ Port of      │ Port of      │ Final            │ Marks & Nos/  │ No & Kind of │ Row 7
    # │ Loading      │ Discharge    │ Destination      │ Container No  │ Packages     │
    # │ Visakha...   │ Florida      │ Washington       │ jkn32ed       │ 36 | Nutra.. │
    # └──────────────┴──────────────┴──────────────────┴───────────────┴──────────────┘
    #
    #     Col 0         Col 1         Col 2         Col 3         Col 4
    #
    # --------------------------------------------------------------------

    # First table: Rows 0-5 with adjusted column widths
    main_info_data_top = main_info_data[0:6]  # Rows 0-5
    main_info_table_top = Table(main_info_data_top, colWidths=[36*mm, 36*mm, 54*mm, 54*mm])

    main_info_table_top.setStyle(TableStyle([
        # --------------------------------------------------------------------
        # GLOBAL STYLES (apply to entire table using -1 for "last" row/col)
        # --------------------------------------------------------------------

        # Draw grid lines around all cells (0.5 points thick, black)
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

        # Align cell content to TOP of cells
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

        # Cell padding (space inside cells, in points)
        ('LEFTPADDING', (0, 0), (-1, -1), 4),    # 4 points from left edge
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),   # 4 points from right edge
        ('TOPPADDING', (0, 0), (-1, -1), 3),     # 3 points from top edge
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),  # 3 points from bottom edge

        # --------------------------------------------------------------------
        # CELL SPANNING (MERGING) for Rows 0-5
        # --------------------------------------------------------------------
        # IMPORTANT: When you SPAN cells, the content comes from the TOP-LEFT cell
        #            of the span region. Other cells in the span should be empty strings.

        # Merge Exporter section: Columns 0-1, Rows 0-2 (2 columns x 3 rows block)
        # This creates a large merged cell for the exporter information
        ('SPAN', (0, 0), (1, 2)),
        #        └─────┘  └─────┘
        #        start    end
        #     (col 0,   (col 1,
        #      row 0)    row 2)

        # Merge Proforma Invoice No & Date: Columns 2-3, Row 0 (horizontal merge)
        ('SPAN', (2, 0), (3, 0)),

        # Merge Buyer Order No and Date: Columns 2-3, Row 1 (horizontal merge)
        ('SPAN', (2, 1), (3, 1)),

        # Merge Other reference(s): Columns 2-3, Row 2 (horizontal merge)
        ('SPAN', (2, 2), (3, 2)),

        # Merge Consignee section: Columns 0-1, Rows 3-5 (2 columns x 3 rows block)
        # This creates a large merged cell for the consignee information
        ('SPAN', (0, 3), (1, 5)),

        # Merge Buyer if other than consignee: Columns 2-3, Rows 3-4 (2 columns x 2 rows)
        ('SPAN', (2, 3), (3, 4)),

        # Note: Row 5, Columns 2-3 are separate cells for Country of Origin and Country of Final Destination
    ]))

    # Second table: Rows 6-7 with 5 equal columns
    main_info_data_bottom = main_info_data[6:8]  # Rows 6-7
    main_info_table_bottom = Table(main_info_data_bottom, colWidths=[36*mm, 36*mm, 36*mm, 36*mm, 36*mm])

    main_info_table_bottom.setStyle(TableStyle([
        # --------------------------------------------------------------------
        # GLOBAL STYLES
        # --------------------------------------------------------------------
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),

        # --------------------------------------------------------------------
        # NO CELL SPANNING for Rows 6-7
        # --------------------------------------------------------------------
        # All cells in this table are separate (no merging)
    ]))

    # Add both tables to the story
    story.append(main_info_table_top)
    story.append(main_info_table_bottom)

    # Add vertical space after the table (1 = full width, 10 = 10 points height)
    story.append(Spacer(1, 10))

    # ========================================================================
    # LINE ITEMS TABLE (Product Details)
    # ========================================================================
    # This table has a header row followed by dynamic data rows
    # Each row represents one product/line item in the invoice

    # Create the header row (will be row 0 of the table)
    li_header = [
        Paragraph("<b>Sr.</b>", style_label),               # Serial number
        Paragraph("<b>HSN Code</b>", style_label),          # Harmonized System Nomenclature
        Paragraph("<b>Item Code</b>", style_label),         # Product code
        Paragraph("<b>Description of Goods</b>", style_label),  # Product description
        Paragraph("<b>Qty (MT)</b>", style_label),          # Quantity in metric tons
        Paragraph("<b>Rate (USD/MT)</b>", style_label),     # Price per metric ton
        Paragraph("<b>Amount (USD)</b>", style_label)       # Total amount
    ]

    # Start building rows list with header
    li_rows = [li_header]

    # Query the database for active line items, ordered by creation date
    items_qs = invoice.line_items.filter(is_active=True).order_by("created_at")

    # Loop through each line item and add a row to the table
    idx = 0
    for it in items_qs:
        idx += 1  # Increment serial number
        li_rows.append([
            Paragraph(str(idx), style_text),                          # Serial number
            Paragraph(safe(it.hs_code), style_text),                  # HSN code
            Paragraph(safe(it.item_code), style_text),                # Item code
            Paragraph(safe(it.description), style_text),              # Description
            Paragraph(fmt_qty(it.quantity), style_text),              # Quantity (formatted)
            Paragraph(fmt_money(it.unit_price_usd), style_text),      # Unit price
            Paragraph(fmt_money(it.amount_usd), style_text),          # Total amount
        ])

    # ========================================================================
    # CREATE LINE ITEMS TABLE
    # ========================================================================
    # Column widths are specified to fit different content types:
    # - Narrow columns for serial numbers and codes
    # - Wide column for descriptions
    # - Medium columns for numbers
    # Total width: 180mm (matching main info tables)

    li_table = Table(li_rows, colWidths=[10*mm, 24*mm, 24*mm, 50*mm, 19*mm, 26*mm, 27*mm])
    #                                      ^^     ^^     ^^     ^^     ^^     ^^     ^^
    #                                      Sr.    HSN    Item   Desc   Qty    Rate   Amount
    #                                      Total: 10+24+24+50+19+26+27 = 180mm

    # Apply styling to the line items table
    li_table.setStyle(TableStyle([
        # Draw grid around all cells
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

        # Header row background (row 0)
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),

        # Vertical alignment for all cells
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Default horizontal alignment is LEFT for all cells
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

        # RIGHT-align numeric columns (Qty, Rate, Amount = columns 4-6)
        # Starting from row 1 (data rows, not header) to last row (-1)
        ('ALIGN', (4, 1), (6, -1), 'RIGHT'),
        #          └────┘  └─────┘
        #          cols    rows
        #          4-6     1 to end

        # Cell padding
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    story.append(li_table)
    story.append(Spacer(1, 10))

    # ========================================================================
    # TOTAL AMOUNT TABLE
    # ========================================================================
    # Simple single-row table showing the invoice total

    total_usd = fmt_money(invoice.total_amount_usd)
    amount_section = [
        [
            # Column 0: Currency label (takes most of the width)
            Paragraph("<b>Amount Chargeable in:</b> USD", style_text),
            # Column 1: "Total" label
            Paragraph("<b>Total</b>", style_text),
            # Column 2: Total amount value
            Paragraph(f"${total_usd}", style_text)
        ]
    ]

    # Column widths: [100mm, 40mm, 40mm] = 180mm total
    amount_table = Table(amount_section, colWidths=[100*mm, 40*mm, 40*mm])

    amount_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Center vertically
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    story.append(amount_table)
    story.append(Spacer(1, 4))

    # ========================================================================
    # AMOUNT IN WORDS (Plain Paragraph)
    # ========================================================================
    # Not in a table, just a simple paragraph
    total_amount_usd = invoice.total_amount_usd
    currency_name = "USD"

    # Comma-separated amount
    formatted_amount = f"{int(total_amount_usd):,} {currency_name}"
    story.append(Paragraph(f"<b>Amount:</b> {formatted_amount}", style_text))
    story.append(Spacer(1, 4))

    # Amount in words
    amount_in_words_str = amount_to_words(total_amount_usd, currency=currency_name)
    story.append(Paragraph(f"<b>Amount in Words:</b> {amount_in_words_str}", style_text))
    story.append(Spacer(1, 10))

    # ========================================================================
    # VALIDITY AND SHIPMENT INFORMATION TABLE
    # ========================================================================
    # Single-column table with multiple rows
    # Each row contains one piece of information

    validity_data = [
        # Each inner list is a row with just one column
        [
            Paragraph(f"<b>Validity for Acceptance:</b> {safe(invoice.validity_for_acceptance)}", style_text)
        ],
        [
            Paragraph(f"<b>Validity for Shipment:</b> {safe(invoice.validity_for_shipment)}", style_text)
        ],
        [
            Paragraph(f"<b>Bank Charges:</b> {fmt_money(invoice.bank_charges)}", style_text)
        ],
        [
            Paragraph(f"<b>Partial Shipment:</b> {bool_yn(invoice.partial_shipment)}", style_text)
        ],
        [
            Paragraph(f"<b>Transshipment:</b> {bool_yn(invoice.transshipment)}", style_text)
        ]
    ]

    # Single-column table: colWidths=[180*mm] sets fixed width
    validity_table = Table(validity_data, colWidths=[180*mm])

    validity_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Draw borders
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),            # Align to top
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    story.append(validity_table)
    story.append(Spacer(1, 10))

    # ========================================================================
    # INFORMATIONAL PARAGRAPHS
    # ========================================================================

    # MT103 advisory - banking instruction
    story.append(Paragraph(
        "Request your bank to send MT 103 Message to our bank and send us copy of this message to trace & claim the payment from our bank.",
        style_text
    ))
    story.append(Spacer(1, 8))

    # Legal declaration
    story.append(Paragraph(
        "<b>Declaration:</b> We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.",
        style_text
    ))
    story.append(Spacer(1, 10))

    # ========================================================================
    # BENEFICIARY/BANK DETAILS TABLE
    # ========================================================================
    # Single-column table displaying bank account information
    # Similar structure to validity table above

    beneficiary_data = [
        # Each row contains one bank detail field
        [Paragraph(f"<b>BENEFICIARY NAME:</b> {safe(getattr(bank, 'beneficiary_name', '')) if bank else ''}", style_text)],
        [Paragraph(f"<b>BANK NAME:</b> {safe(getattr(bank, 'bank_name', '')) if bank else ''}", style_text)],
        [Paragraph(f"<b>BRANCH NAME:</b> {safe(getattr(bank, 'branch_name', '')) if bank else ''}", style_text)],
        [Paragraph(f"<b>BRANCH ADDRESS:</b> {safe(getattr(bank, 'branch_address', '')) if bank else ''}", style_text)],
        [Paragraph(f"<b>A/C NO.:</b> {safe(getattr(bank, 'account_number', '')) if bank else ''}", style_text)],
        [Paragraph(f"<b>SWIFT CODE:</b> {safe(getattr(bank, 'swift_code', '')) if bank else ''}", style_text)]
    ]

    # Create table with single column at 180mm width
    beneficiary_table = Table(beneficiary_data, colWidths=[180*mm])

    beneficiary_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Border around all cells
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),            # Top-aligned content
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    story.append(beneficiary_table)
    story.append(Spacer(1, 10))

    # ========================================================================
    # OPTIONAL: TERMS & CONDITIONS SECTION
    # ========================================================================
    # Only included if invoice has terms and conditions text

    if invoice.terms_and_conditions:
        # Add page break before terms and conditions
        story.append(PageBreak())

        # Section heading
        story.append(Paragraph("<b>Additional Terms & Conditions</b>", style_label))
        story.append(Spacer(1, 6))

        # Get the raw terms text
        tac_raw = safe(invoice.terms_and_conditions)

        # --------------------------------------------------------------------
        # HTML SANITIZATION
        # --------------------------------------------------------------------
        # The terms might contain HTML from a rich text editor
        # We need to clean it and keep only safe formatting
        # ReportLab Paragraphs support limited HTML: <b>, <i>, <br/>, <font>
        # We remove potentially harmful or unsupported tags

        # Normalize line endings to Unix style (\n)
        tac = tac_raw.replace("\r\n", "\n").replace("\r", "\n")

        # Normalize break tags to <br/>
        tac = tac.replace("<br>", "<br/>").replace("<br />", "<br/>")

        # Remove unsupported HTML tags using regex
        # re.I = case-insensitive, re.S = dot matches newlines

        tac = re.sub(r"<\s*(/)?\s*span[^>]*>", "", tac, flags=re.I)         # Remove <span>
        tac = re.sub(r"<\s*(/)?\s*div[^>]*>", "", tac, flags=re.I)          # Remove <div>
        tac = re.sub(r"<\s*(/)?\s*p[^>]*>", "", tac, flags=re.I)            # Remove <p>
        tac = re.sub(r"<\s*(/)?\s*style[^>]*>.*?</\s*style\s*>", "", tac, flags=re.I | re.S)   # Remove <style> blocks
        tac = re.sub(r"<\s*(/)?\s*script[^>]*>.*?</\s*script\s*>", "", tac, flags=re.I | re.S) # Remove <script> blocks

        # Remove any remaining HTML tags except <br/> (negative lookahead)
        tac = re.sub(r"<(?!br\s*/?>)[^>]+>", "", tac, flags=re.I)

        # Convert newlines to <br/> for proper rendering in Paragraph
        tac = tac.replace("\n", "<br/>")

        # Add the sanitized terms to the document
        story.append(Paragraph(tac, style_small))
        story.append(Spacer(1, 10))

    # ========================================================================
    # BUILD THE PDF
    # ========================================================================
    # doc.build() processes the entire story and generates the PDF
    # It handles:
    #   - Flowing content across multiple pages
    #   - Page breaks when content doesn't fit
    #   - Table splitting (if tables are too tall for one page)
    #   - Applying page templates and margins
    # The onPage callback adds the footer to each page

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)

    # Extract the PDF bytes from the buffer
    pdf_bytes = buffer.getvalue()

    # Clean up the buffer
    buffer.close()

    # Return the complete PDF as bytes
    return pdf_bytes


# ============================================================================
# KEY CONCEPTS SUMMARY
# ============================================================================
#
# 1. MEASUREMENTS:
#    - Use mm (millimeters) for real-world sizing: 1*mm, 45*mm, 180*mm
#    - Default unit is points: 1 point = 1/72 inch
#    - 1mm = 2.834645669 points
#
# 2. TABLE COORDINATES:
#    - (column, row) notation, zero-indexed
#    - (0, 0) is top-left cell
#    - -1 means "last column" or "last row"
#
# 3. CELL SPANNING:
#    - ('SPAN', (start_col, start_row), (end_col, end_row))
#    - End coordinates are INCLUSIVE
#    - Content comes from top-left cell of span
#    - Other cells in span should be empty strings ""
#
# 4. TABLE STYLING:
#    - Styles are applied in order (later styles override earlier ones)
#    - Can apply to entire table: (0, 0), (-1, -1)
#    - Or specific cells/ranges: (2, 1), (4, 3)
#    - Common commands: GRID, VALIGN, ALIGN, BACKGROUND, SPAN, padding
#
# 5. PARAGRAPHS:
#    - Support basic HTML: <b>, <i>, <br/>, <font>
#    - Style controlled by ParagraphStyle objects
#    - Key properties: fontSize, leading, alignment, fontName
#
# 6. STORY FLOW:
#    - Elements added to story list are rendered sequentially
#    - ReportLab handles pagination automatically
#    - Spacer() adds vertical space
#    - SimpleDocTemplate manages page layout
#
# ============================================================================
