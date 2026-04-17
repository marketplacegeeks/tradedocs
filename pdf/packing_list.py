"""
Combined Packing List + Commercial Invoice PDF generator (FR-14M.13).

Produces a single in-memory PDF with two sections:
  Section 1 — Commercial Invoice          (pages 1+)
  Section 2 — Packing List / Weight Note  (starts on a new page)

Both sections use the pdf1/ reference layout from their respective story
builders.  A PageBreak separates them inside a single SimpleDocTemplate so
only one pass of doc.build() is needed.

Constraint #20: Returns a BytesIO buffer — never writes to disk.
"""
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, SimpleDocTemplate
from reportlab.pdfgen import canvas


def generate_pl_ci_pdf(pl) -> io.BytesIO:
    """
    Generate a combined Commercial Invoice + Packing List PDF.
    Returns an in-memory BytesIO buffer — constraint #20: never writes to disk.

    Section 1 — Commercial Invoice (starts at page 1)
    Section 2 — Packing List (starts on a new page after the CI)
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

    # Import the story builders - CI first, then PL
    story = []

    # Section 1 — Commercial Invoice (if exists)
    if ci is not None:
        try:
            from pdf.commercial_invoice_generator import _make_ci_styles, build_ci_story
            ci_styles = _make_ci_styles()
            story = build_ci_story(ci, ci_styles)
        except ImportError:
            pass

    # Section 2 — Packing List (comes after CI)
    try:
        from pdf.packing_list_generator import _make_pl_styles, build_pl_story
        pl_styles = _make_pl_styles()
        if story:  # Add page break if CI was generated
            story.append(PageBreak())
        story += build_pl_story(pl, pl_styles)
    except ImportError:
        # Fallback: create minimal story if generators not available
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        styles = getSampleStyleSheet()
        if story:
            story.append(PageBreak())
        story += [
            Paragraph("PACKING LIST", styles['Title']),
            Spacer(1, 12),
            Paragraph("Packing list content would appear here.", styles['Normal']),
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
            # DRAFT watermark on all non-Approved documents (FR-08.3)
            if is_draft:
                self.saveState()
                self.setFont("Helvetica-Bold", 80)
                self.setFillColor(_HexColor('#CC0000'), alpha=0.15)
                self.translate(A4[0] / 2, A4[1] / 2)
                self.rotate(45)
                self.drawCentredString(0, 0, "DRAFT")
                self.restoreState()

            self.saveState()
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
