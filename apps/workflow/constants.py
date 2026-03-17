# Constraint #10: All document status strings are defined here.
# Import from this module everywhere — never hardcode "DRAFT" etc.

# ---- Document statuses -------------------------------------------------------

DRAFT = "DRAFT"
PENDING_APPROVAL = "PENDING_APPROVAL"
APPROVED = "APPROVED"
REWORK = "REWORK"
PERMANENTLY_REJECTED = "PERMANENTLY_REJECTED"
DISABLED = "DISABLED"  # Valid only for CommercialInvoice (constraint #14)

DOCUMENT_STATUS_CHOICES = [
    (DRAFT, "Draft"),
    (PENDING_APPROVAL, "Pending Approval"),
    (APPROVED, "Approved"),
    (REWORK, "Rework"),
    (PERMANENTLY_REJECTED, "Permanently Rejected"),
    (DISABLED, "Disabled"),
]

# ---- Workflow actions --------------------------------------------------------

SUBMIT = "SUBMIT"
APPROVE = "APPROVE"
REWORK_ACTION = "REWORK"
PERMANENTLY_REJECT = "PERMANENTLY_REJECT"
DISABLE = "DISABLE"  # CommercialInvoice only

WORKFLOW_ACTION_CHOICES = [
    (SUBMIT, "Submit"),
    (APPROVE, "Approve"),
    (REWORK_ACTION, "Rework"),
    (PERMANENTLY_REJECT, "Permanently Reject"),
    (DISABLE, "Disable"),
]

# States in which a document can be edited by a Maker.
EDITABLE_STATES = frozenset({DRAFT, REWORK})

# Actions that require a mandatory non-empty comment (constraint #15).
COMMENT_REQUIRED_ACTIONS = frozenset({REWORK_ACTION, PERMANENTLY_REJECT, DISABLE})

# ---- Per-document valid state machines ---------------------------------------
# Maps: current_status → { action → (next_status, allowed_roles) }

from apps.accounts.models import UserRole  # noqa: E402  (imported here to avoid circular imports at module load)

PI_TRANSITIONS = {
    DRAFT: {
        SUBMIT: (PENDING_APPROVAL, [UserRole.MAKER, UserRole.COMPANY_ADMIN]),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, [UserRole.CHECKER, UserRole.COMPANY_ADMIN]),
    },
    PENDING_APPROVAL: {
        APPROVE: (APPROVED, [UserRole.CHECKER, UserRole.COMPANY_ADMIN]),
        REWORK_ACTION: (REWORK, [UserRole.CHECKER, UserRole.COMPANY_ADMIN]),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, [UserRole.CHECKER, UserRole.COMPANY_ADMIN]),
    },
    REWORK: {
        SUBMIT: (PENDING_APPROVAL, [UserRole.MAKER, UserRole.COMPANY_ADMIN]),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, [UserRole.CHECKER, UserRole.COMPANY_ADMIN]),
    },
    APPROVED: {
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, [UserRole.CHECKER, UserRole.COMPANY_ADMIN]),
    },
}
