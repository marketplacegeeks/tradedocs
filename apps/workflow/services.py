"""
WorkflowService — the single source of truth for all document status transitions.

Constraint #11: All status transitions go through here. Never update document.status anywhere else.
Constraint #12: AuditLog is written in the same transaction.atomic() as the status update.
Constraint #13: Permanently Rejected cascade is implemented only here.
Constraint #14: REWORK and PERMANENTLY_REJECT require a non-empty comment.
"""

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import UserRole

from .constants import (
    APPROVE,
    COMMENT_REQUIRED_ACTIONS,
    PI_TRANSITIONS,
    PLCI_TRANSITIONS,
    PERMANENTLY_REJECTED,
    SUBMIT,
)
from .models import AuditLog


class WorkflowService:

    @staticmethod
    def transition(document, document_type, action, performed_by, comment=""):
        """
        Apply a workflow action to a document.

        Args:
            document:       The model instance (must have .status, .pi_number / .pl_number / .ci_number).
            document_type:  String key, e.g. "proforma_invoice".
            action:         One of the WORKFLOW_ACTION_CHOICES strings.
            performed_by:   User instance performing the action.
            comment:        Optional string; required for certain actions.

        Raises:
            ValidationError  — invalid action for current state, or missing comment.
            PermissionDenied — user's role is not allowed to perform this action.
        """
        # Look up the transition table for this document type.
        transitions = WorkflowService._get_transitions(document_type)
        current_status = document.status

        if current_status not in transitions:
            raise ValidationError(
                {"action": f"No transitions are allowed from status '{current_status}'."}
            )

        allowed_actions = transitions[current_status]
        if action not in allowed_actions:
            raise ValidationError(
                {
                    "action": (
                        f"Action '{action}' is not allowed when status is '{current_status}'. "
                        f"Allowed actions: {list(allowed_actions.keys())}."
                    )
                }
            )

        next_status, allowed_roles = allowed_actions[action]

        # Check the user's role is permitted for this action.
        if performed_by.role not in allowed_roles:
            raise PermissionDenied(
                f"Your role ({performed_by.role}) is not allowed to perform '{action}'."
            )

        # FR-08.2 / US-04: the user who created the document cannot approve it,
        # unless they are a Company Admin (Admins are trusted to self-approve).
        if (action == APPROVE
                and hasattr(document, "created_by")
                and document.created_by == performed_by
                and performed_by.role != UserRole.COMPANY_ADMIN):
            raise PermissionDenied(
                "You cannot approve a document you created."
            )

        # Constraint #15: mandatory comment check.
        if action in COMMENT_REQUIRED_ACTIONS and not comment.strip():
            raise ValidationError(
                {"comment": f"A comment is required when performing '{action}'."}
            )

        # Perform the transition inside a single atomic transaction (constraint #12).
        with transaction.atomic():
            document.status = next_status
            document.save(update_fields=["status", "updated_at"])

            AuditLog.objects.create(
                document_type=document_type,
                document_id=document.pk,
                document_number=WorkflowService._get_document_number(document, document_type),
                action=action,
                from_status=current_status,
                to_status=next_status,
                comment=comment.strip(),
                performed_by=performed_by,
            )

            # Constraint #13: cascade Permanently Rejected to linked documents.
            if next_status == PERMANENTLY_REJECTED:
                WorkflowService._cascade_permanently_rejected(document, document_type, performed_by, comment)

        return next_status

    # ---- Helpers -------------------------------------------------------------

    @staticmethod
    def transition_joint(packing_list, action, performed_by, comment=""):
        """
        Apply a workflow action jointly to a PackingList and its linked CommercialInvoice.

        FR-14M.12: PL and CI are treated as a single unit — one action transitions both.
        Both status updates and both AuditLog entries are committed in one transaction.atomic().

        Args:
            packing_list:  The PackingList model instance.
            action:        One of the WORKFLOW_ACTION_CHOICES strings.
            performed_by:  User instance performing the action.
            comment:       Required for REWORK and PERMANENTLY_REJECT.

        Raises:
            ValidationError  — invalid action for current state, or missing comment.
            PermissionDenied — user's role is not allowed to perform this action.
        """
        transitions = PLCI_TRANSITIONS
        current_status = packing_list.status

        if current_status not in transitions:
            raise ValidationError(
                {"action": f"No transitions are allowed from status '{current_status}'."}
            )

        allowed_actions = transitions[current_status]
        if action not in allowed_actions:
            raise ValidationError(
                {
                    "action": (
                        f"Action '{action}' is not allowed when status is '{current_status}'. "
                        f"Allowed actions: {list(allowed_actions.keys())}."
                    )
                }
            )

        next_status, allowed_roles = allowed_actions[action]

        if performed_by.role not in allowed_roles:
            raise PermissionDenied(
                f"Your role ({performed_by.role}) is not allowed to perform '{action}'."
            )

        # FR-08.2: creator cannot approve their own document, unless they are a Company Admin.
        if (action == APPROVE
                and packing_list.created_by == performed_by
                and performed_by.role != UserRole.COMPANY_ADMIN):
            raise PermissionDenied("You cannot approve a document you created.")

        if action in COMMENT_REQUIRED_ACTIONS and not comment.strip():
            raise ValidationError(
                {"comment": f"A comment is required when performing '{action}'."}
            )

        # Incoterms is mandatory before a PL+CI can be submitted.
        if action == SUBMIT and not packing_list.incoterms_id:
            raise ValidationError(
                {"incoterms": "Incoterms must be set before submitting for approval."}
            )

        # Load the linked CI (required — PL and CI always exist together).
        try:
            ci = packing_list.commercial_invoice
        except Exception:
            raise ValidationError(
                {"detail": "No Commercial Invoice found linked to this Packing List."}
            )

        with transaction.atomic():
            # Transition the PL.
            packing_list.status = next_status
            packing_list.save(update_fields=["status", "updated_at"])
            AuditLog.objects.create(
                document_type="packing_list",
                document_id=packing_list.pk,
                document_number=packing_list.pl_number,
                action=action,
                from_status=current_status,
                to_status=next_status,
                comment=comment.strip(),
                performed_by=performed_by,
            )

            # Transition the CI to the same state.
            ci.status = next_status
            ci.save(update_fields=["status", "updated_at"])
            AuditLog.objects.create(
                document_type="commercial_invoice",
                document_id=ci.pk,
                document_number=ci.ci_number,
                action=action,
                from_status=current_status,
                to_status=next_status,
                comment=comment.strip(),
                performed_by=performed_by,
            )

        return next_status

    @staticmethod
    def _get_transitions(document_type):
        """Return the transition table for the given document type."""
        if document_type == "proforma_invoice":
            return PI_TRANSITIONS
        if document_type in ("packing_list", "commercial_invoice"):
            return PLCI_TRANSITIONS
        raise ValueError(f"Unknown document type: '{document_type}'.")

    @staticmethod
    def _get_document_number(document, document_type):
        """Read the document number field based on document type."""
        if document_type == "proforma_invoice":
            return document.pi_number
        if document_type == "packing_list":
            return document.pl_number
        if document_type == "commercial_invoice":
            return document.ci_number
        return str(document.pk)

    @staticmethod
    def _cascade_permanently_rejected(document, document_type, performed_by, comment):
        """
        Constraint #13: When a PI is permanently rejected, cascade to linked PLs and CIs.
        When a PL is permanently rejected, cascade to linked CIs.
        Uses lazy imports to avoid circular dependencies with future apps.
        """
        if document_type == "proforma_invoice":
            try:
                PackingList = _import_packing_list_model()
            except ImportError:
                return  # packing_list app not yet installed

            linked_pls = PackingList.objects.filter(
                proforma_invoice=document,
            ).exclude(status=PERMANENTLY_REJECTED)

            for pl in linked_pls:
                WorkflowService.transition(
                    document=pl,
                    document_type="packing_list",
                    action="PERMANENTLY_REJECT",
                    performed_by=performed_by,
                    comment=comment or f"Cascade from PI {document.pi_number}",
                )

        elif document_type == "packing_list":
            try:
                CommercialInvoice = _import_commercial_invoice_model()
            except ImportError:
                return

            linked_cis = CommercialInvoice.objects.filter(
                packing_list=document,
            ).exclude(status=PERMANENTLY_REJECTED)

            for ci in linked_cis:
                WorkflowService.transition(
                    document=ci,
                    document_type="commercial_invoice",
                    action="PERMANENTLY_REJECT",
                    performed_by=performed_by,
                    comment=comment or f"Cascade from PL {document.pl_number}",
                )


def _import_packing_list_model():
    from apps.packing_list.models import PackingList  # noqa
    return PackingList


def _import_commercial_invoice_model():
    from apps.commercial_invoice.models import CommercialInvoice  # noqa
    return CommercialInvoice
