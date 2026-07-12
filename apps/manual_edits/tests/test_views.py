"""
API view tests for the Manual Edits page.

Every endpoint has at minimum:
- One happy-path test
- One permission-denial test
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.tests.factories import MakerFactory
from apps.manual_edits.models import DocumentEditTracking
from apps.proforma_invoice.tests.factories import ProformaInvoiceFactory

pytestmark = pytest.mark.django_db


def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


LIST_URL = "/api/v1/manual-edits/"


def upload_url(document_type, document_id):
    return f"/api/v1/manual-edits/{document_type}/{document_id}/upload/"


# ---- List endpoint ----------------------------------------------------------

def test_list_returns_documents_across_all_types():
    pi = ProformaInvoiceFactory()
    client = auth_client(MakerFactory())

    response = client.get(LIST_URL)

    assert response.status_code == 200
    numbers = [row["document_number"] for row in response.data]
    assert pi.pi_number in numbers


def test_list_denies_unauthenticated_requests():
    client = APIClient()

    response = client.get(LIST_URL)

    assert response.status_code == 401


# ---- Upload endpoint ----------------------------------------------------------

def test_upload_saves_files_and_comment():
    pi = ProformaInvoiceFactory()
    client = auth_client(MakerFactory())
    pdf_file = SimpleUploadedFile("edited.pdf", b"%PDF-1.4 fake", content_type="application/pdf")

    response = client.post(
        upload_url("proforma_invoice", pi.pk),
        data={"comment": "Buyer name misspelled on original PDF.", "pdf_file": pdf_file},
        format="multipart",
    )

    assert response.status_code == 200
    tracking = DocumentEditTracking.objects.get(document_type="proforma_invoice", document_id=pi.pk)
    assert tracking.edit_comment == "Buyer name misspelled on original PDF."
    assert tracking.edited_pdf_file.name
    assert tracking.edited_at is not None


def test_upload_blocked_when_comment_is_empty():
    pi = ProformaInvoiceFactory()
    client = auth_client(MakerFactory())
    pdf_file = SimpleUploadedFile("edited.pdf", b"%PDF-1.4 fake", content_type="application/pdf")

    response = client.post(
        upload_url("proforma_invoice", pi.pk),
        data={"comment": "", "pdf_file": pdf_file},
        format="multipart",
    )

    assert response.status_code == 400
    assert not DocumentEditTracking.objects.filter(document_type="proforma_invoice", document_id=pi.pk).exists()


def test_upload_blocked_when_no_file_provided():
    pi = ProformaInvoiceFactory()
    client = auth_client(MakerFactory())

    response = client.post(
        upload_url("proforma_invoice", pi.pk),
        data={"comment": "Some reason with no attached file."},
        format="multipart",
    )

    assert response.status_code == 400


def test_upload_denies_unauthenticated_requests():
    pi = ProformaInvoiceFactory()
    client = APIClient()
    pdf_file = SimpleUploadedFile("edited.pdf", b"%PDF-1.4 fake", content_type="application/pdf")

    response = client.post(
        upload_url("proforma_invoice", pi.pk),
        data={"comment": "reason", "pdf_file": pdf_file},
        format="multipart",
    )

    assert response.status_code == 401


def test_upload_404_for_unknown_document_type():
    client = auth_client(MakerFactory())
    pdf_file = SimpleUploadedFile("edited.pdf", b"%PDF-1.4 fake", content_type="application/pdf")

    response = client.post(
        upload_url("not_a_real_type", 1),
        data={"comment": "reason", "pdf_file": pdf_file},
        format="multipart",
    )

    assert response.status_code == 404
