"""
API view tests for CommercialInvoice and CommercialInvoiceLineItem endpoints.

Every endpoint has at minimum:
- One happy-path test
- One permission-denial test
"""

import pytest
from decimal import Decimal
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CheckerFactory, CompanyAdminFactory, MakerFactory
from apps.master_data.tests.factories import BankFactory, UOMFactory
from apps.workflow.constants import APPROVED, DRAFT, PENDING_APPROVAL, REWORK

from apps.packing_list.tests.factories import PackingListFactory
from .factories import CommercialInvoiceFactory, CommercialInvoiceLineItemFactory


# ---- Helpers ----------------------------------------------------------------

def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


CI_LIST_URL = "/api/v1/commercial-invoices/"


def ci_detail_url(pk):
    return f"/api/v1/commercial-invoices/{pk}/"


def line_item_detail_url(pk):
    return f"/api/v1/ci-line-items/{pk}/"


# ---- List -------------------------------------------------------------------

@pytest.mark.django_db
class TestCommercialInvoiceList:

    def test_all_roles_can_list(self):
        for user in (MakerFactory(), CheckerFactory(), CompanyAdminFactory()):
            resp = auth_client(user).get(CI_LIST_URL)
            assert resp.status_code == 200

    def test_unauthenticated_denied(self):
        resp = APIClient().get(CI_LIST_URL)
        assert resp.status_code == 401


# ---- Retrieve ---------------------------------------------------------------

@pytest.mark.django_db
class TestCommercialInvoiceRetrieve:

    def test_any_role_can_retrieve(self):
        ci = CommercialInvoiceFactory()
        for user in (MakerFactory(), CheckerFactory(), CompanyAdminFactory()):
            resp = auth_client(user).get(ci_detail_url(ci.pk))
            assert resp.status_code == 200

    def test_retrieve_includes_line_items(self):
        ci = CommercialInvoiceFactory()
        CommercialInvoiceLineItemFactory(ci=ci)
        resp = auth_client(ci.created_by).get(ci_detail_url(ci.pk))
        assert resp.status_code == 200
        assert len(resp.json()["line_items"]) == 1


# ---- Create/Delete blocked --------------------------------------------------

@pytest.mark.django_db
class TestCommercialInvoiceCreateDeleteBlocked:

    def test_direct_create_blocked(self):
        maker = MakerFactory()
        resp = auth_client(maker).post(CI_LIST_URL, {}, format="json")
        assert resp.status_code == 400

    def test_direct_delete_blocked(self):
        maker = MakerFactory()
        ci = CommercialInvoiceFactory(created_by=maker)
        resp = auth_client(maker).delete(ci_detail_url(ci.pk))
        assert resp.status_code == 400


# ---- Update financial fields ------------------------------------------------

@pytest.mark.django_db
class TestCommercialInvoiceUpdate:

    def test_creator_can_update_financial_fields_in_draft(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        ci = CommercialInvoiceFactory(packing_list=pl, status=DRAFT, created_by=maker)
        bank = BankFactory()
        resp = auth_client(maker).patch(
            ci_detail_url(ci.pk),
            {"bank": bank.pk, "lc_details": "LC 12345"},
            format="json",
        )
        assert resp.status_code == 200

    def test_cannot_update_when_pending_approval(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=PENDING_APPROVAL, created_by=maker)
        ci = CommercialInvoiceFactory(packing_list=pl, status=PENDING_APPROVAL, created_by=maker)
        resp = auth_client(maker).patch(
            ci_detail_url(ci.pk),
            {"lc_details": "LC 99999"},
            format="json",
        )
        assert resp.status_code == 400

    def test_non_creator_cannot_update(self):
        pl = PackingListFactory(status=DRAFT)
        ci = CommercialInvoiceFactory(packing_list=pl, status=DRAFT, created_by=pl.created_by)
        other_maker = MakerFactory()
        resp = auth_client(other_maker).patch(
            ci_detail_url(ci.pk),
            {"lc_details": "Not mine"},
            format="json",
        )
        assert resp.status_code == 403


# ---- Line item rate update --------------------------------------------------

@pytest.mark.django_db
class TestCILineItemUpdate:

    def test_creator_can_update_rate(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        ci = CommercialInvoiceFactory(packing_list=pl, status=DRAFT, created_by=maker)
        li = CommercialInvoiceLineItemFactory(ci=ci)
        resp = auth_client(maker).patch(
            line_item_detail_url(li.pk),
            {"rate_usd": "250.00"},
            format="json",
        )
        assert resp.status_code == 200
        li.refresh_from_db()
        assert li.rate_usd == Decimal("250.00")

    def test_cannot_update_rate_when_approved(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=APPROVED, created_by=maker)
        ci = CommercialInvoiceFactory(packing_list=pl, status=APPROVED, created_by=maker)
        li = CommercialInvoiceLineItemFactory(ci=ci)
        resp = auth_client(maker).patch(
            line_item_detail_url(li.pk),
            {"rate_usd": "999.00"},
            format="json",
        )
        assert resp.status_code == 400

    def test_creator_can_update_packages_kind(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        ci = CommercialInvoiceFactory(packing_list=pl, status=DRAFT, created_by=maker)
        li = CommercialInvoiceLineItemFactory(ci=ci)
        resp = auth_client(maker).patch(
            line_item_detail_url(li.pk),
            {"packages_kind": "10 Bags, 5 Bags"},
            format="json",
        )
        assert resp.status_code == 200
        li.refresh_from_db()
        assert li.packages_kind == "10 Bags, 5 Bags"

    def test_negative_rate_rejected(self):
        maker = MakerFactory()
        pl = PackingListFactory(status=DRAFT, created_by=maker)
        ci = CommercialInvoiceFactory(packing_list=pl, status=DRAFT, created_by=maker)
        li = CommercialInvoiceLineItemFactory(ci=ci)
        resp = auth_client(maker).patch(
            line_item_detail_url(li.pk),
            {"rate_usd": "-10.00"},
            format="json",
        )
        assert resp.status_code == 400
