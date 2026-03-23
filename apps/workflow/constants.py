# Constraint #10: All document status strings are defined here.
# Import from this module everywhere — never hardcode "DRAFT" etc.

# ---- Document statuses -------------------------------------------------------

DRAFT = "DRAFT"
PENDING_APPROVAL = "PENDING_APPROVAL"
APPROVED = "APPROVED"
REWORK = "REWORK"
PERMANENTLY_REJECTED = "PERMANENTLY_REJECTED"

DOCUMENT_STATUS_CHOICES = [
    (DRAFT, "Draft"),
    (PENDING_APPROVAL, "Pending Approval"),
    (APPROVED, "Approved"),
    (REWORK, "Rework"),
    (PERMANENTLY_REJECTED, "Permanently Rejected"),
]

# ---- Workflow actions --------------------------------------------------------

SUBMIT = "SUBMIT"
APPROVE = "APPROVE"
REWORK_ACTION = "REWORK"
PERMANENTLY_REJECT = "PERMANENTLY_REJECT"

WORKFLOW_ACTION_CHOICES = [
    (SUBMIT, "Submit"),
    (APPROVE, "Approve"),
    (REWORK_ACTION, "Rework"),
    (PERMANENTLY_REJECT, "Permanently Reject"),
]

# States in which a document can be edited by a Maker.
EDITABLE_STATES = frozenset({DRAFT, REWORK})

# Actions that require a mandatory non-empty comment (constraint #15).
COMMENT_REQUIRED_ACTIONS = frozenset({REWORK_ACTION, PERMANENTLY_REJECT})

# ---- Per-document valid state machines ---------------------------------------
# Maps: current_status → { action → (next_status, allowed_roles) }

from apps.accounts.models import UserRole  # noqa: E402  (imported here to avoid circular imports at module load)

# ---- Combined PL + CI state machine (FR-14M.12) ------------------------------
# Both PackingList and CommercialInvoice share the same transition rules.
# WorkflowService applies this state machine to BOTH records simultaneously.
SUBMIT_ROLES = [UserRole.MAKER, UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN]
APPROVE_ROLES = [UserRole.MAKER, UserRole.CHECKER, UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN]

PLCI_TRANSITIONS = {
    DRAFT: {
        SUBMIT: (PENDING_APPROVAL, SUBMIT_ROLES),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
    PENDING_APPROVAL: {
        APPROVE: (APPROVED, APPROVE_ROLES),
        REWORK_ACTION: (REWORK, APPROVE_ROLES),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
    REWORK: {
        SUBMIT: (PENDING_APPROVAL, SUBMIT_ROLES),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
    APPROVED: {
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
}

PO_TRANSITIONS = {
    DRAFT: {
        SUBMIT: (PENDING_APPROVAL, SUBMIT_ROLES),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
    PENDING_APPROVAL: {
        APPROVE: (APPROVED, APPROVE_ROLES),
        REWORK_ACTION: (REWORK, APPROVE_ROLES),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
    REWORK: {
        SUBMIT: (PENDING_APPROVAL, SUBMIT_ROLES),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
    APPROVED: {
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
}

PI_TRANSITIONS = {
    DRAFT: {
        SUBMIT: (PENDING_APPROVAL, SUBMIT_ROLES),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
    PENDING_APPROVAL: {
        APPROVE: (APPROVED, APPROVE_ROLES),
        REWORK_ACTION: (REWORK, APPROVE_ROLES),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
    REWORK: {
        SUBMIT: (PENDING_APPROVAL, SUBMIT_ROLES),
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
    APPROVED: {
        PERMANENTLY_REJECT: (PERMANENTLY_REJECTED, APPROVE_ROLES),
    },
}
