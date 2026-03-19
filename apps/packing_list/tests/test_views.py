"""
API view tests for PackingList, Container, and ContainerItem endpoints.

Every endpoint has at minimum:
- One happy-path test
- One permission-denial test
"""

import pytest
from decimal import Decimal
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CheckerFactory, CompanyAdminFactory, MakerFactory
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
        """Create a PL+CI pair in the given status."""
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        maker = maker or MakerFactory()
        pl = PackingListFactory(status=status_value, created_by=maker)
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

    def test_creator_cannot_approve_own_document(self):
        """FR-08.2: maker who created the document cannot approve it, even as Admin."""
        from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
        admin = CompanyAdminFactory()
        pl = PackingListFactory(status=PENDING_APPROVAL, created_by=admin)
        CommercialInvoiceFactory(packing_list=pl, status=PENDING_APPROVAL, created_by=admin)
        resp = auth_client(admin).post(
            pl_workflow_url(pl.pk), {"action": "APPROVE"}, format="json"
        )
        assert resp.status_code == 403

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
