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
from reportlab.platypus import Flowable, PageBreak, SimpleDocTemplate
from reportlab.pdfgen import canvas


class _PLSectionMarker(Flowable):
    """
    Zero-size marker flowable placed at the top of the Packing List section.
    When drawn it records the current page number on the canvas so that
    NumberedCanvas can compute independent page counters for CI and PL.
    """

    def __init__(self):
        super().__init__()
        self.width = 0
        self.height = 0

    def wrap(self, *args):
        return 0, 0

    def draw(self):
        # canvas.getPageNumber() returns the 1-based page currently being built
        self.canv._pl_section_start_page = self.canv.getPageNumber()


def generate_pl_ci_pdf(pl, client_invoice=False) -> io.BytesIO:
    """
    Generate a combined Commercial Invoice + Packing List PDF.
    Returns an in-memory BytesIO buffer — constraint #20: never writes to disk.

    Section 1 — Commercial Invoice (starts at page 1)
    Section 2 — Packing List (starts on a new page after the CI)

    When client_invoice=True, CI line item rates are CIF-adjusted using the
    linked Proforma Invoice's freight and insurance_amount values.
    """
    try:
        ci = pl.commercial_invoice
    except Exception:
        ci = None

    # Resolve the linked PI for CIF rate calculation (used when client_invoice=True)
    pi = getattr(pl, "proforma_invoice", None)

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
            story = build_ci_story(ci, ci_styles, client_invoice=client_invoice, pi=pi)
        except ImportError:
            pass

    # Section 2 — Packing List (comes after CI).
    # _PLSectionMarker is always the first item in the PL section so that
    # NumberedCanvas can detect the CI/PL page boundary during rendering.
    pl_section: list = [_PLSectionMarker()]
    try:
        from pdf.packing_list_generator import _make_pl_styles, build_pl_story
        pl_styles = _make_pl_styles()
        pl_section += build_pl_story(pl, pl_styles)
    except ImportError:
        # Fallback: create minimal story if generators not available
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        styles = getSampleStyleSheet()
        pl_section += [
            Paragraph("PACKING LIST", styles['Title']),
            Spacer(1, 12),
            Paragraph("Packing list content would appear here.", styles['Normal']),
        ]

    if story:  # Add page break between CI and PL
        story.append(PageBreak())
    story += pl_section

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

            # Find the page where PL begins (recorded by _PLSectionMarker.draw()).
            # CI pages are 1 .. pl_start-1; PL pages are pl_start .. total_pages.
            pl_start = None
            for state in self._saved_page_states:
                if '_pl_section_start_page' in state:
                    pl_start = state['_pl_section_start_page']
                    break
            ci_total = (pl_start - 1) if pl_start is not None else total_pages

            for page_num, state in enumerate(self._saved_page_states, start=1):
                self.__dict__.update(state)
                self._draw_footer(page_num, pl_start, ci_total, total_pages)
                super().showPage()
            super().save()

        def _draw_footer(self, page_num, pl_start, ci_total, total_pages):
            # DRAFT watermark on all non-Approved documents (FR-08.3)
            if is_draft:
                self.saveState()
                self.setFont("Helvetica-Bold", 80)
                self.setFillColor(_HexColor('#CC0000'), alpha=0.15)
                self.translate(A4[0] / 2, A4[1] / 2)
                self.rotate(45)
                self.drawCentredString(0, 0, "DRAFT")
                self.restoreState()

            # Each document section gets its own independent page counter.
            if pl_start is not None and page_num >= pl_start:
                pl_page = page_num - pl_start + 1
                pl_total = total_pages - ci_total
                page_label = f"Page {pl_page} of {pl_total}"
            else:
                page_label = f"Page {page_num} of {ci_total}"

            self.saveState()
            self.setFont("Helvetica", 8)
            self.drawCentredString(
                A4[0] / 2, 12 * mm,
                "This is a computer generated document and does not require signature",
            )
            self.setFont("Helvetica", 7)
            self.drawCentredString(A4[0] / 2, 8 * mm, page_label)
            self.restoreState()

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
