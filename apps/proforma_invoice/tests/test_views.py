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

from apps.accounts.tests.factories import CheckerFactory, CompanyAdminFactory, MakerFactory, SuperAdminFactory
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

    def test_non_creator_maker_can_update(self):
        """Any MAKER can edit a DRAFT PI regardless of who created it."""
        other_maker = MakerFactory()
        pi = ProformaInvoiceFactory(status=DRAFT)
        resp = auth_client(other_maker).patch(pi_detail_url(pi.pk), {"buyer_order_no": "X"}, format="json")
        assert resp.status_code == 200

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
        ProformaInvoiceLineItemFactory(pi=pi)
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
        ProformaInvoiceLineItemFactory(pi=pi)
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
        ProformaInvoiceLineItemFactory(pi=pi)
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
        """Draft PI → watermark transparency ExtGState (/ca .15) is present
        in the uncompressed page resources dictionary (FR-08.3)."""
        pi = ProformaInvoiceFactory(status=DRAFT)
        resp = auth_client(MakerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        body = b"".join(resp.streaming_content)
        # ReportLab writes the alpha value into the page resource dict as an
        # uncompressed ExtGState entry — reliably detectable in raw PDF bytes.
        assert b"/ca .15" in body

    def test_approved_pdf_has_no_watermark(self):
        """Approved PI → clean PDF; watermark ExtGState must be absent (FR-08.3)."""
        pi = ProformaInvoiceFactory(status=APPROVED)
        resp = auth_client(CheckerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        body = b"".join(resp.streaming_content)
        assert b"/ca .15" not in body

    def test_pdf_downloadable_for_pending_approval_status(self):
        """PDF is accessible at every workflow stage, not just DRAFT (US-05)."""
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        resp = auth_client(CheckerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        body = b"".join(resp.streaming_content)
        assert body.startswith(b"%PDF")


# ============================================================================
# NEW TESTS — COMPREHENSIVE COVERAGE EXTENSION
# Organised by layer to match the test matrix agreed before implementation.
# ============================================================================


# ---- Layer 2: Company Admin permissions -------------------------------------

@pytest.mark.django_db
class TestCompanyAdminPermissions:
    """Company Admin can do everything a Maker can, plus edit any PI regardless of creator."""

    def _payload(self):
        return {
            "exporter": OrganisationFactory().pk,
            "consignee": OrganisationFactory().pk,
        }

    def test_admin_can_list_pis(self):
        admin = CompanyAdminFactory()
        ProformaInvoiceFactory.create_batch(2)
        resp = auth_client(admin).get(PI_LIST_URL)
        assert resp.status_code == 200

    def test_admin_can_create_pi(self):
        admin = CompanyAdminFactory()
        resp = auth_client(admin).post(PI_LIST_URL, self._payload(), format="json")
        assert resp.status_code == 201
        assert resp.data["status"] == DRAFT

    def test_admin_can_retrieve_pi(self):
        admin = CompanyAdminFactory()
        pi = ProformaInvoiceFactory()
        resp = auth_client(admin).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200

    def test_admin_can_update_pi_created_by_another_user(self):
        """Company Admin can edit any PI regardless of who created it (views.py:84)."""
        admin = CompanyAdminFactory()
        pi = ProformaInvoiceFactory(status=DRAFT)   # created by a Maker, not the admin
        resp = auth_client(admin).patch(
            pi_detail_url(pi.pk), {"buyer_order_no": "ADMIN-UPDATE"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.data["buyer_order_no"] == "ADMIN-UPDATE"

    def test_checker_cannot_update_draft_pi(self):
        """Checker has read-only access to content fields (views.py:84)."""
        checker = CheckerFactory()
        pi = ProformaInvoiceFactory(status=DRAFT)
        resp = auth_client(checker).patch(
            pi_detail_url(pi.pk), {"buyer_order_no": "CHECKER-EDIT"}, format="json"
        )
        assert resp.status_code == 403

    def test_admin_can_add_line_item_to_any_pi(self):
        """Company Admin can add line items to a PI they did not create (views.py:205)."""
        admin = CompanyAdminFactory()
        pi = ProformaInvoiceFactory(status=DRAFT)
        payload = {"description": "Admin Item", "quantity": "5.000", "rate_usd": "100.00"}
        resp = auth_client(admin).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 201

    def test_other_maker_can_add_line_item(self):
        """Any MAKER can add line items to a DRAFT PI they did NOT create."""
        other_maker = MakerFactory()
        pi = ProformaInvoiceFactory(status=DRAFT)   # created by a different Maker
        payload = {"description": "Shared Item", "quantity": "1.000", "rate_usd": "10.00"}
        resp = auth_client(other_maker).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 201

    def test_other_maker_can_add_charge(self):
        """Any MAKER can add charges to a DRAFT PI they did NOT create."""
        other_maker = MakerFactory()
        pi = ProformaInvoiceFactory(status=DRAFT)
        payload = {"description": "Shared Charge", "amount_usd": "50.00"}
        resp = auth_client(other_maker).post(pi_charge_url(pi.pk), payload, format="json")
        assert resp.status_code == 201

    def test_admin_can_download_pdf(self):
        pi = ProformaInvoiceFactory()
        resp = auth_client(CompanyAdminFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"

    def test_unauthenticated_cannot_create(self):
        resp = APIClient().post(PI_LIST_URL, self._payload(), format="json")
        assert resp.status_code == 401


# ---- Layer 3: Workflow state machine (complete graph) -----------------------

@pytest.mark.django_db
class TestWorkflowStateMachineExtended:

    def test_submit_with_zero_line_items_is_blocked(self):
        """
        A PI with no line items cannot be submitted for approval.
        Requirement: requirements.md §13.2.1 — "At least one line item must be present."
        NOTE: if this test fails, the submission validation is not yet implemented.
        """
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        # Deliberately do NOT create any line items
        resp = auth_client(maker).post(
            pi_workflow_url(pi.pk), {"action": "SUBMIT"}, format="json"
        )
        assert resp.status_code == 400

    def test_cannot_submit_from_pending_approval(self):
        """SUBMIT is not a valid action from PENDING_APPROVAL (PI_TRANSITIONS)."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=PENDING_APPROVAL)
        resp = auth_client(maker).post(
            pi_workflow_url(pi.pk), {"action": "SUBMIT"}, format="json"
        )
        assert resp.status_code == 400

    def test_full_rework_cycle(self):
        """DRAFT → PENDING_APPROVAL → REWORK → PENDING_APPROVAL → APPROVED (FR-08.2)."""
        maker = MakerFactory()
        checker = CheckerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        ProformaInvoiceLineItemFactory(pi=pi)

        # Maker submits
        resp = auth_client(maker).post(
            pi_workflow_url(pi.pk), {"action": "SUBMIT"}, format="json"
        )
        assert resp.data["status"] == PENDING_APPROVAL

        # Checker sends back for rework
        resp = auth_client(checker).post(
            pi_workflow_url(pi.pk),
            {"action": "REWORK", "comment": "Fix the item description."},
            format="json",
        )
        assert resp.data["status"] == REWORK

        # Maker edits in REWORK state
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"buyer_order_no": "REVISED-BO-001"}, format="json"
        )
        assert resp.status_code == 200

        # Maker resubmits
        resp = auth_client(maker).post(
            pi_workflow_url(pi.pk), {"action": "SUBMIT"}, format="json"
        )
        assert resp.data["status"] == PENDING_APPROVAL

        # Checker approves
        resp = auth_client(checker).post(
            pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json"
        )
        assert resp.data["status"] == APPROVED

    def test_checker_cannot_approve_directly_from_rework(self):
        """Checker cannot approve a REWORK PI — Maker must resubmit first (FR-08.2)."""
        pi = ProformaInvoiceFactory(status=REWORK)
        resp = auth_client(CheckerFactory()).post(
            pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json"
        )
        assert resp.status_code == 400

    def test_company_admin_can_approve_pending_pi(self):
        """Company Admin can approve a PI they did not create (workflow constants)."""
        admin = CompanyAdminFactory()
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=PENDING_APPROVAL)
        resp = auth_client(admin).post(
            pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.data["status"] == APPROVED

    def test_permanently_reject_from_approved_state(self):
        """Checker can permanently reject even an Approved PI (PI_TRANSITIONS)."""
        pi = ProformaInvoiceFactory(status=APPROVED)
        resp = auth_client(CheckerFactory()).post(
            pi_workflow_url(pi.pk),
            {"action": "PERMANENTLY_REJECT", "comment": "Recalled post-approval."},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["status"] == PERMANENTLY_REJECTED

    def test_permanently_reject_from_rework_state(self):
        """Checker can permanently reject a PI in REWORK state."""
        pi = ProformaInvoiceFactory(status=REWORK)
        resp = auth_client(CheckerFactory()).post(
            pi_workflow_url(pi.pk),
            {"action": "PERMANENTLY_REJECT", "comment": "Unrecoverable issues."},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["status"] == PERMANENTLY_REJECTED

    def test_permanently_rejected_blocks_all_further_transitions(self):
        """Once PERMANENTLY_REJECTED no further actions are accepted (terminal state)."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=PERMANENTLY_REJECTED)
        resp = auth_client(maker).post(
            pi_workflow_url(pi.pk), {"action": "SUBMIT"}, format="json"
        )
        assert resp.status_code == 400

    def test_maker_cannot_permanently_reject(self):
        """Maker role is not allowed to permanently reject documents."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=PENDING_APPROVAL)
        resp = auth_client(maker).post(
            pi_workflow_url(pi.pk),
            {"action": "PERMANENTLY_REJECT", "comment": "Maker trying to reject."},
            format="json",
        )
        assert resp.status_code == 403

    def test_audit_log_records_rework_comment(self):
        """The comment entered on REWORK must appear verbatim in the audit log."""
        from apps.workflow.models import AuditLog
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        comment_text = "Quantities do not match the purchase order."
        auth_client(CheckerFactory()).post(
            pi_workflow_url(pi.pk),
            {"action": "REWORK", "comment": comment_text},
            format="json",
        )
        log = AuditLog.objects.filter(
            document_type="proforma_invoice",
            document_id=pi.pk,
            action="REWORK",
        ).first()
        assert log is not None
        assert log.comment == comment_text

    def test_permanently_rejected_pi_cascades_to_linked_pl(self):
        """
        Permanently rejecting a PI must cascade to all linked Packing Lists
        (constraint #13 / WorkflowService._cascade_permanently_rejected).
        """
        from apps.packing_list.tests.factories import PackingListFactory
        from apps.packing_list.models import PackingList

        pi = ProformaInvoiceFactory(status=APPROVED)
        pl = PackingListFactory(proforma_invoice=pi, status=DRAFT)

        auth_client(CheckerFactory()).post(
            pi_workflow_url(pi.pk),
            {"action": "PERMANENTLY_REJECT", "comment": "Fraud detected."},
            format="json",
        )
        pl.refresh_from_db()
        assert pl.status == PERMANENTLY_REJECTED

    def test_workflow_missing_action_field_returns_400(self):
        """Calling /workflow/ with an empty body returns a validation error."""
        pi = ProformaInvoiceFactory(status=DRAFT)
        resp = auth_client(pi.created_by).post(
            pi_workflow_url(pi.pk), {}, format="json"
        )
        assert resp.status_code == 400

    def test_full_audit_trail_after_multiple_transitions(self):
        """Multiple transitions should each produce a separate AuditLog entry."""
        from apps.workflow.models import AuditLog
        maker = MakerFactory()
        checker = CheckerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        ProformaInvoiceLineItemFactory(pi=pi)

        auth_client(maker).post(pi_workflow_url(pi.pk), {"action": "SUBMIT"}, format="json")
        auth_client(checker).post(
            pi_workflow_url(pi.pk),
            {"action": "REWORK", "comment": "Fix it."},
            format="json",
        )
        auth_client(maker).post(pi_workflow_url(pi.pk), {"action": "SUBMIT"}, format="json")
        auth_client(checker).post(pi_workflow_url(pi.pk), {"action": "APPROVE"}, format="json")

        logs = AuditLog.objects.filter(document_type="proforma_invoice", document_id=pi.pk)
        # 4 transitions → 4 audit log entries
        assert logs.count() == 4
        actions = list(logs.values_list("action", flat=True))
        assert "SUBMIT" in actions
        assert "REWORK" in actions
        assert "APPROVE" in actions


# ---- Layer 3 + 4: REWORK state editability ----------------------------------

@pytest.mark.django_db
class TestReworkStateEditability:

    def test_maker_can_edit_pi_header_in_rework_state(self):
        """REWORK is in EDITABLE_STATES — Maker can PATCH content fields."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=REWORK)
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"buyer_order_no": "REWORK-FIX"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.data["buyer_order_no"] == "REWORK-FIX"

    def test_maker_can_add_line_item_to_rework_pi(self):
        """Line items can be added when PI is in REWORK state."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=REWORK)
        payload = {"description": "Rework Item", "quantity": "3.000", "rate_usd": "75.00"}
        resp = auth_client(maker).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 201

    def test_maker_can_add_charge_to_rework_pi(self):
        """Charges can be added when PI is in REWORK state."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=REWORK)
        payload = {"description": "Revised Handling Fee", "amount_usd": "200.00"}
        resp = auth_client(maker).post(pi_charge_url(pi.pk), payload, format="json")
        assert resp.status_code == 201

    def test_pending_approval_pi_cannot_be_edited(self):
        """PENDING_APPROVAL is not in EDITABLE_STATES — PATCH returns 400."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=PENDING_APPROVAL)
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"buyer_order_no": "SHOULD-FAIL"}, format="json"
        )
        assert resp.status_code == 400

    def test_permanently_rejected_pi_cannot_be_edited(self):
        """PERMANENTLY_REJECTED is not in EDITABLE_STATES — PATCH returns 400."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=PERMANENTLY_REJECTED)
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"buyer_order_no": "SHOULD-FAIL"}, format="json"
        )
        assert resp.status_code == 400


# ---- Layer 4: Line items — CRUD in all states -------------------------------

@pytest.mark.django_db
class TestLineItemExtendedCoverage:

    def test_list_line_items_returns_all_items_for_pi(self):
        """GET /line-items/ returns all line items belonging to the PI."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        ProformaInvoiceLineItemFactory.create_batch(3, pi=pi)
        resp = auth_client(maker).get(pi_line_item_url(pi.pk))
        assert resp.status_code == 200
        assert len(resp.data) == 3

    def test_put_replaces_line_item(self):
        """PUT updates all fields including recomputing amount_usd."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        item = ProformaInvoiceLineItemFactory(pi=pi)
        resp = auth_client(maker).put(
            pi_line_item_detail_url(pi.pk, item.pk),
            {"description": "Updated Description", "quantity": "20.000", "rate_usd": "25.00"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["description"] == "Updated Description"
        # 20 × 25 = 500
        assert Decimal(resp.data["amount_usd"]) == Decimal("500.00")

    def test_patch_updates_line_item_partially(self):
        """PATCH recomputes amount_usd after a quantity change."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        item = ProformaInvoiceLineItemFactory(
            pi=pi, quantity=Decimal("10.000"), rate_usd=Decimal("50.00")
        )
        resp = auth_client(maker).patch(
            pi_line_item_detail_url(pi.pk, item.pk),
            {"quantity": "15.000"},
            format="json",
        )
        assert resp.status_code == 200
        # 15 × 50 = 750
        assert Decimal(resp.data["amount_usd"]) == Decimal("750.00")

    def test_checker_cannot_update_line_item(self):
        """Checkers have read-only access to content — cannot PATCH line items."""
        pi = ProformaInvoiceFactory(status=DRAFT)
        item = ProformaInvoiceLineItemFactory(pi=pi)
        resp = auth_client(CheckerFactory()).patch(
            pi_line_item_detail_url(pi.pk, item.pk),
            {"quantity": "5.000"},
            format="json",
        )
        assert resp.status_code == 403

    def test_cannot_add_line_item_to_pending_approval_pi(self):
        """PENDING_APPROVAL is not an editable state — POST to /line-items/ returns 400."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=PENDING_APPROVAL)
        payload = {"description": "X", "quantity": "1.000", "rate_usd": "10.00"}
        resp = auth_client(maker).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 400

    def test_cannot_delete_line_item_from_approved_pi(self):
        """Deleting a line item from an APPROVED PI is blocked."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=APPROVED)
        item = ProformaInvoiceLineItemFactory(pi=pi)
        resp = auth_client(maker).delete(pi_line_item_detail_url(pi.pk, item.pk))
        assert resp.status_code == 400

    def test_cannot_add_line_item_to_permanently_rejected_pi(self):
        """PERMANENTLY_REJECTED is a terminal state — no modifications allowed."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=PERMANENTLY_REJECTED)
        payload = {"description": "X", "quantity": "1.000", "rate_usd": "10.00"}
        resp = auth_client(maker).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 400

    def test_zero_quantity_rejected(self):
        """Quantity must be > 0 (serializer validate_quantity)."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        payload = {"description": "X", "quantity": "0.000", "rate_usd": "10.00"}
        resp = auth_client(maker).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 400

    def test_negative_rate_rejected(self):
        """Rate must be >= 0 (serializer validate_rate_usd)."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        payload = {"description": "X", "quantity": "1.000", "rate_usd": "-10.00"}
        resp = auth_client(maker).post(pi_line_item_url(pi.pk), payload, format="json")
        assert resp.status_code == 400

    def test_amount_usd_recalculated_on_patch(self):
        """After PATCH, amount_usd on the DB record reflects the new rate."""
        from apps.proforma_invoice.models import ProformaInvoiceLineItem
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        item = ProformaInvoiceLineItemFactory(
            pi=pi, quantity=Decimal("5.000"), rate_usd=Decimal("100.00")
        )
        auth_client(maker).patch(
            pi_line_item_detail_url(pi.pk, item.pk),
            {"rate_usd": "200.00"},
            format="json",
        )
        item.refresh_from_db()
        assert item.amount_usd == Decimal("1000.00")  # 5 × 200


# ---- Layer 4: Charges — CRUD in all states ----------------------------------

@pytest.mark.django_db
class TestChargesExtendedCoverage:

    def test_list_charges_returns_all_charges_for_pi(self):
        """GET /charges/ returns all charges belonging to the PI."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        ProformaInvoiceChargeFactory.create_batch(2, pi=pi)
        resp = auth_client(maker).get(pi_charge_url(pi.pk))
        assert resp.status_code == 200
        assert len(resp.data) == 2

    def test_put_replaces_charge(self):
        """PUT updates all fields of a charge row."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        charge = ProformaInvoiceChargeFactory(pi=pi)
        resp = auth_client(maker).put(
            pi_charge_detail_url(pi.pk, charge.pk),
            {"description": "Revised Handling Fee", "amount_usd": "250.00"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["description"] == "Revised Handling Fee"
        assert Decimal(resp.data["amount_usd"]) == Decimal("250.00")

    def test_patch_updates_charge_amount_only(self):
        """PATCH allows updating only amount_usd, keeping description intact."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        charge = ProformaInvoiceChargeFactory(pi=pi, description="Inspection Fee")
        resp = auth_client(maker).patch(
            pi_charge_detail_url(pi.pk, charge.pk),
            {"amount_usd": "999.00"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["description"] == "Inspection Fee"
        assert Decimal(resp.data["amount_usd"]) == Decimal("999.00")

    def test_cannot_add_charge_to_pending_approval_pi(self):
        """Charges cannot be added when PI is in PENDING_APPROVAL."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=PENDING_APPROVAL)
        payload = {"description": "Late Fee", "amount_usd": "50.00"}
        resp = auth_client(maker).post(pi_charge_url(pi.pk), payload, format="json")
        assert resp.status_code == 400

    def test_cannot_delete_charge_from_approved_pi(self):
        """Charges cannot be deleted from an APPROVED PI."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=APPROVED)
        charge = ProformaInvoiceChargeFactory(pi=pi)
        resp = auth_client(maker).delete(pi_charge_detail_url(pi.pk, charge.pk))
        assert resp.status_code == 400

    def test_negative_charge_amount_rejected(self):
        """Charge amounts cannot be negative (serializer validate_amount_usd)."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        payload = {"description": "Negative Fee", "amount_usd": "-10.00"}
        resp = auth_client(maker).post(pi_charge_url(pi.pk), payload, format="json")
        assert resp.status_code == 400


# ---- Layer 5: Incoterm cost-field validation (FR-09.7.8) --------------------

@pytest.mark.django_db
class TestIncotermCostFieldValidation:
    """
    On UPDATE, seller-borne cost fields may not be explicitly set to null.
    The serializer validate() only fires when the field is present in the request body.
    """

    def _draft_pi_with_incoterm(self, maker, code):
        incoterm = IncotermFactory(code=code)
        return ProformaInvoiceFactory(created_by=maker, status=DRAFT, incoterms=incoterm)

    def test_patch_cif_freight_to_null_fails(self):
        """CIF requires freight — explicitly setting it to null must return 400."""
        maker = MakerFactory()
        pi = self._draft_pi_with_incoterm(maker, "CIF")
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"freight": None}, format="json"
        )
        assert resp.status_code == 400

    def test_patch_cif_insurance_to_null_fails(self):
        """CIF requires insurance_amount — explicitly setting it to null must return 400."""
        maker = MakerFactory()
        pi = self._draft_pi_with_incoterm(maker, "CIF")
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"insurance_amount": None}, format="json"
        )
        assert resp.status_code == 400

    def test_patch_cfr_freight_to_null_fails(self):
        """CFR requires freight."""
        maker = MakerFactory()
        pi = self._draft_pi_with_incoterm(maker, "CFR")
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"freight": None}, format="json"
        )
        assert resp.status_code == 400

    def test_patch_ddp_import_duty_to_null_fails(self):
        """DDP requires import_duty."""
        maker = MakerFactory()
        pi = self._draft_pi_with_incoterm(maker, "DDP")
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"import_duty": None}, format="json"
        )
        assert resp.status_code == 400

    def test_patch_ddp_destination_charges_to_null_fails(self):
        """DDP requires destination_charges."""
        maker = MakerFactory()
        pi = self._draft_pi_with_incoterm(maker, "DDP")
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"destination_charges": None}, format="json"
        )
        assert resp.status_code == 400

    def test_cost_fields_not_required_on_create(self):
        """Cost-field validation only fires on UPDATE, never on CREATE (serializers.py:200)."""
        maker = MakerFactory()
        cif = IncotermFactory(code="CIF")
        resp = auth_client(maker).post(
            PI_LIST_URL,
            {
                "exporter": OrganisationFactory().pk,
                "consignee": OrganisationFactory().pk,
                "incoterms": cif.pk,
                # No freight or insurance_amount — must still succeed on create
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_exw_freight_null_is_accepted(self):
        """EXW has no seller-borne cost fields — setting freight to null is valid."""
        maker = MakerFactory()
        pi = self._draft_pi_with_incoterm(maker, "EXW")
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"freight": None}, format="json"
        )
        assert resp.status_code == 200

    def test_fob_freight_null_is_accepted(self):
        """FOB buyer bears freight — null freight is valid for this incoterm."""
        maker = MakerFactory()
        pi = self._draft_pi_with_incoterm(maker, "FOB")
        resp = auth_client(maker).patch(
            pi_detail_url(pi.pk), {"freight": None}, format="json"
        )
        assert resp.status_code == 200


# ---- Layer 5: Incoterm computed totals (remaining incoterms) ----------------

@pytest.mark.django_db
class TestIncotermComputedTotalsExtended:

    def test_no_incoterm_invoice_total_equals_grand_total(self):
        """When no incoterm is set, Invoice Total = Grand Total (serializers.py:277)."""
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker, status=DRAFT, incoterms=None)
        ProformaInvoiceLineItemFactory(pi=pi, quantity=Decimal("1.000"), rate_usd=Decimal("500.00"))
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        assert Decimal(resp.data["invoice_total"]) == Decimal(resp.data["grand_total"])

    def test_dap_invoice_total_includes_freight_and_insurance(self):
        """DAP: freight + insurance added to Grand Total."""
        maker = MakerFactory()
        dap = IncotermFactory(code="DAP")
        pi = ProformaInvoiceFactory(
            created_by=maker, status=DRAFT, incoterms=dap,
            freight=Decimal("100.00"), insurance_amount=Decimal("30.00"),
        )
        ProformaInvoiceLineItemFactory(pi=pi, quantity=Decimal("1.000"), rate_usd=Decimal("500.00"))
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        # grand_total=500, freight=100, insurance=30 → invoice_total=630
        assert Decimal(resp.data["invoice_total"]) == Decimal("630.00")
        assert Decimal(resp.data["grand_total"]) == Decimal("500.00")

    def test_dpu_invoice_total_includes_freight_insurance_destination(self):
        """DPU: freight + insurance + destination charges added to Grand Total."""
        maker = MakerFactory()
        dpu = IncotermFactory(code="DPU")
        pi = ProformaInvoiceFactory(
            created_by=maker, status=DRAFT, incoterms=dpu,
            freight=Decimal("80.00"),
            insurance_amount=Decimal("20.00"),
            destination_charges=Decimal("50.00"),
        )
        ProformaInvoiceLineItemFactory(pi=pi, quantity=Decimal("2.000"), rate_usd=Decimal("200.00"))
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        # grand_total=400, freight=80, insurance=20, dest=50 → invoice_total=550
        assert Decimal(resp.data["invoice_total"]) == Decimal("550.00")

    def test_ddp_invoice_total_includes_all_four_cost_fields(self):
        """DDP: all four cost fields are added to Grand Total."""
        maker = MakerFactory()
        ddp = IncotermFactory(code="DDP")
        pi = ProformaInvoiceFactory(
            created_by=maker, status=DRAFT, incoterms=ddp,
            freight=Decimal("100.00"),
            insurance_amount=Decimal("25.00"),
            import_duty=Decimal("50.00"),
            destination_charges=Decimal("40.00"),
        )
        ProformaInvoiceLineItemFactory(pi=pi, quantity=Decimal("1.000"), rate_usd=Decimal("1000.00"))
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        # grand_total=1000, costs=215 → invoice_total=1215
        assert Decimal(resp.data["invoice_total"]) == Decimal("1215.00")

    def test_cip_invoice_total_same_shape_as_cif(self):
        """CIP: freight + insurance (identical field set to CIF)."""
        maker = MakerFactory()
        cip = IncotermFactory(code="CIP")
        pi = ProformaInvoiceFactory(
            created_by=maker, status=DRAFT, incoterms=cip,
            freight=Decimal("60.00"), insurance_amount=Decimal("15.00"),
        )
        ProformaInvoiceLineItemFactory(pi=pi, quantity=Decimal("1.000"), rate_usd=Decimal("300.00"))
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        # grand_total=300, freight=60, insurance=15 → invoice_total=375
        assert Decimal(resp.data["invoice_total"]) == Decimal("375.00")

    def test_invoice_total_excludes_null_cost_fields(self):
        """A seller-borne field that is None (not yet entered) is excluded from the total."""
        maker = MakerFactory()
        cif = IncotermFactory(code="CIF")
        pi = ProformaInvoiceFactory(
            created_by=maker, status=DRAFT, incoterms=cif,
            freight=Decimal("100.00"),
            insurance_amount=None,   # not yet entered
        )
        ProformaInvoiceLineItemFactory(pi=pi, quantity=Decimal("1.000"), rate_usd=Decimal("500.00"))
        resp = auth_client(maker).get(pi_detail_url(pi.pk))
        # grand_total=500, freight=100, insurance excluded → invoice_total=600
        assert Decimal(resp.data["invoice_total"]) == Decimal("600.00")


# ---- Layer 7: T&C template snapshot (FR-09.4 / serializers.py:224) ---------

@pytest.mark.django_db
class TestTCTemplateSnapshot:

    def test_tc_content_snapshotted_from_template_on_create(self):
        """
        When a T&C Template is selected on PI create, its body is copied into
        tc_content on the PI record immediately (point-in-time snapshot).
        """
        from apps.master_data.tests.factories import TCTemplateFactory
        maker = MakerFactory()
        template = TCTemplateFactory(body="<p>Confidential terms.</p>")
        resp = auth_client(maker).post(
            PI_LIST_URL,
            {
                "exporter": OrganisationFactory().pk,
                "consignee": OrganisationFactory().pk,
                "tc_template": template.pk,
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["tc_content"] == "<p>Confidential terms.</p>"

    def test_template_edit_does_not_update_existing_snapshot(self):
        """
        Editing the TCTemplate body after PI creation must NOT change the PI's
        tc_content — it is a frozen snapshot, not a live reference.
        """
        from apps.master_data.tests.factories import TCTemplateFactory
        maker = MakerFactory()
        template = TCTemplateFactory(body="<p>Original terms.</p>")
        pi = ProformaInvoiceFactory(
            created_by=maker,
            status=DRAFT,
            tc_template=template,
            tc_content="<p>Original terms.</p>",
        )
        # Mutate the template after the PI was created
        template.body = "<p>Updated terms that should NOT propagate.</p>"
        template.save()

        pi.refresh_from_db()
        assert pi.tc_content == "<p>Original terms.</p>"

    def test_create_without_template_has_empty_tc_content(self):
        """If no T&C Template is supplied at create, tc_content defaults to ''."""
        maker = MakerFactory()
        resp = auth_client(maker).post(
            PI_LIST_URL,
            {
                "exporter": OrganisationFactory().pk,
                "consignee": OrganisationFactory().pk,
                # No tc_template supplied
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["tc_content"] == ""


# ---- Layer 7: List filtering and ordering (constraint #19) ------------------

@pytest.mark.django_db
class TestListFilteringAndOrdering:

    def test_filter_by_created_by_returns_only_that_makers_pis(self):
        """?created_by=<id> returns only PIs created by that user."""
        maker1 = MakerFactory()
        maker2 = MakerFactory()
        ProformaInvoiceFactory.create_batch(2, created_by=maker1)
        ProformaInvoiceFactory.create_batch(3, created_by=maker2)
        resp = auth_client(maker1).get(PI_LIST_URL, {"created_by": maker1.pk})
        assert resp.status_code == 200
        assert all(pi["created_by"] == maker1.pk for pi in resp.data)
        assert len(resp.data) == 2

    def test_filter_by_status_returns_only_matching_pis(self):
        """?status=APPROVED returns only APPROVED PIs."""
        maker = MakerFactory()
        ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        ProformaInvoiceFactory(created_by=maker, status=APPROVED)
        ProformaInvoiceFactory(created_by=maker, status=PENDING_APPROVAL)
        resp = auth_client(maker).get(PI_LIST_URL, {"status": APPROVED})
        assert resp.status_code == 200
        assert all(pi["status"] == APPROVED for pi in resp.data)

    def test_ordering_parameter_accepted_without_error(self):
        """All declared ordering_fields are accepted by the API without error."""
        maker = MakerFactory()
        ProformaInvoiceFactory.create_batch(2, created_by=maker)
        for ordering in ["created_at", "-created_at", "pi_number", "-pi_number"]:
            resp = auth_client(maker).get(PI_LIST_URL, {"ordering": ordering})
            assert resp.status_code == 200, f"ordering={ordering} returned {resp.status_code}"

    def test_combined_filter_and_ordering(self):
        """status filter and ordering can be combined in a single request."""
        maker = MakerFactory()
        ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        ProformaInvoiceFactory(created_by=maker, status=DRAFT)
        resp = auth_client(maker).get(PI_LIST_URL, {"status": DRAFT, "ordering": "pi_number"})
        assert resp.status_code == 200
        assert all(pi["status"] == DRAFT for pi in resp.data)


# ---- Layer 6: PDF content spot checks ---------------------------------------

@pytest.mark.django_db
class TestPdfContentSpotChecks:

    def test_rework_pdf_has_draft_watermark(self):
        """FR-08.3: REWORK state PDF must carry the DRAFT watermark."""
        pi = ProformaInvoiceFactory(status=REWORK)
        resp = auth_client(MakerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        body = b"".join(resp.streaming_content)
        assert b"/ca .15" in body

    def test_pending_approval_pdf_has_draft_watermark(self):
        """FR-08.3: PENDING_APPROVAL PDF also carries the DRAFT watermark."""
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL)
        resp = auth_client(CheckerFactory()).get(pi_pdf_url(pi.pk))
        assert resp.status_code == 200
        body = b"".join(resp.streaming_content)
        assert b"/ca .15" in body

    def test_company_admin_can_download_pdf_at_any_status(self):
        """Company Admin is an authorised role for PDF download at every status."""
        for doc_status in [DRAFT, PENDING_APPROVAL, APPROVED, REWORK]:
            pi = ProformaInvoiceFactory(status=doc_status)
            resp = auth_client(CompanyAdminFactory()).get(pi_pdf_url(pi.pk))
            assert resp.status_code == 200, f"Failed for status={doc_status}"
            assert resp["Content-Type"] == "application/pdf"

    def test_pdf_body_is_non_trivial_size(self):
        """The streamed PDF must be larger than 1 KB — guards against empty responses."""
        pi = ProformaInvoiceFactory(status=DRAFT)
        ProformaInvoiceLineItemFactory(pi=pi)
        resp = auth_client(MakerFactory()).get(pi_pdf_url(pi.pk))
        body = b"".join(resp.streaming_content)
        assert len(body) > 1024


# ---- Signed copy: re-upload overwrites previous file -----------------------

@pytest.mark.django_db
class TestSignedCopyReupload:

    def test_reupload_replaces_previous_signed_copy(self):
        """
        Uploading a new signed copy for an already-uploaded PI replaces the
        old file (views.py:161 — pi.signed_copy.delete(save=False) before save).
        """
        pi = ProformaInvoiceFactory(status=APPROVED)
        maker = MakerFactory()
        client = auth_client(maker)

        file_1 = SimpleUploadedFile(
            "first.pdf", b"%PDF-1.4 first file", content_type="application/pdf"
        )
        client.post(pi_signed_copy_url(pi.pk), {"file": file_1}, format="multipart")

        file_2 = SimpleUploadedFile(
            "second.pdf", b"%PDF-1.4 second file", content_type="application/pdf"
        )
        resp = client.post(pi_signed_copy_url(pi.pk), {"file": file_2}, format="multipart")
        assert resp.status_code == 200
        assert resp.data["signed_copy_url"] is not None

        pi.refresh_from_db()
        assert pi.signed_copy.name is not None


@pytest.mark.django_db
class TestSuperAdminProformaInvoicePermissions:
    """SUPER_ADMIN must have the same access as COMPANY_ADMIN on all PI endpoints."""

    def test_super_admin_can_list_pis(self):
        ProformaInvoiceFactory()
        resp = auth_client(SuperAdminFactory()).get(PI_LIST_URL)
        assert resp.status_code == 200

    def test_super_admin_can_retrieve_pi(self):
        pi = ProformaInvoiceFactory()
        resp = auth_client(SuperAdminFactory()).get(pi_detail_url(pi.pk))
        assert resp.status_code == 200

    def test_super_admin_can_hard_delete_pi(self):
        from apps.proforma_invoice.models import ProformaInvoice
        super_admin = SuperAdminFactory()
        pi = ProformaInvoiceFactory()
        resp = auth_client(super_admin).delete(f"/api/v1/proforma-invoices/{pi.pk}/hard-delete/")
        assert resp.status_code == 204
        assert not ProformaInvoice.objects.filter(pk=pi.pk).exists()

    def test_maker_cannot_hard_delete_pi(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker)
        resp = auth_client(maker).delete(f"/api/v1/proforma-invoices/{pi.pk}/hard-delete/")
        assert resp.status_code == 403

    def test_company_admin_cannot_hard_delete_pi(self):
        pi = ProformaInvoiceFactory()
        resp = auth_client(CompanyAdminFactory()).delete(f"/api/v1/proforma-invoices/{pi.pk}/hard-delete/")
        assert resp.status_code == 403

    def test_super_admin_can_create_pi(self):
        """SUPER_ADMIN must be allowed by perform_create (same as Maker / Company Admin)."""
        super_admin = SuperAdminFactory()
        payload = {
            "exporter": OrganisationFactory().pk,
            "consignee": OrganisationFactory().pk,
        }
        resp = auth_client(super_admin).post(PI_LIST_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.data["pi_number"].startswith("PI-")

    def test_super_admin_hard_delete_pi_blocked_when_pl_exists(self):
        """Hard delete returns 400 when a Packing List references the PI (PROTECT constraint)."""
        from apps.packing_list.tests.factories import PackingListFactory
        super_admin = SuperAdminFactory()
        pi = ProformaInvoiceFactory()
        PackingListFactory(proforma_invoice=pi)
        resp = auth_client(super_admin).delete(f"/api/v1/proforma-invoices/{pi.pk}/hard-delete/")
        assert resp.status_code == 400
        assert "Packing List" in str(resp.data)
