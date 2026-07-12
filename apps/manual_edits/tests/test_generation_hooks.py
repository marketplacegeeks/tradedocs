"""
Confirms that downloading a PDF/Word for any document type stamps
DocumentEditTracking.first_generated_at the first time, and never again.
"""
import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import MakerFactory
from apps.manual_edits.models import DocumentEditTracking
from apps.proforma_invoice.tests.factories import ProformaInvoiceFactory
from apps.packing_list.tests.factories import PackingListFactory
from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
from apps.purchase_order.tests.factories import PurchaseOrderFactory
from apps.certificate_of_analysis.tests.factories import CertificateOfAnalysisFactory

pytestmark = pytest.mark.django_db


def auth_client():
    client = APIClient()
    client.force_authenticate(user=MakerFactory())
    return client


def tracking_for(document_type, document_id):
    return DocumentEditTracking.objects.get(document_type=document_type, document_id=document_id)


@pytest.mark.parametrize("action", ["pdf", "word"])
def test_proforma_invoice_download_records_first_generation(action):
    pi = ProformaInvoiceFactory()
    client = auth_client()

    response = client.get(f"/api/v1/proforma-invoices/{pi.pk}/{action}/")

    assert response.status_code == 200
    tracking = tracking_for("proforma_invoice", pi.pk)
    assert tracking.first_generated_at is not None
    assert tracking.document_number == pi.pi_number


@pytest.mark.parametrize("action", ["pdf", "word"])
def test_packing_list_download_records_first_generation(action):
    pl = PackingListFactory()
    client = auth_client()

    response = client.get(f"/api/v1/packing-lists/{pl.pk}/{action}/")

    assert response.status_code == 200
    tracking = tracking_for("packing_list", pl.pk)
    assert tracking.first_generated_at is not None


def test_client_invoice_pdf_records_first_generation_against_commercial_invoice():
    pl = PackingListFactory()
    ci = CommercialInvoiceFactory(packing_list=pl)
    client = auth_client()

    response = client.get(f"/api/v1/packing-lists/{pl.pk}/client-invoice-pdf/")

    assert response.status_code == 200
    tracking = tracking_for("commercial_invoice", ci.pk)
    assert tracking.first_generated_at is not None
    assert tracking.document_number == ci.ci_number


@pytest.mark.parametrize("action", ["pdf", "word"])
def test_purchase_order_download_records_first_generation(action):
    po = PurchaseOrderFactory()
    client = auth_client()

    response = client.get(f"/api/v1/purchase-orders/{po.pk}/{action}/")

    assert response.status_code == 200
    tracking = tracking_for("purchase_order", po.pk)
    assert tracking.first_generated_at is not None


@pytest.mark.parametrize("action", ["pdf", "word"])
def test_certificate_of_analysis_download_records_first_generation(action):
    coa = CertificateOfAnalysisFactory()
    client = auth_client()

    response = client.get(f"/api/v1/coas/{coa.pk}/{action}/")

    assert response.status_code == 200
    tracking = tracking_for("certificate_of_analysis", coa.pk)
    assert tracking.first_generated_at is not None


def test_second_download_does_not_change_first_generated_at():
    pi = ProformaInvoiceFactory()
    client = auth_client()

    client.get(f"/api/v1/proforma-invoices/{pi.pk}/pdf/")
    first_timestamp = tracking_for("proforma_invoice", pi.pk).first_generated_at

    client.get(f"/api/v1/proforma-invoices/{pi.pk}/pdf/")
    second_timestamp = tracking_for("proforma_invoice", pi.pk).first_generated_at

    assert first_timestamp == second_timestamp
