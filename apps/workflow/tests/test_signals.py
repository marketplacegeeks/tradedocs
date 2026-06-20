"""
Tests for apps/workflow/signals.py — email notifications on AuditLog post_save.

Strategy:
  - Use Django's in-memory email backend so emails go to django.core.mail.outbox
    instead of the console.
  - Clear mail.outbox in setUp() before each test.
  - Create real DB objects (AuditLog, User, ProformaInvoice) via factories so the
    signal fires naturally through the ORM save path.
"""

from unittest.mock import patch

import pytest
from django.core import mail
from django.test import TestCase, override_settings

from apps.accounts.models import UserRole
from apps.accounts.tests.factories import (
    CheckerFactory,
    CompanyAdminFactory,
    MakerFactory,
    UserFactory,
)
from apps.proforma_invoice.tests.factories import ProformaInvoiceFactory
from apps.workflow.constants import APPROVE, PERMANENTLY_REJECT, REWORK_ACTION, SUBMIT
from apps.workflow.tests.factories import AuditLogFactory


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TestWorkflowSignals(TestCase):
    """Email notification signal tests."""

    def setUp(self):
        # Clear the in-memory outbox before every test.
        mail.outbox = []

    # ------------------------------------------------------------------
    # 1. SUBMIT → all active Checkers and Company Admins notified
    # ------------------------------------------------------------------
    def test_submit_notifies_checkers_and_admins(self):
        checker = CheckerFactory()
        admin = CompanyAdminFactory()
        maker = MakerFactory()

        AuditLogFactory(action=SUBMIT, performed_by=maker)

        # At least one email should have been sent.
        self.assertGreaterEqual(len(mail.outbox), 1)

        # Collect all recipients across all outbox messages.
        all_recipients = [addr for msg in mail.outbox for addr in msg.to]
        self.assertIn(checker.email, all_recipients)
        self.assertIn(admin.email, all_recipients)

    # ------------------------------------------------------------------
    # 2. APPROVE → document creator notified
    # ------------------------------------------------------------------
    def test_approve_notifies_document_creator(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker)

        AuditLogFactory(
            action=APPROVE,
            document_type="proforma_invoice",
            document_id=pi.pk,
            from_status="PENDING_APPROVAL",
            to_status="APPROVED",
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(maker.email, mail.outbox[0].to)

    # ------------------------------------------------------------------
    # 3. REWORK → document creator notified
    # ------------------------------------------------------------------
    def test_rework_notifies_document_creator(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker)

        AuditLogFactory(
            action=REWORK_ACTION,
            document_type="proforma_invoice",
            document_id=pi.pk,
            from_status="PENDING_APPROVAL",
            to_status="REWORK",
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(maker.email, mail.outbox[0].to)

    # ------------------------------------------------------------------
    # 4. PERMANENTLY_REJECT → document creator notified
    # ------------------------------------------------------------------
    def test_permanently_reject_notifies_document_creator(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker)

        AuditLogFactory(
            action=PERMANENTLY_REJECT,
            document_type="proforma_invoice",
            document_id=pi.pk,
            from_status="PENDING_APPROVAL",
            to_status="PERMANENTLY_REJECTED",
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(maker.email, mail.outbox[0].to)

    # ------------------------------------------------------------------
    # 5. Email failure does NOT raise — the signal swallows it
    # ------------------------------------------------------------------
    def test_email_failure_does_not_raise(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker)

        with patch(
            "apps.workflow.signals.send_mail",
            side_effect=Exception("SMTP down"),
        ):
            # This must not raise — the signal catches the exception.
            try:
                AuditLogFactory(
                    action=APPROVE,
                    document_type="proforma_invoice",
                    document_id=pi.pk,
                    from_status="PENDING_APPROVAL",
                    to_status="APPROVED",
                )
            except Exception as exc:
                self.fail(f"Signal propagated an exception when it should not have: {exc}")

    # ------------------------------------------------------------------
    # 6. Unknown action → no email sent
    # ------------------------------------------------------------------
    def test_no_email_for_unknown_action(self):
        maker = MakerFactory()

        AuditLogFactory(action="UNKNOWN", performed_by=maker)

        self.assertEqual(len(mail.outbox), 0)

    # ------------------------------------------------------------------
    # 7. Inactive Checkers are excluded from SUBMIT notifications
    # ------------------------------------------------------------------
    def test_submit_skips_inactive_checkers(self):
        # Inactive checker — should NOT receive email.
        inactive_checker = CheckerFactory(is_active=False)
        # Active checker — SHOULD receive email.
        active_checker = CheckerFactory(is_active=True)
        maker = MakerFactory()

        AuditLogFactory(action=SUBMIT, performed_by=maker)

        all_recipients = [addr for msg in mail.outbox for addr in msg.to]
        self.assertIn(active_checker.email, all_recipients)
        self.assertNotIn(inactive_checker.email, all_recipients)

    # ------------------------------------------------------------------
    # 8. Email body contains the deep link to the document
    # ------------------------------------------------------------------
    def test_email_body_contains_deep_link(self):
        maker = MakerFactory()
        pi = ProformaInvoiceFactory(created_by=maker)

        AuditLogFactory(
            action=APPROVE,
            document_type="proforma_invoice",
            document_id=pi.pk,
            from_status="PENDING_APPROVAL",
            to_status="APPROVED",
        )

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        # Deep link format: {FRONTEND_BASE_URL}/proforma-invoice/{pk}
        self.assertIn("proforma-invoice", body)
        self.assertIn(str(pi.pk), body)
