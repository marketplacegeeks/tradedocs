"""
Tests for the bulk-workflow endpoint on CommercialInvoiceViewSet.

POST /api/v1/commercial-invoices/bulk-workflow/
Body:  {"document_ids": [1, 2, 3], "action": "APPROVE", "comment": "..."}
Returns: {"succeeded": [...], "failed": [{"id": ..., "reason": "..."}]}

CommercialInvoice uses WorkflowService.transition() directly (same as PI).
All tests exercise the HTTP layer — WorkflowService is not mocked.
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CheckerFactory, MakerFactory
from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
from apps.workflow.constants import APPROVED, DRAFT, PENDING_APPROVAL

BULK_WORKFLOW_URL = "/api/v1/commercial-invoices/bulk-workflow/"


def auth_client(user):
    """Return an APIClient authenticated as the given user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestCIBulkWorkflowSucceeds:
    """Happy-path: Checker approves two PENDING_APPROVAL CommercialInvoices."""

    def test_bulk_approve_succeeds(self):
        maker = MakerFactory()
        checker = CheckerFactory()

        ci1 = CommercialInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)
        ci2 = CommercialInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)

        payload = {
            "document_ids": [ci1.pk, ci2.pk],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert sorted(data["succeeded"]) == sorted([ci1.pk, ci2.pk])
        assert data["failed"] == []

        # Confirm DB state changed.
        ci1.refresh_from_db()
        ci2.refresh_from_db()
        assert ci1.status == APPROVED
        assert ci2.status == APPROVED


@pytest.mark.django_db
class TestCIBulkWorkflowValidation:
    """Input validation: 400 for missing required fields."""

    def test_bulk_missing_ids_returns_400(self):
        checker = CheckerFactory()
        payload = {"document_ids": [], "action": "APPROVE"}
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")
        assert response.status_code == 400

    def test_bulk_missing_action_returns_400(self):
        checker = CheckerFactory()
        maker = MakerFactory()
        ci = CommercialInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)
        payload = {"document_ids": [ci.pk], "action": ""}
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestCIBulkWorkflowPartialFailure:
    """Tests that failures are captured per-document, not globally."""

    def test_bulk_nonexistent_id_in_failed(self):
        maker = MakerFactory()
        checker = CheckerFactory()
        ci = CommercialInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)
        nonexistent_id = 999999

        payload = {
            "document_ids": [ci.pk, nonexistent_id],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert ci.pk in data["succeeded"]
        failed_ids = [f["id"] for f in data["failed"]]
        assert nonexistent_id in failed_ids

    def test_bulk_wrong_status_in_failed(self):
        """A DRAFT CI cannot be APPROVED — it appears in failed."""
        maker = MakerFactory()
        checker = CheckerFactory()
        ci_pending = CommercialInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)
        ci_draft = CommercialInvoiceFactory(status=DRAFT, created_by=maker)

        payload = {
            "document_ids": [ci_pending.pk, ci_draft.pk],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert ci_pending.pk in data["succeeded"]
        failed_ids = [f["id"] for f in data["failed"]]
        assert ci_draft.pk in failed_ids
        reason = next(f["reason"] for f in data["failed"] if f["id"] == ci_draft.pk)
        assert reason


@pytest.mark.django_db
class TestCIBulkWorkflowAuth:
    """Authentication and authorization tests."""

    def test_bulk_unauthenticated_returns_401(self):
        maker = MakerFactory()
        ci = CommercialInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)
        payload = {"document_ids": [ci.pk], "action": "APPROVE"}
        response = APIClient().post(BULK_WORKFLOW_URL, payload, format="json")
        assert response.status_code == 401

    def test_bulk_maker_cannot_approve(self):
        """Maker trying to APPROVE gets 200 with items in failed (PermissionDenied per document)."""
        maker = MakerFactory()
        maker2 = MakerFactory()
        ci = CommercialInvoiceFactory(status=PENDING_APPROVAL, created_by=maker)

        payload = {
            "document_ids": [ci.pk],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(maker2).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert data["succeeded"] == []
        failed_ids = [f["id"] for f in data["failed"]]
        assert ci.pk in failed_ids
