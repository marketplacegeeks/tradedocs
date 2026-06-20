"""
Tests for the bulk-workflow endpoint on ProformaInvoiceViewSet.

POST /api/v1/proforma-invoices/bulk-workflow/
Body:  {"document_ids": [1, 2, 3], "action": "APPROVE", "comment": "..."}
Returns: {"succeeded": [...], "failed": [{"id": ..., "reason": "..."}]}

All tests exercise the HTTP layer only — WorkflowService is not mocked so real
transition rules are applied.
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CheckerFactory, MakerFactory
from apps.proforma_invoice.tests.factories import ProformaInvoiceFactory
from apps.workflow.constants import DRAFT, PENDING_APPROVAL, APPROVED

BULK_WORKFLOW_URL = "/api/v1/proforma-invoices/bulk-workflow/"


def auth_client(user):
    """Return an APIClient authenticated as the given user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestPIBulkWorkflowSucceeds:
    """Happy-path: Checker approves two PENDING_APPROVAL documents."""

    def test_bulk_approve_succeeds(self):
        maker = MakerFactory()
        checker = CheckerFactory()

        # Create two PIs submitted by maker (PENDING_APPROVAL).
        pi1 = ProformaInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)
        pi2 = ProformaInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)

        payload = {
            "document_ids": [pi1.pk, pi2.pk],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert sorted(data["succeeded"]) == sorted([pi1.pk, pi2.pk])
        assert data["failed"] == []

        # Confirm DB state actually changed.
        pi1.refresh_from_db()
        pi2.refresh_from_db()
        assert pi1.status == APPROVED
        assert pi2.status == APPROVED


@pytest.mark.django_db
class TestPIBulkWorkflowValidation:
    """Input validation tests — 400 for missing required fields."""

    def test_bulk_missing_ids_returns_400(self):
        checker = CheckerFactory()
        payload = {"document_ids": [], "action": "APPROVE"}
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")
        assert response.status_code == 400

    def test_bulk_missing_action_returns_400(self):
        checker = CheckerFactory()
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)
        payload = {"document_ids": [pi.pk], "action": ""}
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestPIBulkWorkflowPartialFailure:
    """Tests that failures are captured per-document, not globally."""

    def test_bulk_nonexistent_id_in_failed(self):
        maker = MakerFactory()
        checker = CheckerFactory()
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)
        nonexistent_id = 999999

        payload = {
            "document_ids": [pi.pk, nonexistent_id],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert pi.pk in data["succeeded"]
        failed_ids = [f["id"] for f in data["failed"]]
        assert nonexistent_id in failed_ids

    def test_bulk_wrong_status_in_failed(self):
        """A DRAFT document cannot be APPROVED — it appears in failed."""
        maker = MakerFactory()
        checker = CheckerFactory()
        pi_pending = ProformaInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)
        pi_draft = ProformaInvoiceFactory(status=DRAFT, created_by=maker)

        payload = {
            "document_ids": [pi_pending.pk, pi_draft.pk],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert pi_pending.pk in data["succeeded"]
        failed_ids = [f["id"] for f in data["failed"]]
        assert pi_draft.pk in failed_ids
        # Verify the reason mentions the disallowed action.
        reason = next(f["reason"] for f in data["failed"] if f["id"] == pi_draft.pk)
        assert reason  # non-empty reason string


@pytest.mark.django_db
class TestPIBulkWorkflowAuth:
    """Authentication and authorization tests."""

    def test_bulk_unauthenticated_returns_401(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)
        payload = {"document_ids": [pi.pk], "action": "APPROVE"}
        response = APIClient().post(BULK_WORKFLOW_URL, payload, format="json")
        assert response.status_code == 401

    def test_bulk_maker_cannot_approve(self):
        """Maker trying to APPROVE gets 200 with items in failed (PermissionDenied per document)."""
        maker = MakerFactory()
        # A different maker submitted it — maker2 tries to approve.
        maker2 = MakerFactory()
        pi = ProformaInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)

        payload = {
            "document_ids": [pi.pk],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(maker2).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert data["succeeded"] == []
        failed_ids = [f["id"] for f in data["failed"]]
        assert pi.pk in failed_ids
