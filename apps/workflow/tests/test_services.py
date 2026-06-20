"""
Unit tests for WorkflowService — cascade, status-parity, and atomicity.

These tests call WorkflowService methods directly (not through the HTTP layer)
so they stay fast and do not depend on URL routing.
"""

import pytest
from unittest.mock import patch, MagicMock

from apps.accounts.tests.factories import CheckerFactory, MakerFactory
from apps.commercial_invoice.models import CommercialInvoice
from apps.commercial_invoice.tests.factories import CommercialInvoiceFactory
from apps.packing_list.models import PackingList
from apps.packing_list.tests.factories import PackingListFactory
from apps.proforma_invoice.tests.factories import ProformaInvoiceFactory
from apps.workflow.constants import (
    APPROVED, DRAFT, PENDING_APPROVAL, PERMANENTLY_REJECTED, REWORK,
    PERMANENTLY_REJECT, APPROVE, SUBMIT,
)
from apps.workflow.models import AuditLog
from apps.workflow.services import WorkflowService


# ---- Cascade: PI → PL → CI --------------------------------------------------

@pytest.mark.django_db
class TestWorkflowCascade:
    """
    Verify _cascade_permanently_rejected() propagates through the full chain:
    PI → PL → CI.

    The existing test in test_views.py::TestWorkflowStateMachineExtended checks
    only that the PL status changes. This class checks the CI also changes,
    and tests the direct cascade path so we don't depend on HTTP routing.
    """

    def test_permanently_rejecting_pi_cascades_to_linked_ci(self):
        """
        When a PI is PERMANENTLY_REJECTED, the cascade must reach the linked CI.
        Chain: PI.transition() → _cascade_permanently_rejected("proforma_invoice")
               → PL.transition() → _cascade_permanently_rejected("packing_list")
               → CI.transition()
        All three documents must end in PERMANENTLY_REJECTED.
        """
        checker = CheckerFactory()
        pi = ProformaInvoiceFactory(status=APPROVED)
        pl = PackingListFactory(proforma_invoice=pi, status=DRAFT)
        ci = CommercialInvoiceFactory(packing_list=pl, status=DRAFT)

        WorkflowService.transition(
            document=pi,
            document_type="proforma_invoice",
            action=PERMANENTLY_REJECT,
            performed_by=checker,
            comment="Fraud detected at PI level.",
        )

        pi.refresh_from_db()
        pl.refresh_from_db()
        ci.refresh_from_db()

        assert pi.status == PERMANENTLY_REJECTED
        assert pl.status == PERMANENTLY_REJECTED, (
            "PL was not cascaded to PERMANENTLY_REJECTED when linked PI was rejected"
        )
        assert ci.status == PERMANENTLY_REJECTED, (
            "CI was not cascaded to PERMANENTLY_REJECTED when linked PI was rejected — "
            "cascade chain PI→PL→CI incomplete"
        )

    def test_permanently_rejecting_already_rejected_pl_is_skipped(self):
        """
        If the PL is already PERMANENTLY_REJECTED when the PI cascade fires,
        the service must skip it (the .exclude(status=PERMANENTLY_REJECTED) guard).
        No ValidationError must be raised.
        """
        checker = CheckerFactory()
        pi = ProformaInvoiceFactory(status=APPROVED)
        pl = PackingListFactory(proforma_invoice=pi, status=PERMANENTLY_REJECTED)
        ci = CommercialInvoiceFactory(packing_list=pl, status=PERMANENTLY_REJECTED)

        # This must NOT raise — already-rejected PLs are excluded from cascade.
        WorkflowService.transition(
            document=pi,
            document_type="proforma_invoice",
            action=PERMANENTLY_REJECT,
            performed_by=checker,
            comment="Cascade with already-rejected PL.",
        )

        pi.refresh_from_db()
        assert pi.status == PERMANENTLY_REJECTED

    def test_cascade_writes_audit_log_for_each_document(self):
        """
        Each document in the cascade must get its own AuditLog entry with
        document_type matching the model ('proforma_invoice', 'packing_list',
        'commercial_invoice').
        """
        checker = CheckerFactory()
        pi = ProformaInvoiceFactory(status=APPROVED)
        pl = PackingListFactory(proforma_invoice=pi, status=DRAFT)
        ci = CommercialInvoiceFactory(packing_list=pl, status=DRAFT)

        WorkflowService.transition(
            document=pi,
            document_type="proforma_invoice",
            action=PERMANENTLY_REJECT,
            performed_by=checker,
            comment="Audit log cascade test.",
        )

        pi_logs = AuditLog.objects.filter(
            document_type="proforma_invoice", document_id=pi.pk, action=PERMANENTLY_REJECT
        )
        pl_logs = AuditLog.objects.filter(
            document_type="packing_list", document_id=pl.pk, action=PERMANENTLY_REJECT
        )
        ci_logs = AuditLog.objects.filter(
            document_type="commercial_invoice", document_id=ci.pk, action=PERMANENTLY_REJECT
        )

        assert pi_logs.count() == 1, "PI must have an audit log entry for PERMANENTLY_REJECT"
        assert pl_logs.count() == 1, "PL must have an audit log entry from cascade"
        assert ci_logs.count() == 1, "CI must have an audit log entry from cascade"


# ---- transition_joint() status parity ----------------------------------------

@pytest.mark.django_db
class TestTransitionJointStatusParity:
    """
    Verify that transition_joint() always leaves PL and CI in the same status.
    Also verifies the atomic rollback guarantee via mock.
    """

    def _pl_ci_pair(self, status=DRAFT):
        """Return (pl, ci) in the given status."""
        from apps.master_data.tests.factories import IncotermFactory
        maker = MakerFactory()
        pl = PackingListFactory(
            status=status, created_by=maker, incoterms=IncotermFactory()
        )
        ci = CommercialInvoiceFactory(packing_list=pl, status=status, created_by=maker)
        return pl, ci, maker

    def test_approve_transitions_both_pl_and_ci(self):
        """
        APPROVE action via transition_joint() must move both PL and CI to APPROVED.
        Status parity: pl.status == ci.status == APPROVED after the call.
        """
        pl, ci, maker = self._pl_ci_pair(status=PENDING_APPROVAL)
        checker = CheckerFactory()

        WorkflowService.transition_joint(
            packing_list=pl,
            action=APPROVE,
            performed_by=checker,
        )

        pl.refresh_from_db()
        ci.refresh_from_db()

        assert pl.status == APPROVED
        assert ci.status == APPROVED
        assert pl.status == ci.status, "PL and CI must always share the same status"

    def test_rework_transitions_both_pl_and_ci(self):
        """
        REWORK action must move both PL and CI to REWORK simultaneously.
        """
        pl, ci, maker = self._pl_ci_pair(status=PENDING_APPROVAL)
        checker = CheckerFactory()

        WorkflowService.transition_joint(
            packing_list=pl,
            action="REWORK",
            performed_by=checker,
            comment="Quantities mismatch.",
        )

        pl.refresh_from_db()
        ci.refresh_from_db()

        assert pl.status == REWORK
        assert ci.status == REWORK
        assert pl.status == ci.status

    def test_transition_joint_is_atomic_ci_failure_rolls_back_pl(self):
        """
        If the CI status save fails inside transition_joint(), the PL status
        must NOT be committed (atomic rollback).

        Strategy: mock ci.save() to raise IntegrityError after PL has been saved
        but before the transaction commits. Assert PL status is unchanged.
        """
        from django.db import IntegrityError

        pl, ci, maker = self._pl_ci_pair(status=PENDING_APPROVAL)
        checker = CheckerFactory()

        original_pl_status = pl.status

        # Patch CommercialInvoice.save to raise after PL has been saved.
        # We patch on the instance (ci) rather than the class to avoid affecting
        # other test infrastructure.
        original_save = ci.__class__.save

        call_count = [0]

        def failing_save(self_inner, *args, **kwargs):
            call_count[0] += 1
            if self_inner.pk == ci.pk and call_count[0] >= 1:
                raise IntegrityError("Simulated CI save failure")
            return original_save(self_inner, *args, **kwargs)

        with patch.object(ci.__class__, "save", failing_save):
            with pytest.raises(IntegrityError):
                WorkflowService.transition_joint(
                    packing_list=pl,
                    action=APPROVE,
                    performed_by=checker,
                )

        # The transaction was rolled back — PL status must be unchanged.
        pl.refresh_from_db()
        assert pl.status == original_pl_status, (
            f"PL status should have rolled back to {original_pl_status!r} "
            f"but is now {pl.status!r} — transition_joint() is not atomic"
        )
