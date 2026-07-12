"""
Aggregation and tracking logic for the "Manual Edits" page.
Combines documents from all 5 document apps into one list, joined against
DocumentEditTracking for first-generation timestamps and manual-edit state.
"""
from django.utils import timezone

from apps.commercial_invoice.models import CommercialInvoice
from apps.certificate_of_analysis.models import CertificateOfAnalysis
from apps.packing_list.models import PackingList
from apps.proforma_invoice.models import ProformaInvoice
from apps.purchase_order.models import PurchaseOrder

from .models import DocumentEditTracking


def _org_name(org):
    return org.name if org else ""


def _proforma_invoice_rows():
    for pi in ProformaInvoice.objects.select_related("exporter", "consignee").all():
        yield {
            "document_type": "proforma_invoice",
            "document_id": pi.pk,
            "document_number": pi.pi_number,
            "exporter_name": _org_name(pi.exporter),
            "importer_name": _org_name(pi.consignee),
            "vendor_name": "",
            "download_pdf_path": f"/proforma-invoices/{pi.pk}/pdf/",
            "download_word_path": f"/proforma-invoices/{pi.pk}/word/",
        }


def _packing_list_rows():
    for pl in PackingList.objects.select_related("exporter", "consignee").all():
        yield {
            "document_type": "packing_list",
            "document_id": pl.pk,
            "document_number": pl.pl_number,
            "exporter_name": _org_name(pl.exporter),
            "importer_name": _org_name(pl.consignee),
            "vendor_name": "",
            "download_pdf_path": f"/packing-lists/{pl.pk}/pdf/",
            "download_word_path": f"/packing-lists/{pl.pk}/word/",
        }


def _commercial_invoice_rows():
    for ci in CommercialInvoice.objects.select_related(
        "packing_list__exporter", "packing_list__consignee"
    ).all():
        pl = ci.packing_list
        yield {
            "document_type": "commercial_invoice",
            "document_id": ci.pk,
            "document_number": ci.ci_number,
            "exporter_name": _org_name(pl.exporter) if pl else "",
            "importer_name": _org_name(pl.consignee) if pl else "",
            "vendor_name": "",
            # CI has no PDF/Word endpoint of its own — it's rendered as part of its
            # parent Packing List's CIF-adjusted "client invoice" PDF. No Word equivalent exists.
            "download_pdf_path": f"/packing-lists/{pl.pk}/client-invoice-pdf/" if pl else None,
            "download_word_path": None,
        }


def _purchase_order_rows():
    for po in PurchaseOrder.objects.select_related("vendor").all():
        yield {
            "document_type": "purchase_order",
            "document_id": po.pk,
            "document_number": po.po_number,
            "exporter_name": "",
            "importer_name": "",
            "vendor_name": _org_name(po.vendor),
            "download_pdf_path": f"/purchase-orders/{po.pk}/pdf/",
            "download_word_path": f"/purchase-orders/{po.pk}/word/",
        }


def _certificate_of_analysis_rows():
    for coa in CertificateOfAnalysis.objects.all():
        yield {
            "document_type": "certificate_of_analysis",
            "document_id": coa.pk,
            "document_number": coa.coa_number,
            "exporter_name": "",
            "importer_name": "",
            "vendor_name": "",
            "download_pdf_path": f"/coas/{coa.pk}/pdf/",
            "download_word_path": f"/coas/{coa.pk}/word/",
        }


_ROW_BUILDERS = [
    _proforma_invoice_rows,
    _packing_list_rows,
    _commercial_invoice_rows,
    _purchase_order_rows,
    _certificate_of_analysis_rows,
]

# document_type -> (Model, number_field_name). Used by the upload endpoint to
# validate a document exists and to snapshot its number onto DocumentEditTracking.
DOCUMENT_MODELS = {
    "proforma_invoice": (ProformaInvoice, "pi_number"),
    "packing_list": (PackingList, "pl_number"),
    "commercial_invoice": (CommercialInvoice, "ci_number"),
    "purchase_order": (PurchaseOrder, "po_number"),
    "certificate_of_analysis": (CertificateOfAnalysis, "coa_number"),
}


def record_first_generation(document_type, document_id, document_number):
    """
    Stamp the first time a PDF/Word was generated for a document.
    Idempotent — later calls never overwrite an existing timestamp.
    """
    tracking, created = DocumentEditTracking.objects.get_or_create(
        document_type=document_type,
        document_id=document_id,
        defaults={
            "document_number": document_number,
            "first_generated_at": timezone.now(),
        },
    )
    if not created and tracking.first_generated_at is None:
        tracking.first_generated_at = timezone.now()
        tracking.document_number = document_number
        tracking.save(update_fields=["first_generated_at", "document_number"])


def list_all_documents():
    """
    Returns one dict per document across all 5 document types, joined with
    its DocumentEditTracking row (if any) for first-generation and
    manual-edit state.
    """
    rows = [row for builder in _ROW_BUILDERS for row in builder()]

    tracking_by_key = {
        (t.document_type, t.document_id): t
        for t in DocumentEditTracking.objects.all()
    }

    for row in rows:
        tracking = tracking_by_key.get((row["document_type"], row["document_id"]))
        if tracking:
            row["first_generated_at"] = tracking.first_generated_at
            row["has_manual_edit"] = bool(tracking.edited_word_file or tracking.edited_pdf_file)
            row["edit_comment"] = tracking.edit_comment
            row["edited_at"] = tracking.edited_at
            row["edited_by_name"] = tracking.edited_by.full_name if tracking.edited_by else ""
            row["edited_word_file"] = tracking.edited_word_file
            row["edited_pdf_file"] = tracking.edited_pdf_file
        else:
            row["first_generated_at"] = None
            row["has_manual_edit"] = False
            row["edit_comment"] = ""
            row["edited_at"] = None
            row["edited_by_name"] = ""
            row["edited_word_file"] = None
            row["edited_pdf_file"] = None

    return rows
