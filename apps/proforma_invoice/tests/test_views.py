"""
API view tests for Proforma Invoice endpoints.

Every endpoint has at minimum:
- One happy-path test
- One permission-denial test
"""

import io
import pytest
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CheckerFactory, CompanyAdminFactory, MakerFactory
from apps.master_data.tests.factories import (
    IncotermFactory, OrganisationFactory, PaymentTermFactory,
)
from apps.workflow.constants import DRAFT, PENDING_APPROVAL, APPROVED, REWORK, PERMANENTLY_REJECTED

from .factories import (
    ProformaInvoiceChargeFactory,
    ProformaInvoiceFactory,
    ProformaInvoiceLineItemFactory,
)


# ---- Helpers ----------------------------------------------------------------

def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


PI_LIST_URL = "/api/v1/proforma-invoices/"


def pi_detail_url(pk):
    return f"/api/v1/proforma-invoices/{pk}/"


def pi_workflow_url(pk):
    return f"/api/v1/proforma-invoices/{pk}/workflow/"


def pi_pdf_url(pk):
    return f"/api/v1/proforma-invoices/{pk}/pdf/"


def pi_audit_url(pk):
    return f"/api/v1/proforma-invoices/{pk}/audit-log/"


def pi_line_item_url(pk):
    return f"/api/v1/proforma-invoices/{pk}/line-items/"


def pi_line_item_detail_url(pk, lid):
    return f"/api/v1/proforma-invoices/{pk}/line-items/{lid}/"


def pi_charge_url(pk):
    return f"/api/v1/proforma-invoices/{pk}/charges/"


def pi_charge_detail_url(pk, cid):
    return f"/api/v1/proforma-invoices/{pk}/charges/{cid}/"


# ---- List & Detail ----------------------------------------------------------

@pytest.mark.django_db
class TestProformaInvoiceList:

    def test_maker_can_list(self):
        maker = MakerFactory()
        ProformaInvoiceFactory.create_batch(3, created_by=maker)
        resp = auth_client(maker).get(PI_LIST_URL)
        assert resp.status_code == 200
        assert len(resp.data) >= 3

    def test_unauthenticated_denied(self):
        resp = APIClient().get(PI_LIST_URL)
        assert resp.status_code == 401

    def test_filter_by_status(self):
        maker = MakerFactory()
        ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        ProformaInvoiceFactory(created_by=maker, status=PENDING_APPROVAL)
        resp = auth_client(maker).get(PI_LIST_URL, {"status": DRAFT})
        assert resp.status_code == 200
        assert all(pi["status"] == DRAFT for pi in resp.data)


@pytest.mark.django_db
class TestProformaInvoiceDetail:

    def test_checker_can_retrieve(self):
        pi = ProformaInvoiceFactory()
        resp = auth_client(CheckerFactory()).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200
        assert resp.data["pi_number"] == pi.pi_number

    def test_unauthenticated_denied(self):
        pi = ProformaInvoiceFactory()
        resp = APIClient().get(pi_detail_url(pi.pk))
        assert resp.status_code == 401


# ---- Create -----------------------------------------------------------------

@pytest.mark.django_db
class TestProformaInvoiceCreate:

    def _payload(self):
        exporter = OrganisationFactory()
        consignee = OrganisationFactory()
        return {
            "exporter": exporter.pk,
            "consignee": consignee.pk,
        }

    def test_maker_can_create(self):
        maker = MakerFactory()
        resp = auth_client(maker).post(PI_LIST_URL, self._payload(), format="json")
        assert resp.status_code == 201
        assert resp.data["status"] == DRAFT
        assert resp.data["created_by"] == maker.pk
        # pi_number should be auto-generated
        assert resp.data["pi_number"].startswith("PI-")

    def test_checker_cannot_create(self):
        resp = auth_client(CheckerFactory()).post(PI_LIST_URL, self._payload(), format="json")
        assert resp.status_code == 403

    def test_pi_date_defaults_to_today(self):
        from datetime import date
        maker = MakerFactory()
        resp = auth_client(maker).post(PI_LIST_URL, self._payload(), format="json")
        assert resp.status_code == 201
        assert resp.data["pi_date"] == str(date.today())


# ---- Update -----------------------------------------------------------------

@pytest.mark.django_db
class TestProformaInvoiceUpdate:

    def test_creator_can_update_draft(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        resp = auth_client(maker).patch(pi_detail_url(pi.pk), {"buyer_order_no": "BO-001"}, format="json")
        assert resp.status_code == 200
        assert resp.data["buyer_order_no"] == "BO-001"

    def test_non_creator_cannot_update(self):
        other_maker = MakerFactory()
        pi = ProformaInvoiceFactory(status=DRAFT)
        resp = auth_client(other_maker).patch(pi_detail_url(pi.pk), {"buyer_order_no": "X"}, format="json")
        assert resp.status_code == 403

    def test_cannot_update_approved_pi(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=APPROVED)
        resp = auth_client(maker).patch(pi_detail_url(pi.pk), {"buyer_order_no": "X"}, format="json")
        assert resp.status_code == 400


# ---- Workflow ----------------------------------------------------------------

@pytest.mark.django_db
class TestProformaInvoiceWorkflow:

    def test_maker_can_submit(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        resp = auth_client(maker).post(pi_workflow_url(pi.pk), {"action": "SUBMIT"}, format="json")
        assert resp.status_code == 200
        assert resp.data["status"] == PENDING_APPROVAL

    def test_checker_can_approve(self):
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        checker = CheckerFactory()
        resp = auth_client(checker).post(pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json")
        assert resp.status_code == 200
        assert resp.data["status"] == APPROVED

    def test_checker_rework_requires_comment(self):
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        resp = auth_client(CheckerFactory()).post(pi_workflow_url(pi.pk), {"action": "REWORK"}, format="json")
        assert resp.status_code == 400

    def test_checker_rework_with_comment_succeeds(self):
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        resp = auth_client(CheckerFactory()).post(
            pi_workflow_url(pi.pk),
            {"action": "REWORK", "comment": "Please fix the description."},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["status"] == REWORK

    def test_maker_cannot_approve(self):
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        resp = auth_client(MakerFactory()).post(pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json")
        assert resp.status_code == 403

    def test_permanently_reject_requires_comment(self):
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        resp = auth_client(CheckerFactory()).post(
            pi_workflow_url(pi.pk), {"action": "PERMANENTLY_REJECT"}, format="json"
        )
        assert resp.status_code == 400

    def test_permanently_reject_with_comment(self):
        pi = ProformaInvoiceFactory(status=DRAFT)
        resp = auth_client(CheckerFactory()).post(
            pi_workflow_url(pi.pk),
            {"action": "PERMANENTLY_REJECT", "comment": "Fraudulent document."},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["status"] == PERMANENTLY_REJECTED

    def test_audit_log_written_on_transition(self):
        from apps.workflow.models import AuditLog
        pi = ProformaInvoiceFactory(status=DRAFT)
        maker = pi.created_by
        auth_client(maker).post(pi_workflow_url(pi.pk), {"action": "SUBMIT"}, format="json")
        log = AuditLog.objects.filter(document_type="proforma_invoice", document_id=pi.pk).first()
        assert log is not None
        assert log.action == "SUBMIT"
        assert log.from_status == DRAFT
        assert log.to_status == PENDING_APPROVAL

    def test_invalid_action_rejected(self):
        pi = ProformaInvoiceFactory(status=DRAFT)
        resp = auth_client(pi.created_by).post(
            pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json"
        )
        assert resp.status_code == 400

# ---- Audit log --------------------------------------------------------------

@pytest.mark.django_db
class TestAuditLogEndpoint:

    def test_any_role_can_read_audit_log(self):
        pi = ProformaInvoiceFactory(status=DRAFT)
        auth_client(pi.created_by).post(pi_workflow_url(pi.pk), {"action": "SUBMIT"}, format="json")
        resp = auth_client(CheckerFactory()).get(pi_audit_url(pi.pk))
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_unauthenticated_denied(self):
        pi = ProformaInvoiceFactory()
        resp = APIClient().get(pi_audit_url(pi.pk))
        assert resp.status_code == 401


# ---- Line items -------------------------------------------------------------

@pytest.mark.django_db
class TestLineItems:

    def test_maker_can_add_line_item(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        payload = {
            "description": "Soybean Oil",
            "quantity": "100.000",
            "rate_usd": "50.00",
        }
        resp = auth_client(maker).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 201
        assert resp.data["amount_usd"] == "5000.00"

    def test_checker_cannot_add_line_item(self):
        pi = ProformaInvoiceFactory(status=DRAFT)
        payload = {"description": "X", "quantity": "1.000", "rate_usd": "10.00"}
        resp = auth_client(CheckerFactory()).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 403

    def test_cannot_add_line_item_to_approved_pi(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=APPROVED)
        payload = {"description": "X", "quantity": "1.000", "rate_usd": "10.00"}
        resp = auth_client(maker).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 400

    def test_maker_can_delete_line_item(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        item = ProformaInvoiceLineItemFactory(pi=pi)
        resp = auth_client(maker).delete(pi_line_item_detail_url(pi.pk, item.pk))
        assert resp.status_code == 204

    def test_invalid_hsn_code_rejected(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        payload = {"description": "X", "quantity": "1.000", "rate_usd": "10.00", "hsn_code": "12345"}
        resp = auth_client(maker).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 400


# ---- Charges ----------------------------------------------------------------

@pytest.mark.django_db
class TestCharges:

    def test_maker_can_add_charge(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        payload = {"description": "Bank Charges", "amount_usd": "150.00"}
        resp = auth_client(maker).post(pi_charge_url(pi.pk), payload, format="json")
        assert resp.status_code == 201
        assert resp.data["description"] == "Bank Charges"

    def test_checker_cannot_add_charge(self):
        pi = ProformaInvoiceFactory(status=DRAFT)
        payload = {"description": "X", "amount_usd": "50.00"}
        resp = auth_client(CheckerFactory()).post(pi_charge_url(pi.pk), payload, format="json")
        assert resp.status_code == 403

    def test_maker_can_delete_charge(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        charge = ProformaInvoiceChargeFactory(pi=pi)
        resp = auth_client(maker).delete(pi_charge_detail_url(pi.pk, charge.pk))
        assert resp.status_code == 204


# ---- Computed totals in serializer ------------------------------------------

@pytest.mark.django_db
class TestSerializerTotals:

    def test_grand_total_includes_line_items_and_charges(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        ProformaInvoiceLineItemFactory(pi=pi, quantity=Decimal("10.000"), rate_usd=Decimal("100.00"))
        ProformaInvoiceChargeFactory(pi=pi, amount_usd=Decimal("50.00"))
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200
        assert Decimal(resp.data["grand_total"]) == Decimal("1050.00")

    def test_invoice_total_equals_grand_total_for_exw(self):
        from apps.master_data.tests.factories import IncotermFactory
        maker = MakerFactory()
        exw = IncotermFactory(code="EXW")
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT, incoterms=exw)
        ProformaInvoiceLineItemFactory(pi=pi, quantity=Decimal("5.000"), rate_usd=Decimal("200.00"))
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        assert Decimal(resp.data["invoice_total"]) == Decimal(resp.data["grand_total"])


# ---- Self-approval block (FR-08.2 / US-04) ----------------------------------

@pytest.mark.django_db
class TestSelfApprovalBlock:

    def test_maker_cannot_approve_own_document(self):
        """A Maker who created a PI cannot approve it."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=PENDING_APPROVAL)
        resp = auth_client(maker).post(pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json")
        assert resp.status_code == 403

    def test_checker_cannot_approve_own_document(self):
        """A Checker who created a PI cannot approve it."""
        checker = CheckerFactory()
        pi = ProformaInvoiceFactory(created_by=checker, status=PENDING_APPROVAL)
        resp = auth_client(checker).post(pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json")
        assert resp.status_code == 403

    def test_admin_can_approve_own_document(self):
        """A Company Admin who created a PI is allowed to approve it."""
        admin = CompanyAdminFactory()
        pi = ProformaInvoiceFactory(created_by=admin, status=PENDING_APPROVAL)
        resp = auth_client(admin).post(pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json")
        assert resp.status_code == 200
        assert resp.data["status"] == APPROVED

    def test_different_checker_can_approve(self):
        """A Checker who did NOT create the PI can approve it normally."""
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        checker = CheckerFactory()
        resp = auth_client(checker).post(pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json")
        assert resp.status_code == 200
        assert resp.data["status"] == APPROVED


# ---- Signed copy upload (FR-08.4) -------------------------------------------

def pi_signed_copy_url(pk):
    return f"/api/v1/proforma-invoices/{pk}/signed-copy/"


def _small_pdf():
    """Return a tiny fake PDF file for upload tests."""
    return SimpleUploadedFile("signed.pdf", b"%PDF-1.4 fake content", content_type="application/pdf")


@pytest.mark.django_db
class TestSignedCopyUpload:

    def test_upload_succeeds_for_approved_pi(self):
        pi = ProformaInvoiceFactory(status=APPROVED)
        resp = auth_client(MakerFactory()).post(
            pi_signed_copy_url(pi.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        assert resp.status_code == 200
        assert resp.data["signed_copy_url"] is not None

    def test_upload_blocked_for_non_approved_pi(self):
        pi = ProformaInvoiceFactory(status=DRAFT)
        resp = auth_client(MakerFactory()).post(
            pi_signed_copy_url(pi.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        assert resp.status_code == 400

    def test_upload_blocked_for_pending_approval(self):
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        resp = auth_client(CheckerFactory()).post(
            pi_signed_copy_url(pi.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        assert resp.status_code == 400

    def test_upload_requires_file_field(self):
        pi = ProformaInvoiceFactory(status=APPROVED)
        resp = auth_client(MakerFactory()).post(
            pi_signed_copy_url(pi.pk),
            {},  # no file
            format="multipart",
        )
        assert resp.status_code == 400

    def test_upload_rejects_oversized_file(self, settings):
        settings.SIGNED_COPY_MAX_BYTES = 10  # 10 bytes — anything real will exceed this
        pi = ProformaInvoiceFactory(status=APPROVED)
        resp = auth_client(MakerFactory()).post(
            pi_signed_copy_url(pi.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        assert resp.status_code == 400

    def test_unauthenticated_upload_denied(self):
        pi = ProformaInvoiceFactory(status=APPROVED)
        resp = APIClient().post(
            pi_signed_copy_url(pi.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        assert resp.status_code == 401

    def test_signed_copy_url_appears_in_detail_response(self):
        """After upload, GET on the PI returns a non-null signed_copy_url."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(status=APPROVED)
        auth_client(maker).post(
            pi_signed_copy_url(pi.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200
        assert resp.data["signed_copy_url"] is not None


# ---- Name fields in serializer response (FR-09) ----------------------------

@pytest.mark.django_db
class TestNameFields:
    """The serializer must return human-readable name fields alongside FK ids."""

    def test_list_response_includes_exporter_and_consignee_names(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory()
        resp = auth_client(maker).get(PI_LIST_URL)
        assert resp.status_code == 200
        row = next(r for r in resp.data if r["id"] == pi.pk)
        assert row["exporter_name"] == pi.exporter.name
        assert row["consignee_name"] == pi.consignee.name

    def test_detail_response_includes_all_name_fields(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory()
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200
        assert resp.data["exporter_name"] == pi.exporter.name
        assert resp.data["consignee_name"] == pi.consignee.name
        # buyer_name is null when no buyer is set
        assert resp.data["buyer_name"] is None

    def test_detail_response_buyer_name_when_set(self):
        maker = MakerFactory()
        buyer_org = OrganisationFactory()
        pi = ProformaInvoiceFactory(buyer=buyer_org)
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200
        assert resp.data["buyer_name"] == buyer_org.name

    def test_detail_response_payment_terms_name(self):
        maker = MakerFactory()
        pt = PaymentTermFactory()
        pi = ProformaInvoiceFactory(payment_terms=pt)
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200
        assert resp.data["payment_terms_name"] == pt.name


# ---- INCOTERM_SELLER_FIELDS correctness (FR-09.7) ---------------------------

@pytest.mark.django_db
class TestIncotermSellerFields:
    """
    The serializer's INCOTERM_SELLER_FIELDS must match FR-09.7.3.
    FCA/FOB: no editable cost fields (seller_fields = {}).
    CFR/CPT: freight only.
    CIF/CIP/DAP: freight + insurance.
    """

    def _pi_with_incoterm(self, code):
        incoterm = IncotermFactory(code=code)
        return ProformaInvoiceFactory(incoterms=incoterm)

    def test_fca_invoice_total_equals_grand_total(self):
        """FCA: no seller-borne cost fields → Invoice Total = Grand Total."""
        maker = MakerFactory()
        pi = self._pi_with_incoterm("FCA")
        # Add a line item so grand_total > 0
        ProformaInvoiceLineItemFactory(pi=pi)
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200
        assert resp.data["invoice_total"] == resp.data["grand_total"]

    def test_fob_invoice_total_equals_grand_total(self):
        """FOB: same as FCA."""
        maker = MakerFactory()
        pi = self._pi_with_incoterm("FOB")
        ProformaInvoiceLineItemFactory(pi=pi)
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200
        assert resp.data["invoice_total"] == resp.data["grand_total"]

    def test_cfr_invoice_total_includes_freight_not_insurance(self):
        """CFR: freight is seller-borne, insurance is NOT (buyer pays)."""
        from apps.proforma_invoice.serializers import INCOTERM_SELLER_FIELDS
        cfr_fields = INCOTERM_SELLER_FIELDS["CFR"]
        assert "freight" in cfr_fields
        assert "insurance_amount" not in cfr_fields

    def test_cpt_invoice_total_includes_freight_not_insurance(self):
        """CPT: same shape as CFR."""
        from apps.proforma_invoice.serializers import INCOTERM_SELLER_FIELDS
        cpt_fields = INCOTERM_SELLER_FIELDS["CPT"]
        assert "freight" in cpt_fields
        assert "insurance_amount" not in cpt_fields

    def test_cif_includes_freight_and_insurance(self):
        from apps.proforma_invoice.serializers import INCOTERM_SELLER_FIELDS
        cif_fields = INCOTERM_SELLER_FIELDS["CIF"]
        assert "freight" in cif_fields
        assert "insurance_amount" in cif_fields
        assert "import_duty" not in cif_fields

    def test_ddp_includes_all_cost_fields(self):
        from apps.proforma_invoice.serializers import INCOTERM_SELLER_FIELDS
        ddp_fields = INCOTERM_SELLER_FIELDS["DDP"]
        assert ddp_fields == {"freight", "insurance_amount", "import_duty", "destination_charges"}

    def test_cfr_invoice_total_computed_correctly(self):
        """CFR PI with freight set → Invoice Total = Grand Total + Freight."""
        from decimal import Decimal
        maker = MakerFactory()
        pi = self._pi_with_incoterm("CFR")
        item = ProformaInvoiceLineItemFactory(pi=pi, quantity=Decimal("2.000"), rate_usd=Decimal("100.00"))
        pi.freight = Decimal("50.00")
        pi.save(update_fields=["freight"])
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200
        # grand_total = 200.00, freight = 50.00 → invoice_total = 250.00
        assert Decimal(resp.data["invoice_total"]) == Decimal("250.00")
        assert Decimal(resp.data["grand_total"]) == Decimal("200.00")


# ---- PDF download (FR-09.6) -------------------------------------------------

@pytest.mark.django_db
class TestPdfDownload:
    """
    PDF download endpoint (FR-09.6, US-05).
    GET /proforma-invoices/{id}/pdf/ — streams PDF in memory; all roles; all statuses.
    """

    def test_maker_can_download_pdf(self):
        """Any authenticated Maker gets a 200 application/pdf response."""
        pi = ProformaInvoiceFactory()
        resp = auth_client(MakerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"

    def test_checker_can_download_pdf(self):
        """Checkers can also download at any status."""
        pi = ProformaInvoiceFactory()
        resp = auth_client(CheckerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"

    def test_unauthenticated_cannot_download_pdf(self):
        """Unauthenticated requests must be rejected."""
        pi = ProformaInvoiceFactory()
        resp = APIClient().get(pi_pdf_url(pi.pk))
        assert resp.status_code == 401

    def test_pdf_response_starts_with_pdf_magic_bytes(self):
        """Response body must be a real PDF file (starts with %PDF)."""
        pi = ProformaInvoiceFactory()
        resp = auth_client(MakerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        body = b"".join(resp.streaming_content)
        assert body.startswith(b"%PDF")

    def test_pdf_filename_matches_pi_number(self):
        """Content-Disposition header must use the PI number as the filename."""
        pi = ProformaInvoiceFactory()
        resp = auth_client(MakerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        assert f"{pi.pi_number}.pdf" in resp["Content-Disposition"]

    def test_draft_pdf_contains_watermark(self):
        """Draft PI → watermark transparency ExtGState (/ca .07) is present
        in the uncompressed page resources dictionary (FR-08.3)."""
        pi = ProformaInvoiceFactory(status=DRAFT)
        resp = auth_client(MakerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        body = b"".join(resp.streaming_content)
        # ReportLab writes the alpha value into the page resource dict as an
        # uncompressed ExtGState entry — reliably detectable in raw PDF bytes.
        assert b"/ca .07" in body

    def test_approved_pdf_has_no_watermark(self):
        """Approved PI → clean PDF; watermark ExtGState must be absent (FR-08.3)."""
        pi = ProformaInvoiceFactory(status=APPROVED)
        resp = auth_client(CheckerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        body = b"".join(resp.streaming_content)
        assert b"/ca .07" not in body

    def test_pdf_downloadable_for_pending_approval_status(self):
        """PDF is accessible at every workflow stage, not just DRAFT (US-05)."""
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        resp = auth_client(CheckerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        body = b"".join(resp.streaming_content)
        assert body.startswith(b"%PDF")
