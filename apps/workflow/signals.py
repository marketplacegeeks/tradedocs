"""
Email notifications for document status changes.

Fires on AuditLog post_save — which happens after WorkflowService commits the status
transition to the database. Email failures are caught and logged so they never block
the workflow (CONTEXT.md decision; technical_architecture.md constraint #30).

Recipient rules:
  SUBMIT              → all active Checkers and Admins (they need to review)
  APPROVE / REWORK /
  PERMANENTLY_REJECT  → document creator (they need to know the outcome)

Each email includes a deep link to the document using settings.FRONTEND_BASE_URL
(per CONTEXT.md locked decision for deep link in email body).
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .constants import APPROVE, PERMANENTLY_REJECT, REWORK_ACTION, SUBMIT
from .models import AuditLog

logger = logging.getLogger(__name__)

# Actions that notify the document creator.
CREATOR_NOTIFY_ACTIONS = frozenset({APPROVE, REWORK_ACTION, PERMANENTLY_REJECT})

# Human-readable labels for email subjects.
_ACTION_LABELS = {
    SUBMIT: "submitted for approval",
    APPROVE: "approved",
    REWORK_ACTION: "sent back for rework",
    PERMANENTLY_REJECT: "permanently rejected",
}


@receiver(post_save, sender=AuditLog)
def on_audit_log_saved(sender, instance, created, **kwargs):
    """
    Send a notification email whenever a new AuditLog entry is created.
    Only fires on INSERT (created=True) — AuditLog rows are never updated.
    """
    if not created:
        return  # AuditLog is immutable; updates should never happen, but guard anyway.

    action = instance.action
    if action not in (SUBMIT, APPROVE, REWORK_ACTION, PERMANENTLY_REJECT):
        return  # Unknown action — no email for it.

    try:
        _dispatch_notification(instance, action)
    except Exception:
        # Constraint: email failure must never propagate to the caller.
        logger.exception(
            "Failed to send workflow notification email for AuditLog pk=%s action=%s",
            instance.pk,
            action,
        )


def _dispatch_notification(log: AuditLog, action: str) -> None:
    """Build recipient list and call send_mail based on action type."""
    from apps.accounts.models import User, UserRole  # lazy import — avoids circular

    document_label = log.document_type.replace("_", " ").title()
    action_label = _ACTION_LABELS.get(action, action.lower())
    subject = f"TradeDocs: {log.document_number} has been {action_label}"

    # Build deep link: convert document_type snake_case to kebab-case for frontend routes.
    # e.g. "proforma_invoice" → "proforma-invoice"
    doc_route = log.document_type.replace("_", "-")
    deep_link = f"{settings.FRONTEND_BASE_URL}/{doc_route}/{log.document_id}"

    # Use .full_name (a @property on the User model) — NOT .get_full_name() which does not exist.
    actor_name = log.performed_by.full_name or log.performed_by.email

    body = (
        f"Document: {document_label} {log.document_number}\n"
        f"Action: {action_label.capitalize()}\n"
        f"New status: {log.to_status.replace('_', ' ').title()}\n"
        f"Performed by: {actor_name}\n"
        f"View document: {deep_link}\n"
    )
    if log.comment:
        body += f"Comment: {log.comment}\n"

    from_email = settings.DEFAULT_FROM_EMAIL

    if action == SUBMIT:
        # Notify all active Checkers and Company Admins.
        recipient_emails = list(
            User.objects
            .filter(
                role__in=[UserRole.CHECKER, UserRole.COMPANY_ADMIN],
                is_active=True,
            )
            .values_list("email", flat=True)
        )
    else:
        # Notify the document creator.
        creator = _get_document_creator(log.document_type, log.document_id)
        if creator is None or not creator.email:
            return
        recipient_emails = [creator.email]

    if not recipient_emails:
        return

    send_mail(
        subject=subject,
        message=body,
        from_email=from_email,
        recipient_list=recipient_emails,
        fail_silently=False,  # Exception caught in on_audit_log_saved; let it surface to logger.
    )
    logger.info(
        "Workflow notification sent: action=%s document=%s recipients=%d",
        action, log.document_number, len(recipient_emails),
    )


def _get_document_creator(document_type: str, document_id: int):
    """Return the User who created the document, or None if not found."""
    try:
        if document_type == "proforma_invoice":
            from apps.proforma_invoice.models import ProformaInvoice
            doc = ProformaInvoice.objects.select_related("created_by").filter(pk=document_id).first()
        elif document_type == "packing_list":
            from apps.packing_list.models import PackingList
            doc = PackingList.objects.select_related("created_by").filter(pk=document_id).first()
        elif document_type == "commercial_invoice":
            from apps.commercial_invoice.models import CommercialInvoice
            doc = CommercialInvoice.objects.select_related("created_by").filter(pk=document_id).first()
        else:
            return None
        return doc.created_by if doc else None
    except Exception:
        logger.exception("Could not fetch document creator for %s pk=%s", document_type, document_id)
        return None
