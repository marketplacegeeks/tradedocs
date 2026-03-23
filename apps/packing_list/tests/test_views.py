"""
API view tests for PackingList, Container, and ContainerItem endpoints.

Every endpoint has at minimum:
- One happy-path test
- One permission-denial test
"""

import pytest
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CheckerFactory, CompanyAdminFactory, MakerFactory, SuperAdminFactory
from apps.master_data.tests.factories import (
    BankFactory,
    OrganisationFactory,
    UOMFactory,
)
from apps.proforma_invoice.tests.factories import ProformaInvoiceFactory
from apps.workflow.constants import (
    APPROVED, DRAFT, PENDING_APPROVAL, PERMANENTLY_REJECTED, REWORK,
)

from .factories import ContainerFactory, ContainerItemFactory, PackingListFactory


# ---- Helpers ----------------------------------------------------------------

def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


PL_LIST_URL = "/api/v1/packing-lists/"


def pl_detail_url(pk):
    return f"/api/v1/packing-lists/{pk}/"


def pl_workflow_url(pk):
    return f"/api/v1/packing-lists/{pk}/workflow/"


def pl_audit_url(pk):
    return f"/api/v1/packing-lists/{pk}/audit-log/"


def container_list_url():
    return "/api/v1/containers/"


def container_detail_url(pk):
    return f"/api/v1/containers/{pk}/"


def container_copy_url(pk):
    return f"/api/v1/containers/{pk}/copy/"


def item_list_url():
    return "/api/v1/container-items/"


def item_detail_url(pk):
    return f"/api/v1/container-items/{pk}/"


def _approved_pi(maker=None):
    """Create a PI in Approved state (required to create a PL)."""
    from apps.workflow.constants import APPROVED
    pi = ProformaInvoiceFactory(status=APPROVED, created_by=maker or MakerFactory())
    return pi


def _pl_payload(pi, exporter=None, consignee=None, bank=None):
    exporter = exporter or OrganisationFactory()
    consignee = consignee or OrganisationFactory()
    bank = bank or BankFactory()
    return {
        "proforma_invoice": pi.pk,
        "pl_date": "2026-03-19",
        "ci_date": "2026-03-19",
        "exporter": exporter.pk,
        "consignee": consignee.pk,
        "bank": bank.pk,
    }


# ---- Create PL + CI ---------------------------------------------------------

@pytest.mark.django_db
class TestPackingListCreate:

    def test_maker_can_create(self):
        maker = MakerFactory()
        pi = _approved_pi(maker)
        payload = _pl_payload(pi)
        resp = auth_client(maker).post(PL_LIST_URL, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["pl_number"].startswith("PL-")
        assert data["ci_number"].startswith("CI-")
        assert data["status"] == DRAFT

    def test_checker_cannot_create(self):
        checker = CheckerFactory()
        pi = _approved_pi()
        payload = _pl_payload(pi)
        resp = auth_client(checker).post(PL_LIST_URL, payload, format="json")
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create(self):
        pi = _approved_pi()
        payload = _pl_payload(pi)
        resp = APIClient().post(PL_LIST_URL, payload, format="json")
        assert resp.status_code == 401

    def test_cannot_create_from_non_approved_pi(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(status=DRAFT, created_by=maker)
        payload = _pl_payload(pi)
        resp = auth_client(maker).post(PL_LIST_URL, payload, format="json")
        assert resp.status_code == 400
        assert "proforma_invoice" in resp.json()

    def test_create_generates_both_numbers(self):
        maker = MakerFactory()
        pi = _approved_pi(maker)
        payload = _pl_payload(pi)
        resp = auth_client(maker).post(PL_LIST_URL, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        # Both numbers must be unique/sequential
        assert data["pl_number"] != ""
        assert data["ci_number"] != ""


# ---- List -------------------------------------------------------------------

@pytest.mark.django_db
class TestPackingListList:

    def test_all_roles_can_list(self):
        for user in (MakerFactory(), CheckerFactory(), CompanyAdminFactory()):
            resp = auth_client(user).get(PL_LIST_URL)
            assert resp.status_code == 200

    def test_unauthenticated_denied(self):
        resp = APIClient().get(PL_LIST_URL)
        assert resp.status_code == 401

    def test_filter_by_status(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        PackingListFactory(status=PENDING_APPROVAL, created_by=maker)
        resp = auth_client(maker).get(PL_LIST_URL + "?status=DRAFT")
        result = resp.json()
        items = result["results"] if isinstance(result, dict) else result
        pks = [item["id"] for item in items]
        assert pl.pk in pks


# ---- Retrieve ---------------------------------------------------------------

@pytest.mark.django_db
class TestPackingListRetrieve:

    def test_any_role_can_retrieve(self):
        pl = PackingListFactory()
        for user in (MakerFactory(), CheckerFactory(), CompanyAdminFactory()):
            resp = auth_client(user).get(pl_detail_url(pl.pk))
            assert resp.status_code == 200

    def test_retrieve_includes_containers(self):
        pl = PackingListFactory()
        ContainerFactory(packing_list=pl)
        resp = auth_client(pl.created_by).get(pl_detail_url(pl.pk))
        assert resp.status_code == 200
        assert len(resp.json()["containers"]) == 1


# ---- Update (PATCH) ---------------------------------------------------------

@pytest.mark.django_db
class TestPackingListUpdate:

    def test_creator_can_patch_in_draft(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        resp = auth_client(maker).patch(
            pl_detail_url(pl.pk),
            {"vessel_flight_no": "MV TITAN"},
            format="json",
        )
        assert resp.status_code == 200

    def test_non_creator_cannot_patch(self):
        pl = PackingListFactory(status=DRAFT)
        other_maker = MakerFactory()
        resp = auth_client(other_maker).patch(
            pl_detail_url(pl.pk),
            {"vessel_flight_no": "MV TITAN"},
            format="json",
        )
        assert resp.status_code == 403

    def test_cannot_patch_pending_approval(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=PENDING_APPROVAL, created_by=maker)
        resp = auth_client(maker).patch(
            pl_detail_url(pl.pk),
            {"vessel_flight_no": "MV TITAN"},
            format="json",
        )
        assert resp.status_code == 400


# ---- Delete -----------------------------------------------------------------

@pytest.mark.django_db
class TestPackingListDelete:

    def test_creator_can_delete_draft(self):
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        CommercialInvoiceFactory(packing_list=pl, created_by=maker)
        resp = auth_client(maker).delete(pl_detail_url(pl.pk))
        assert resp.status_code == 204

    def test_cannot_delete_pending_approval(self):
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        maker = MakerFactory()
        pl = PackingListFactory(status=PENDING_APPROVAL, created_by=maker)
        CommercialInvoiceFactory(packing_list=pl, created_by=maker)
        resp = auth_client(maker).delete(pl_detail_url(pl.pk))
        assert resp.status_code == 400

    def test_checker_cannot_delete(self):
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        checker = CheckerFactory()
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        CommercialInvoiceFactory(packing_list=pl, created_by=maker)
        resp = auth_client(checker).delete(pl_detail_url(pl.pk))
        assert resp.status_code == 403


# ---- Workflow ---------------------------------------------------------------

@pytest.mark.django_db
class TestPackingListWorkflow:

    def _pl_with_ci(self, status_value=DRAFT, maker=None):
        """Create a PL+CI pair in the given status. Incoterms is required for SUBMIT."""
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        from apps.master_data.tests.factories import IncotermFactory
        maker = maker or MakerFactory()
        pl = PackingListFactory(status=status_value, created_by=maker, incoterms=IncotermFactory())
        CommercialInvoiceFactory(packing_list=pl, status=status_value, created_by=maker)
        return pl, maker

    def test_maker_can_submit(self):
        pl, maker = self._pl_with_ci(DRAFT)
        resp = auth_client(maker).post(
            pl_workflow_url(pl.pk), {"action": "SUBMIT"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == PENDING_APPROVAL
        pl.refresh_from_db()
        assert pl.status == PENDING_APPROVAL
        # CI must also transition.
        pl.commercial_invoice.refresh_from_db()
        assert pl.commercial_invoice.status == PENDING_APPROVAL

    def test_checker_can_approve(self):
        pl, maker = self._pl_with_ci(PENDING_APPROVAL)
        checker = CheckerFactory()
        resp = auth_client(checker).post(
            pl_workflow_url(pl.pk), {"action": "APPROVE"}, format="json"
        )
        assert resp.status_code == 200
        pl.refresh_from_db()
        assert pl.status == APPROVED
        pl.commercial_invoice.refresh_from_db()
        assert pl.commercial_invoice.status == APPROVED

    def test_checker_can_rework_with_comment(self):
        pl, maker = self._pl_with_ci(PENDING_APPROVAL)
        checker = CheckerFactory()
        resp = auth_client(checker).post(
            pl_workflow_url(pl.pk),
            {"action": "REWORK", "comment": "Please fix the quantities."},
            format="json",
        )
        assert resp.status_code == 200
        pl.refresh_from_db()
        assert pl.status == REWORK
        pl.commercial_invoice.refresh_from_db()
        assert pl.commercial_invoice.status == REWORK

    def test_rework_requires_comment(self):
        pl, maker = self._pl_with_ci(PENDING_APPROVAL)
        checker = CheckerFactory()
        resp = auth_client(checker).post(
            pl_workflow_url(pl.pk), {"action": "REWORK", "comment": ""}, format="json"
        )
        assert resp.status_code == 400
        assert "comment" in resp.json()

    def test_maker_cannot_approve(self):
        pl, maker = self._pl_with_ci(PENDING_APPROVAL, maker=MakerFactory())
        other_maker = MakerFactory()
        resp = auth_client(other_maker).post(
            pl_workflow_url(pl.pk), {"action": "APPROVE"}, format="json"
        )
        assert resp.status_code == 403

    def test_maker_cannot_approve_own_document(self):
        """FR-08.2: a Maker who created the document cannot approve it."""
        pl, maker = self._pl_with_ci(PENDING_APPROVAL, maker=MakerFactory())
        resp = auth_client(maker).post(
            pl_workflow_url(pl.pk), {"action": "APPROVE"}, format="json"
        )
        assert resp.status_code == 403

    def test_admin_can_approve_own_document(self):
        """Company Admin who created the document is allowed to approve it."""
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        admin = CompanyAdminFactory()
        pl = PackingListFactory(status=PENDING_APPROVAL, created_by=admin)
        CommercialInvoiceFactory(packing_list=pl, status=PENDING_APPROVAL, created_by=admin)
        resp = auth_client(admin).post(
            pl_workflow_url(pl.pk), {"action": "APPROVE"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.data["status"] == APPROVED

    def test_permanently_reject_from_approved_state(self):
        """FR-08.1: Permanently Reject must be allowed from ANY state including Approved."""
        pl, maker = self._pl_with_ci(APPROVED)
        checker = CheckerFactory()
        resp = auth_client(checker).post(
            pl_workflow_url(pl.pk),
            {"action": "PERMANENTLY_REJECT", "comment": "Found critical error."},
            format="json",
        )
        assert resp.status_code == 200
        pl.refresh_from_db()
        assert pl.status == PERMANENTLY_REJECTED
        pl.commercial_invoice.refresh_from_db()
        assert pl.commercial_invoice.status == PERMANENTLY_REJECTED

    def test_permanently_reject_requires_comment(self):
        pl, maker = self._pl_with_ci(DRAFT)
        checker = CheckerFactory()
        resp = auth_client(checker).post(
            pl_workflow_url(pl.pk),
            {"action": "PERMANENTLY_REJECT", "comment": ""},
            format="json",
        )
        assert resp.status_code == 400

    def test_audit_log_created_for_both_pl_and_ci(self):
        from apps.workflow.models import AuditLog
        pl, maker = self._pl_with_ci(DRAFT)
        checker = CheckerFactory()
        auth_client(maker).post(
            pl_workflow_url(pl.pk), {"action": "SUBMIT"}, format="json"
        )
        pl_logs = AuditLog.objects.filter(document_type="packing_list", document_id=pl.pk)
        ci_logs = AuditLog.objects.filter(
            document_type="commercial_invoice", document_id=pl.commercial_invoice.pk
        )
        assert pl_logs.count() == 1
        assert ci_logs.count() == 1

    # ---- GET audit-log endpoint tests ----------------------------------------

    def test_audit_log_endpoint_returns_entries(self):
        """Happy path: maker submits, then audit-log endpoint returns the entry."""
        pl, maker = self._pl_with_ci(DRAFT)
        auth_client(maker).post(
            pl_workflow_url(pl.pk), {"action": "SUBMIT"}, format="json"
        )
        resp = auth_client(maker).get(pl_audit_url(pl.pk))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        entry = data[0]
        # Must use performed_at + performed_by_name (not created_at / performed_by)
        assert "performed_at" in entry
        assert "performed_by_name" in entry
        assert "created_at" not in entry
        assert entry["action"] == "SUBMIT"
        assert entry["from_status"] == "DRAFT"
        assert entry["to_status"] == "PENDING_APPROVAL"
        assert entry["comment"] == ""

    def test_audit_log_endpoint_empty_before_any_action(self):
        """A freshly created PL has no audit entries (creation isn't a workflow transition)."""
        pl, maker = self._pl_with_ci(DRAFT)
        resp = auth_client(maker).get(pl_audit_url(pl.pk))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_audit_log_entries_ordered_newest_first(self):
        """Multiple transitions must be returned most-recent first."""
        pl, maker = self._pl_with_ci(DRAFT)
        checker = CheckerFactory()
        # SUBMIT → REWORK → SUBMIT (three entries)
        auth_client(maker).post(
            pl_workflow_url(pl.pk), {"action": "SUBMIT"}, format="json"
        )
        auth_client(checker).post(
            pl_workflow_url(pl.pk),
            {"action": "REWORK", "comment": "needs changes"},
            format="json",
        )
        auth_client(maker).post(
            pl_workflow_url(pl.pk), {"action": "SUBMIT"}, format="json"
        )
        resp = auth_client(maker).get(pl_audit_url(pl.pk))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        # Newest entry first — last SUBMIT should be first
        assert data[0]["action"] == "SUBMIT"
        assert data[0]["from_status"] == "REWORK"

    def test_audit_log_endpoint_requires_authentication(self):
        """Unauthenticated request must be denied."""
        from rest_framework.test import APIClient
        pl, _ = self._pl_with_ci(DRAFT)
        resp = APIClient().get(pl_audit_url(pl.pk))
        assert resp.status_code == 401


# ---- Containers -------------------------------------------------------------

@pytest.mark.django_db
class TestContainerCRUD:

    def test_maker_can_add_container(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        payload = {
            "packing_list": pl.pk,
            "container_ref": "CONT001",
            "marks_numbers": "Mark A",
            "seal_number": "SEAL001",
            "tare_weight": "2200.000",
        }
        resp = auth_client(maker).post(container_list_url(), payload, format="json")
        assert resp.status_code == 201

    def test_cannot_add_container_when_pending(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=PENDING_APPROVAL, created_by=maker)
        payload = {
            "packing_list": pl.pk,
            "container_ref": "CONT001",
            "marks_numbers": "Mark A",
            "seal_number": "SEAL001",
            "tare_weight": "2200.000",
        }
        resp = auth_client(maker).post(container_list_url(), payload, format="json")
        assert resp.status_code == 400

    def test_copy_container_duplicates_items(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        container = ContainerFactory(packing_list=pl)
        ContainerItemFactory(container=container)
        ContainerItemFactory(container=container)
        resp = auth_client(maker).post(container_copy_url(container.pk))
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["items"]) == 2
        # Ref, marks, seal should be blank on the copy.
        assert data["container_ref"] == ""
        assert data["marks_numbers"] == ""
        assert data["seal_number"] == ""


# ---- ContainerItems ---------------------------------------------------------

@pytest.mark.django_db
class TestContainerItemCRUD:

    def test_maker_can_add_item(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        container = ContainerFactory(packing_list=pl)
        uom = UOMFactory()
        payload = {
            "container": container.pk,
            "item_code": "ITEM001",
            "packages_kind": "10 Bags",
            "description": "Wheat",
            "uom": uom.pk,
            "quantity": "100.000",
            "net_weight": "95.000",
            "inner_packing_weight": "5.000",
        }
        resp = auth_client(maker).post(item_list_url(), payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        # item_gross_weight must be computed.
        assert Decimal(data["item_gross_weight"]) == Decimal("100.000")

    def test_invalid_hsn_rejected(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        container = ContainerFactory(packing_list=pl)
        uom = UOMFactory()
        payload = {
            "container": container.pk,
            "item_code": "ITEM001",
            "packages_kind": "10 Bags",
            "description": "Wheat",
            "hsn_code": "123",  # 3 digits — invalid
            "uom": uom.pk,
            "quantity": "100.000",
            "net_weight": "95.000",
            "inner_packing_weight": "5.000",
        }
        resp = auth_client(maker).post(item_list_url(), payload, format="json")
        assert resp.status_code == 400

    def test_adding_item_rebuilds_ci_line_items(self):
        """Adding a container item must create a matching CI line item."""
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        from apps.commercial_invoice.models import CommercialInvoiceLineItem
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        ci = CommercialInvoiceFactory(packing_list=pl, created_by=maker)
        container = ContainerFactory(packing_list=pl)
        uom = UOMFactory()
        payload = {
            "container": container.pk,
            "item_code": "ITEM001",
            "packages_kind": "10 Bags",
            "description": "Wheat",
            "uom": uom.pk,
            "quantity": "100.000",
            "net_weight": "95.000",
            "inner_packing_weight": "5.000",
        }
        auth_client(maker).post(item_list_url(), payload, format="json")
        assert CommercialInvoiceLineItem.objects.filter(ci=ci, item_code="ITEM001").exists()


# ---- Signed copy upload — Packing List (FR-08.4) ----------------------------

def pl_signed_copy_url(pk):
    return f"/api/v1/packing-lists/{pk}/signed-copy/"


def _small_pdf():
    """Return a tiny fake PDF file for upload tests."""
    return SimpleUploadedFile("signed.pdf", b"%PDF-1.4 fake content", content_type="application/pdf")


@pytest.mark.django_db
class TestPlSignedCopyUpload:

    def test_upload_succeeds_for_approved_pl(self):
        pl = PackingListFactory(status=APPROVED)
        resp = auth_client(MakerFactory()).post(
            pl_signed_copy_url(pl.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        assert resp.status_code == 200
        assert resp.data["signed_copy_url"] is not None

    def test_upload_blocked_for_draft_pl(self):
        pl = PackingListFactory(status=DRAFT)
        resp = auth_client(MakerFactory()).post(
            pl_signed_copy_url(pl.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        assert resp.status_code == 400

    def test_upload_blocked_for_pending_approval(self):
        pl = PackingListFactory(status=PENDING_APPROVAL)
        resp = auth_client(CheckerFactory()).post(
            pl_signed_copy_url(pl.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        assert resp.status_code == 400

    def test_upload_requires_file_field(self):
        pl = PackingListFactory(status=APPROVED)
        resp = auth_client(MakerFactory()).post(
            pl_signed_copy_url(pl.pk),
            {},  # no file
            format="multipart",
        )
        assert resp.status_code == 400

    def test_upload_rejects_oversized_file(self, settings):
        settings.SIGNED_COPY_MAX_BYTES = 10  # 10 bytes — anything real will exceed this
        pl = PackingListFactory(status=APPROVED)
        resp = auth_client(MakerFactory()).post(
            pl_signed_copy_url(pl.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        assert resp.status_code == 400

    def test_unauthenticated_upload_denied(self):
        pl = PackingListFactory(status=APPROVED)
        resp = APIClient().post(
            pl_signed_copy_url(pl.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        assert resp.status_code == 401

    def test_signed_copy_url_appears_in_detail_response(self):
        """After upload, GET on the PL returns a non-null signed_copy_url."""
        maker = MakerFactory()
        pl = PackingListFactory(status=APPROVED)
        auth_client(maker).post(
            pl_signed_copy_url(pl.pk),
            {"file": _small_pdf()},
            format="multipart",
        )
        resp = auth_client(maker).get(pl_detail_url(pl.pk))
        assert resp.status_code == 200
        assert resp.data["signed_copy_url"] is not None

# ---- Extended coverage: shipping fields, bank propagation, CI rates,
#      references, container validation, copy, final rates, CI aggregation ----

def ci_line_item_detail_url(pk):
    return f"/api/v1/ci-line-items/{pk}/"


def ci_detail_url(pk):
    return f"/api/v1/commercial-invoices/{pk}/"


@pytest.mark.django_db
class TestPlExtendedCoverage:
    """12 tests covering gaps identified in wireframe audit."""

    # ---- 1. Shipping fields saved on create --------------------------------

    def test_create_pl_saves_shipping_fields(self):
        """POST with port_of_loading, port_of_discharge, vessel_flight_no
        should return those values in the response."""
        from apps.master_data.tests.factories import PortFactory
        maker = MakerFactory()
        pi = _approved_pi(maker)
        port_load = PortFactory()
        port_discharge = PortFactory()
        payload = _pl_payload(pi)
        payload.update({
            "port_of_loading": port_load.pk,
            "port_of_discharge": port_discharge.pk,
            "vessel_flight_no": "MV ATLAS",
        })
        resp = auth_client(maker).post(PL_LIST_URL, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["port_of_loading"] == port_load.pk
        assert data["port_of_discharge"] == port_discharge.pk
        assert data["vessel_flight_no"] == "MV ATLAS"

    # ---- 2. Country of final destination saved on create -------------------

    def test_create_pl_saves_country_of_final_destination(self):
        """country_of_final_destination FK should round-trip through create."""
        from apps.master_data.tests.factories import CountryFactory
        maker = MakerFactory()
        pi = _approved_pi(maker)
        country = CountryFactory()
        payload = _pl_payload(pi)
        payload["country_of_final_destination"] = country.pk
        resp = auth_client(maker).post(PL_LIST_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["country_of_final_destination"] == country.pk

    # ---- 3. Bank PATCH propagates to linked CI -----------------------------

    def test_patch_bank_propagates_to_ci(self):
        """PATCH bank on a PL in DRAFT → the linked CI's bank must update."""
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        CommercialInvoiceFactory(packing_list=pl, created_by=maker, bank=None)
        new_bank = BankFactory()
        resp = auth_client(maker).patch(
            pl_detail_url(pl.pk),
            {"bank": new_bank.pk},
            format="json",
        )
        assert resp.status_code == 200
        # Verify the CI now references the same bank
        pl.refresh_from_db()
        pl.commercial_invoice.refresh_from_db()
        assert pl.commercial_invoice.bank_id == new_bank.pk

    # ---- 4. Order references round-trip ------------------------------------

    def test_patch_pl_order_references(self):
        """All reference fields should be patchable and returned correctly."""
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        payload = {
            "po_number": "PO-2026-001",
            "po_date": "2026-01-15",
            "lc_number": "LC/2026/SBI/001",
            "lc_date": "2026-01-20",
            "bl_number": "BL-2026-001",
            "bl_date": "2026-02-01",
            "so_number": "SO-001",
            "so_date": "2026-01-10",
            "other_references": "REF-CUSTOM",
            "other_references_date": "2026-01-05",
            "additional_description": "Extra notes here.",
        }
        resp = auth_client(maker).patch(pl_detail_url(pl.pk), payload, format="json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["po_number"] == "PO-2026-001"
        assert data["lc_number"] == "LC/2026/SBI/001"
        assert data["bl_number"] == "BL-2026-001"
        assert data["so_number"] == "SO-001"
        assert data["other_references"] == "REF-CUSTOM"
        assert data["other_references_date"] == "2026-01-05"

    # ---- 5. CI line item rate_usd update -----------------------------------

    def test_ci_line_item_rate_update(self):
        """PATCH /ci-line-items/{id}/ should update rate_usd and amount_usd."""
        from decimal import Decimal
        from apps.commercial_invoice.tests.factories import (
            CommercialInvoiceFactory,
            CommercialInvoiceLineItemFactory,
        )
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        ci = CommercialInvoiceFactory(packing_list=pl, created_by=maker)
        uom = UOMFactory()
        line = CommercialInvoiceLineItemFactory(ci=ci, uom=uom, total_quantity=Decimal("100.000"), rate_usd=Decimal("0.00"))
        resp = auth_client(maker).patch(
            ci_line_item_detail_url(line.pk),
            {"rate_usd": "500.00"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(data["rate_usd"]) == Decimal("500.00")
        # amount_usd = qty × rate = 100.000 × 500.00
        assert Decimal(data["amount_usd"]) == Decimal("50000.00")

    # ---- 6. Container requires container_ref --------------------------------

    def test_container_create_requires_container_ref(self):
        """POST /containers/ without container_ref → 400."""
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        payload = {
            "packing_list": pl.pk,
            # container_ref intentionally omitted
            "marks_numbers": "MARK-001",
            "seal_number": "SEAL-001",
            "tare_weight": "2200.000",
        }
        resp = auth_client(maker).post(container_list_url(), payload, format="json")
        assert resp.status_code == 400

    # ---- 7. Container requires seal_number ----------------------------------

    def test_container_create_requires_seal_number(self):
        """POST /containers/ without seal_number → 400."""
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        payload = {
            "packing_list": pl.pk,
            "container_ref": "CONT001",
            "marks_numbers": "MARK-001",
            # seal_number intentionally omitted
            "tare_weight": "2200.000",
        }
        resp = auth_client(maker).post(container_list_url(), payload, format="json")
        assert resp.status_code == 400

    # ---- 8. Copy container blanks ref/marks/seal but keeps tare_weight ------

    def test_copy_container_blanks_ref_marks_seal_keeps_tare(self):
        """POST /containers/{id}/copy/ → new container has blank ref/marks/seal
        but tare_weight matches the original."""
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        original = ContainerFactory(
            packing_list=pl,
            container_ref="CONT001",
            marks_numbers="MARK-001",
            seal_number="SEAL-001",
            tare_weight=Decimal("2200.000"),
        )
        resp = auth_client(maker).post(container_copy_url(original.pk))
        assert resp.status_code == 201
        data = resp.json()
        assert data["container_ref"] == ""
        assert data["marks_numbers"] == ""
        assert data["seal_number"] == ""
        assert Decimal(data["tare_weight"]) == Decimal("2200.000")

    # ---- 9. Final rates PATCH on PL (incoterms, payment_terms, fob_rate...) -

    def test_patch_final_rates_on_pl(self):
        """PATCH PL with incoterms, payment_terms, fob_rate, freight, insurance,
        lc_details → all fields saved and returned."""
        from apps.master_data.tests.factories import IncotermFactory, PaymentTermFactory
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        CommercialInvoiceFactory(packing_list=pl, created_by=maker)
        incoterm = IncotermFactory()
        payment_term = PaymentTermFactory()
        payload = {
            "incoterms": incoterm.pk,
            "payment_terms": payment_term.pk,
            "fob_rate": "1250.00",
            "freight": "12000.00",
            "insurance": "1500.00",
            "lc_details": "LC/2026/SBI/00123",
        }
        resp = auth_client(maker).patch(pl_detail_url(pl.pk), payload, format="json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["incoterms"] == incoterm.pk
        assert data["payment_terms"] == payment_term.pk
        # CI fields are returned on the PL response
        assert Decimal(data["fob_rate"]) == Decimal("1250.00")
        assert Decimal(data["freight"]) == Decimal("12000.00")

    # ---- 10. CI aggregation: same item_code+UOM → 1 line item ---------------

    def test_ci_line_items_aggregate_by_item_code_uom(self):
        """Items with the same item_code+UOM across multiple containers must
        produce a single aggregated CI line item."""
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        from apps.commercial_invoice.models import CommercialInvoiceLineItem
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        ci = CommercialInvoiceFactory(packing_list=pl, created_by=maker)
        uom = UOMFactory()
        c1 = ContainerFactory(packing_list=pl)
        c2 = ContainerFactory(packing_list=pl)
        # Same item_code + same uom in both containers → should aggregate
        payload_base = {
            "item_code": "ITEM-AGG",
            "packages_kind": "10 Drums",
            "description": "Castor Oil",
            "uom": uom.pk,
            "quantity": "100.000",
            "net_weight": "100.000",
            "inner_packing_weight": "2.000",
        }
        auth_client(maker).post(item_list_url(), {**payload_base, "container": c1.pk}, format="json")
        auth_client(maker).post(item_list_url(), {**payload_base, "container": c2.pk}, format="json")
        line_items = CommercialInvoiceLineItem.objects.filter(ci=ci, item_code="ITEM-AGG")
        assert line_items.count() == 1
        assert Decimal(line_items.first().total_quantity) == Decimal("200.000")

    # ---- 11. CI aggregation: different UOM → separate line items ------------

    def test_ci_line_items_separate_for_different_uom(self):
        """Same item_code but different UOM must produce 2 separate line items."""
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        from apps.commercial_invoice.models import CommercialInvoiceLineItem
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        ci = CommercialInvoiceFactory(packing_list=pl, created_by=maker)
        uom_a = UOMFactory()
        uom_b = UOMFactory()
        container = ContainerFactory(packing_list=pl)
        base = {
            "container": container.pk,
            "item_code": "ITEM-SPLIT",
            "packages_kind": "10 Drums",
            "description": "Castor Oil",
            "quantity": "50.000",
            "net_weight": "50.000",
            "inner_packing_weight": "1.000",
        }
        auth_client(maker).post(item_list_url(), {**base, "uom": uom_a.pk}, format="json")
        auth_client(maker).post(item_list_url(), {**base, "uom": uom_b.pk}, format="json")
        line_items = CommercialInvoiceLineItem.objects.filter(ci=ci, item_code="ITEM-SPLIT")
        assert line_items.count() == 2

    # ---- 12. Incoterms null is allowed on PATCH -----------------------------

    def test_patch_incoterms_null_allowed(self):
        """PATCH PL with incoterms=null → 200, incoterms field is null."""
        from apps.master_data.tests.factories import IncotermFactory
        maker = MakerFactory()
        pl = PackingListFactory(
            status=DRAFT,
            created_by=maker,
            incoterms=IncotermFactory(),
        )
        resp = auth_client(maker).patch(
            pl_detail_url(pl.pk),
            {"incoterms": None},
            format="json",
        )
        assert resp.status_code == 200
        pl.refresh_from_db()
        assert pl.incoterms is None


@pytest.mark.django_db
class TestSuperAdminPackingListPermissions:
    """SUPER_ADMIN must have the same access as COMPANY_ADMIN on all PL endpoints."""

    def test_super_admin_can_list_pls(self):
        PackingListFactory()
        resp = auth_client(SuperAdminFactory()).get(PL_LIST_URL)
        assert resp.status_code == 200

    def test_super_admin_can_retrieve_pl(self):
        pl = PackingListFactory()
        resp = auth_client(SuperAdminFactory()).get(pl_detail_url(pl.pk))
        assert resp.status_code == 200

    def test_super_admin_can_hard_delete_pl(self):
        from apps.packing_list.models import PackingList
        super_admin = SuperAdminFactory()
        pl = PackingListFactory()
        resp = auth_client(super_admin).delete(f"/api/v1/packing-lists/{pl.pk}/hard-delete/")
        assert resp.status_code == 204
        assert not PackingList.objects.filter(pk=pl.pk).exists()

    def test_maker_cannot_hard_delete_pl(self):
        maker = MakerFactory()
        pl = PackingListFactory(created_by=maker)
        resp = auth_client(maker).delete(f"/api/v1/packing-lists/{pl.pk}/hard-delete/")
        assert resp.status_code == 403

    def test_company_admin_cannot_hard_delete_pl(self):
        pl = PackingListFactory()
        resp = auth_client(CompanyAdminFactory()).delete(f"/api/v1/packing-lists/{pl.pk}/hard-delete/")
        assert resp.status_code == 403
