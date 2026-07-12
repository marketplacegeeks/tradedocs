import pytest
from django.core.files.base import ContentFile

from apps.manual_edits.models import DocumentEditTracking
from apps.manual_edits.services import record_first_generation, list_all_documents
from apps.proforma_invoice.tests.factories import ProformaInvoiceFactory
from apps.packing_list.tests.factories import PackingListFactory
from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
from apps.purchase_order.tests.factories import PurchaseOrderFactory
from apps.certificate_of_analysis.tests.factories import CertificateOfAnalysisFactory

pytestmark = pytest.mark.django_db


# ---- record_first_generation ---------------------------------------------

def test_record_first_generation_creates_row_with_timestamp():
    record_first_generation("proforma_invoice", 42, "PI-2026-0001")

    tracking = DocumentEditTracking.objects.get(document_type="proforma_invoice", document_id=42)
    assert tracking.document_number == "PI-2026-0001"
    assert tracking.first_generated_at is not None


def test_record_first_generation_does_not_overwrite_existing_timestamp():
    record_first_generation("proforma_invoice", 42, "PI-2026-0001")
    tracking = DocumentEditTracking.objects.get(document_type="proforma_invoice", document_id=42)
    original_timestamp = tracking.first_generated_at

    record_first_generation("proforma_invoice", 42, "PI-2026-0001")
    tracking.refresh_from_db()
    assert tracking.first_generated_at == original_timestamp


def test_record_first_generation_sets_timestamp_if_row_exists_but_blank():
    # A manual-edit upload can create the tracking row before any PDF/Word was ever generated.
    DocumentEditTracking.objects.create(
        document_type="proforma_invoice",
        document_id=42,
        document_number="PI-2026-0001",
    )
    record_first_generation("proforma_invoice", 42, "PI-2026-0001")

    tracking = DocumentEditTracking.objects.get(document_type="proforma_invoice", document_id=42)
    assert tracking.first_generated_at is not None


# ---- list_all_documents ----------------------------------------------------

def test_list_all_documents_includes_all_five_document_types():
    ProformaInvoiceFactory()
    pl = PackingListFactory()
    CommercialInvoiceFactory(packing_list=pl)
    PurchaseOrderFactory()
    CertificateOfAnalysisFactory()

    rows = list_all_documents()
    types_seen = {row["document_type"] for row in rows}
    assert types_seen == {
        "proforma_invoice",
        "packing_list",
        "commercial_invoice",
        "purchase_order",
        "certificate_of_analysis",
    }


def test_list_all_documents_row_shape_for_proforma_invoice():
    pi = ProformaInvoiceFactory()

    rows = list_all_documents()
    row = next(r for r in rows if r["document_type"] == "proforma_invoice" and r["document_id"] == pi.pk)

    assert row["document_number"] == pi.pi_number
    assert row["exporter_name"] == pi.exporter.name
    assert row["importer_name"] == pi.consignee.name
    assert row["vendor_name"] == ""
    assert row["first_generated_at"] is None
    assert row["has_manual_edit"] is False


def test_list_all_documents_purchase_order_has_vendor_but_no_exporter_or_importer():
    po = PurchaseOrderFactory()

    rows = list_all_documents()
    row = next(r for r in rows if r["document_type"] == "purchase_order" and r["document_id"] == po.pk)

    assert row["vendor_name"] == po.vendor.name
    assert row["exporter_name"] == ""
    assert row["importer_name"] == ""


def test_list_all_documents_commercial_invoice_inherits_parties_from_linked_packing_list():
    pl = PackingListFactory()
    ci = CommercialInvoiceFactory(packing_list=pl)

    rows = list_all_documents()
    row = next(r for r in rows if r["document_type"] == "commercial_invoice" and r["document_id"] == ci.pk)

    assert row["exporter_name"] == pl.exporter.name
    assert row["importer_name"] == pl.consignee.name


def test_list_all_documents_reflects_first_generated_at_and_manual_edit_state():
    pi = ProformaInvoiceFactory()
    record_first_generation("proforma_invoice", pi.pk, pi.pi_number)
    tracking = DocumentEditTracking.objects.get(document_type="proforma_invoice", document_id=pi.pk)
    tracking.edited_pdf_file.save("edited.pdf", ContentFile(b"data"), save=True)

    rows = list_all_documents()
    row = next(r for r in rows if r["document_type"] == "proforma_invoice" and r["document_id"] == pi.pk)

    assert row["first_generated_at"] == tracking.first_generated_at
    assert row["has_manual_edit"] is True


# ---- download URLs ----------------------------------------------------------

def test_list_all_documents_gives_standard_download_urls_for_proforma_invoice():
    pi = ProformaInvoiceFactory()

    rows = list_all_documents()
    row = next(r for r in rows if r["document_type"] == "proforma_invoice" and r["document_id"] == pi.pk)

    assert row["download_pdf_path"] == f"/proforma-invoices/{pi.pk}/pdf/"
    assert row["download_word_path"] == f"/proforma-invoices/{pi.pk}/word/"


def test_list_all_documents_ci_download_pdf_points_to_client_invoice_endpoint_on_its_packing_list():
    pl = PackingListFactory()
    ci = CommercialInvoiceFactory(packing_list=pl)

    rows = list_all_documents()
    row = next(r for r in rows if r["document_type"] == "commercial_invoice" and r["document_id"] == ci.pk)

    # CI has no PDF endpoint of its own — it's generated as part of its parent Packing List.
    assert row["download_pdf_path"] == f"/packing-lists/{pl.pk}/client-invoice-pdf/"
    assert row["download_word_path"] is None
