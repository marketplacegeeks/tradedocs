"""
API tests for Purchase Order endpoints (FR-PO-12).

Tests cover:
- Maker creates PO → 201 with po_number
- Unauthenticated request → 401
- Submit → Approve full round-trip
- Submit → Rework → Resubmit round-trip
- Checker cannot edit content fields after PENDING_APPROVAL
- REWORK blocked if comment is empty
- PERMANENTLY_REJECT blocked if comment is empty
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CheckerFactory, CompanyAdminFactory, MakerFactory, SuperAdminFactory
from apps.purchase_order.models import PurchaseOrder
from .factories import (
    DeliveryAddressFactory,
    PurchaseOrderFactory,
    PurchaseOrderLineItemFactory,
    VendorOrganisationFactory,
)
from apps.master_data.tests.factories import CurrencyFactory, UOMFactory


@pytest.fixture
def api_client():
    return APIClient()


def get_tokens(client, email, password):
    response = client.post(reverse("auth-login"), {"email": email, "password": password})
    return response.data


def auth(client, user):
    tokens = get_tokens(client, user.email, "testpass123")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")


def make_po_payload(vendor=None, delivery_address=None, currency=None, uom=None):
    """Build a minimal valid POST payload for creating a PurchaseOrder."""
    if vendor is None:
        vendor = VendorOrganisationFactory()
    if delivery_address is None:
        delivery_address = DeliveryAddressFactory(organisation=vendor)
    if currency is None:
        currency = CurrencyFactory()
    internal_contact = MakerFactory()
    return {
        "po_date": "2026-03-22",
        "vendor": vendor.pk,
        "internal_contact": internal_contact.pk,
        "delivery_address": delivery_address.pk,
        "currency": currency.pk,
        "transaction_type": "ZERO_RATED",
    }


@pytest.mark.django_db
class TestPurchaseOrderCreate:
    def test_maker_creates_po_returns_201_with_po_number(self, api_client):
        maker = MakerFactory()
        auth(api_client, maker)
        payload = make_po_payload()
        response = api_client.post(reverse("purchase-order-list"), payload)
        assert response.status_code == 201, response.data
        assert "po_number" in response.data
        assert response.data["po_number"].startswith("PO-")

    def test_unauthenticated_create_returns_401(self, api_client):
        payload = make_po_payload()
        response = api_client.post(reverse("purchase-order-list"), payload)
        assert response.status_code == 401

    def test_checker_can_create_po(self, api_client):
        checker = CheckerFactory()
        auth(api_client, checker)
        payload = make_po_payload()
        response = api_client.post(reverse("purchase-order-list"), payload)
        assert response.status_code == 201


@pytest.mark.django_db
class TestPurchaseOrderWorkflow:
    def _po_with_line_item(self, creator):
        po = PurchaseOrderFactory(created_by=creator)
        PurchaseOrderLineItemFactory(purchase_order=po)
        return po

    def test_submit_approve_round_trip(self, api_client):
        """Maker submits → Checker approves → status APPROVED."""
        maker = MakerFactory()
        checker = CheckerFactory()
        po = self._po_with_line_item(maker)

        # Maker submits
        auth(api_client, maker)
        response = api_client.post(
            reverse("purchase-order-workflow", kwargs={"pk": po.pk}),
            {"action": "SUBMIT"},
        )
        assert response.status_code == 200
        assert response.data["status"] == "PENDING_APPROVAL"

        # Checker approves
        auth(api_client, checker)
        response = api_client.post(
            reverse("purchase-order-workflow", kwargs={"pk": po.pk}),
            {"action": "APPROVE"},
        )
        assert response.status_code == 200
        assert response.data["status"] == "APPROVED"

    def test_submit_rework_resubmit_round_trip(self, api_client):
        """Maker submits → Checker sends to rework → Maker resubmits → PENDING_APPROVAL."""
        maker = MakerFactory()
        checker = CheckerFactory()
        po = self._po_with_line_item(maker)

        auth(api_client, maker)
        api_client.post(
            reverse("purchase-order-workflow", kwargs={"pk": po.pk}),
            {"action": "SUBMIT"},
        )

        auth(api_client, checker)
        response = api_client.post(
            reverse("purchase-order-workflow", kwargs={"pk": po.pk}),
            {"action": "REWORK", "comment": "Please fix item descriptions."},
        )
        assert response.status_code == 200
        assert response.data["status"] == "REWORK"

        auth(api_client, maker)
        response = api_client.post(
            reverse("purchase-order-workflow", kwargs={"pk": po.pk}),
            {"action": "SUBMIT"},
        )
        assert response.status_code == 200
        assert response.data["status"] == "PENDING_APPROVAL"

    def test_rework_blocked_without_comment(self, api_client):
        """REWORK action requires a non-empty comment — blocked if comment missing."""
        maker = MakerFactory()
        checker = CheckerFactory()
        po = self._po_with_line_item(maker)

        auth(api_client, maker)
        api_client.post(
            reverse("purchase-order-workflow", kwargs={"pk": po.pk}),
            {"action": "SUBMIT"},
        )

        auth(api_client, checker)
        response = api_client.post(
            reverse("purchase-order-workflow", kwargs={"pk": po.pk}),
            {"action": "REWORK", "comment": ""},
        )
        assert response.status_code == 400

    def test_permanently_reject_blocked_without_comment(self, api_client):
        """PERMANENTLY_REJECT requires a non-empty comment."""
        maker = MakerFactory()
        checker = CheckerFactory()
        po = self._po_with_line_item(maker)

        auth(api_client, maker)
        api_client.post(
            reverse("purchase-order-workflow", kwargs={"pk": po.pk}),
            {"action": "SUBMIT"},
        )

        auth(api_client, checker)
        response = api_client.post(
            reverse("purchase-order-workflow", kwargs={"pk": po.pk}),
            {"action": "PERMANENTLY_REJECT", "comment": ""},
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestPurchaseOrderEditRestrictions:
    def test_checker_cannot_edit_after_pending_approval(self, api_client):
        """Checker is not the document owner — PATCH must be blocked."""
        maker = MakerFactory()
        checker = CheckerFactory()
        po = PurchaseOrderFactory(created_by=maker, status="PENDING_APPROVAL")

        auth(api_client, checker)
        response = api_client.patch(
            reverse("purchase-order-detail", kwargs={"pk": po.pk}),
            {"time_of_delivery": "August 2026"},
        )
        assert response.status_code in (400, 403)

    def test_unauthenticated_list_returns_401(self, api_client):
        response = api_client.get(reverse("purchase-order-list"))
        assert response.status_code == 401


@pytest.mark.django_db
class TestSuperAdminPurchaseOrderPermissions:
    """SUPER_ADMIN must have the same access as COMPANY_ADMIN on all PO endpoints."""

    def test_super_admin_can_list_pos(self, api_client):
        super_admin = SuperAdminFactory()
        PurchaseOrderFactory()
        auth(api_client, super_admin)
        response = api_client.get(reverse("purchase-order-list"))
        assert response.status_code == 200

    def test_super_admin_can_create_po(self, api_client):
        super_admin = SuperAdminFactory()
        auth(api_client, super_admin)
        response = api_client.post(reverse("purchase-order-list"), make_po_payload(), format="json")
        assert response.status_code == 201

    def test_super_admin_can_hard_delete_po(self, api_client):
        super_admin = SuperAdminFactory()
        po = PurchaseOrderFactory()
        auth(api_client, super_admin)
        response = api_client.delete(
            reverse("purchase-order-hard-delete", kwargs={"pk": po.pk})
        )
        assert response.status_code == 204
        assert not PurchaseOrder.objects.filter(pk=po.pk).exists()

    def test_maker_cannot_hard_delete_po(self, api_client):
        maker = MakerFactory()
        po = PurchaseOrderFactory(created_by=maker)
        auth(api_client, maker)
        response = api_client.delete(
            reverse("purchase-order-hard-delete", kwargs={"pk": po.pk})
        )
        assert response.status_code == 403

    def test_company_admin_cannot_hard_delete_po(self, api_client):
        admin = CompanyAdminFactory()
        po = PurchaseOrderFactory()
        auth(api_client, admin)
        response = api_client.delete(
            reverse("purchase-order-hard-delete", kwargs={"pk": po.pk})
        )
        assert response.status_code == 403
