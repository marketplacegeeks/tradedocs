"""
Tests for AuditLogViewSet — GET /api/v1/audit-logs/

Covers:
- Happy-path list access for Checker and Admin
- Maker sees only their own actions (performed_by=request.user)
- Unauthenticated requests are rejected with 401
- Filtering by document_type and action
- Single-entry retrieve endpoint

Note: StandardPageNumberPagination only paginates when ?page= is present.
Tests that assert on paginated shape (count/results) pass page=1.
Tests that don't need pagination structure omit it.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import (
    CheckerFactory,
    CompanyAdminFactory,
    MakerFactory,
)
from apps.workflow.tests.factories import AuditLogFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def checker(db):
    return CheckerFactory()


@pytest.fixture
def admin(db):
    return CompanyAdminFactory()


@pytest.fixture
def maker_a(db):
    return MakerFactory()


@pytest.fixture
def maker_b(db):
    return MakerFactory()


@pytest.mark.django_db
class TestAuditLogViewSetList:
    """Tests for GET /api/v1/audit-logs/ (list endpoint)."""

    def test_list_returns_200_for_checker(self, client, checker):
        """Checker can retrieve the audit log list."""
        AuditLogFactory(performed_by=checker)
        client.force_authenticate(user=checker)
        url = reverse("audit-log-list")
        # Pass page=1 so StandardPageNumberPagination activates and returns {count, results}
        response = client.get(url, {"page": 1})
        assert response.status_code == 200
        assert "results" in response.data
        assert response.data["count"] >= 1

    def test_list_returns_200_for_admin(self, client, admin):
        """Company Admin can retrieve the audit log list."""
        AuditLogFactory(performed_by=admin)
        client.force_authenticate(user=admin)
        url = reverse("audit-log-list")
        response = client.get(url, {"page": 1})
        assert response.status_code == 200
        assert "results" in response.data
        assert response.data["count"] >= 1

    def test_maker_sees_only_own_actions(self, client, maker_a, maker_b, db):
        """Maker A sees only logs where they were the actor, not logs by Maker B."""
        log_a = AuditLogFactory(performed_by=maker_a, document_number="PI-2026-0001")
        AuditLogFactory(performed_by=maker_b, document_number="PI-2026-0002")

        client.force_authenticate(user=maker_a)
        url = reverse("audit-log-list")
        response = client.get(url, {"page": 1})

        assert response.status_code == 200
        returned_ids = [entry["id"] for entry in response.data["results"]]
        assert log_a.id in returned_ids
        # Maker A must NOT see Maker B's entry
        assert response.data["count"] == 1

    def test_unauthenticated_returns_401(self, client, db):
        """Requests without a valid token are rejected."""
        AuditLogFactory()
        url = reverse("audit-log-list")
        response = client.get(url)
        assert response.status_code == 401

    def test_filter_by_document_type(self, client, checker, db):
        """?document_type=proforma_invoice narrows results to that document type only."""
        AuditLogFactory(performed_by=checker, document_type="proforma_invoice")
        AuditLogFactory(performed_by=checker, document_type="packing_list")

        client.force_authenticate(user=checker)
        url = reverse("audit-log-list")
        response = client.get(url, {"document_type": "proforma_invoice", "page": 1})

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["document_type"] == "proforma_invoice"

    def test_filter_by_action(self, client, checker, db):
        """?action=APPROVE narrows results to APPROVE actions only."""
        AuditLogFactory(performed_by=checker, action="APPROVE", from_status="PENDING_APPROVAL", to_status="APPROVED")
        AuditLogFactory(performed_by=checker, action="SUBMIT", from_status="DRAFT", to_status="PENDING_APPROVAL")

        client.force_authenticate(user=checker)
        url = reverse("audit-log-list")
        response = client.get(url, {"action": "APPROVE", "page": 1})

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["action"] == "APPROVE"


@pytest.mark.django_db
class TestAuditLogViewSetRetrieve:
    """Tests for GET /api/v1/audit-logs/{id}/ (detail endpoint)."""

    def test_retrieve_single_entry(self, client, checker, db):
        """GET /api/v1/audit-logs/{id}/ returns 200 with the correct fields."""
        log = AuditLogFactory(
            performed_by=checker,
            document_type="proforma_invoice",
            document_number="PI-2026-0001",
            action="APPROVE",
        )

        client.force_authenticate(user=checker)
        url = reverse("audit-log-detail", args=[log.id])
        response = client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == log.id
        assert response.data["document_type"] == "proforma_invoice"
        assert response.data["document_number"] == "PI-2026-0001"
        assert response.data["action"] == "APPROVE"
        assert "performed_by_name" in response.data
        assert "performed_at" in response.data
