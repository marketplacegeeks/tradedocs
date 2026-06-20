"""
Tests for the bulk-workflow endpoint on PackingListViewSet.

POST /api/v1/packing-lists/bulk-workflow/
Body:  {"document_ids": [1, 2, 3], "action": "APPROVE", "comment": "..."}
Returns: {"succeeded": [...], "failed": [{"id": ..., "reason": "..."}]}

PackingList uses transition_joint() which transitions both PL and linked CI atomically.
All tests exercise the HTTP layer — WorkflowService is not mocked.
"""

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CheckerFactory, MakerFactory
from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
from apps.packing_list.tests.factories import PackingListFactory
from apps.workflow.constants import APPROVED, DRAFT, PENDING_APPROVAL

BULK_WORKFLOW_URL = "/api/v1/packing-lists/bulk-workflow/"


def auth_client(user):
    """Return an APIClient authenticated as the given user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_pl_with_ci(status=DRAFT, created_by=None):
    """
    Create a PackingList and its linked CommercialInvoice in the given status.
    transition_joint() requires a linked CI to exist.
    """
    pl = PackingListFactory(status=status, created_by=created_by)
    CommercialInvoiceFactory(packing_list=pl, status=status, created_by=created_by)
    return pl


@pytest.mark.django_db
class TestPLBulkWorkflowSucceeds:
    """Happy-path: Checker approves two PENDING_APPROVAL PackingLists."""

    def test_bulk_approve_succeeds(self):
        maker = MakerFactory()
        checker = CheckerFactory()

        pl1 = make_pl_with_ci(status=PENDING_APPROVAL, created_by=maker)
        pl2 = make_pl_with_ci(status=PENDING_APPROVAL, created_by=maker)

        payload = {
            "document_ids": [pl1.pk, pl2.pk],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert sorted(data["succeeded"]) == sorted([pl1.pk, pl2.pk])
        assert data["failed"] == []

        # Confirm both PL and linked CI transitioned.
        pl1.refresh_from_db()
        pl2.refresh_from_db()
        assert pl1.status == APPROVED
        assert pl2.status == APPROVED
        assert pl1.commercial_invoice.status == APPROVED
        assert pl2.commercial_invoice.status == APPROVED


@pytest.mark.django_db
class TestPLBulkWorkflowValidation:
    """Input validation: 400 for missing required fields."""

    def test_bulk_missing_ids_returns_400(self):
        checker = CheckerFactory()
        payload = {"document_ids": [], "action": "APPROVE"}
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")
        assert response.status_code == 400

    def test_bulk_missing_action_returns_400(self):
        checker = CheckerFactory()
        maker = MakerFactory()
        pl = make_pl_with_ci(status=PENDING_APPROVAL, created_by=maker)
        payload = {"document_ids": [pl.pk], "action": ""}
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestPLBulkWorkflowPartialFailure:
    """Tests that failures are captured per-document, not globally."""

    def test_bulk_nonexistent_id_in_failed(self):
        maker = MakerFactory()
        checker = CheckerFactory()
        pl = make_pl_with_ci(status=PENDING_APPROVAL, created_by=maker)
        nonexistent_id = 999999

        payload = {
            "document_ids": [pl.pk, nonexistent_id],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert pl.pk in data["succeeded"]
        failed_ids = [f["id"] for f in data["failed"]]
        assert nonexistent_id in failed_ids

    def test_bulk_wrong_status_in_failed(self):
        """A DRAFT PL cannot be APPROVED — it appears in failed."""
        maker = MakerFactory()
        checker = CheckerFactory()
        pl_pending = make_pl_with_ci(status=PENDING_APPROVAL, created_by=maker)
        pl_draft = make_pl_with_ci(status=DRAFT, created_by=maker)

        payload = {
            "document_ids": [pl_pending.pk, pl_draft.pk],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(checker).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert pl_pending.pk in data["succeeded"]
        failed_ids = [f["id"] for f in data["failed"]]
        assert pl_draft.pk in failed_ids
        reason = next(f["reason"] for f in data["failed"] if f["id"] == pl_draft.pk)
        assert reason


@pytest.mark.django_db
class TestPLBulkWorkflowAuth:
    """Authentication and authorization tests."""

    def test_bulk_unauthenticated_returns_401(self):
        maker = MakerFactory()
        pl = make_pl_with_ci(status=PENDING_APPROVAL, created_by=maker)
        payload = {"document_ids": [pl.pk], "action": "APPROVE"}
        response = APIClient().post(BULK_WORKFLOW_URL, payload, format="json")
        assert response.status_code == 401

    def test_bulk_maker_cannot_approve(self):
        """Maker trying to APPROVE gets 200 with items in failed (PermissionDenied per document)."""
        maker = MakerFactory()
        maker2 = MakerFactory()
        pl = make_pl_with_ci(status=PENDING_APPROVAL, created_by=maker)

        payload = {
            "document_ids": [pl.pk],
            "action": "APPROVE",
            "comment": "",
        }
        response = auth_client(maker2).post(BULK_WORKFLOW_URL, payload, format="json")

        assert response.status_code == 200
        data = response.json()
        assert data["succeeded"] == []
        failed_ids = [f["id"] for f in data["failed"]]
        assert pl.pk in failed_ids
