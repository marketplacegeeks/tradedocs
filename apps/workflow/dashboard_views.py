"""
Dashboard summary API — GET /api/v1/dashboard/

Returns document counts and the 10 most recent audit log entries.
Permission: any authenticated user (IsAnyRole).
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAnyRole
from apps.proforma_invoice.models import ProformaInvoice
from apps.packing_list.models import PackingList
from apps.purchase_order.models import PurchaseOrder
from apps.workflow.constants import PENDING_APPROVAL
from apps.workflow.models import AuditLog


# Human-readable labels for audit log actions (mirrors the frontend constant).
_ACTION_LABELS = {
    "SUBMIT": "Submitted",
    "APPROVE": "Approved",
    "REWORK": "Sent for Rework",
    "PERMANENTLY_REJECT": "Permanently Rejected",
}

# Maps document_type string → the path prefix used in the frontend URL.
_DOC_URL_PREFIX = {
    "proforma_invoice": "/proforma-invoices",
    "packing_list": "/packing-lists",
    "purchase_order": "/purchase-orders",
    "commercial_invoice": "/packing-lists",  # CI is viewed via the PL detail page
}


class DashboardView(APIView):
    permission_classes = [IsAnyRole]

    def get(self, request):
        # ---- Counts ---------------------------------------------------------
        pi_count = ProformaInvoice.objects.count()
        pl_count = PackingList.objects.count()
        po_count = PurchaseOrder.objects.count()

        pending_count = (
            ProformaInvoice.objects.filter(status=PENDING_APPROVAL).count()
            + PackingList.objects.filter(status=PENDING_APPROVAL).count()
            + PurchaseOrder.objects.filter(status=PENDING_APPROVAL).count()
        )

        # ---- Recent activity (10 latest audit log entries) ------------------
        logs = (
            AuditLog.objects
            .select_related("performed_by")
            .order_by("-performed_at")[:10]
        )

        activity = []
        for log in logs:
            activity.append({
                "id": log.pk,
                "document_type": log.document_type,
                "document_id": log.document_id,
                "document_number": log.document_number,
                "action": log.action,
                "action_label": _ACTION_LABELS.get(log.action, log.action.replace("_", " ").title()),
                "to_status": log.to_status,
                "performed_by_name": log.performed_by.full_name if log.performed_by else "—",
                "performed_at": log.performed_at.isoformat(),
                "url_prefix": _DOC_URL_PREFIX.get(log.document_type, ""),
            })

        return Response({
            "counts": {
                "proforma_invoices": pi_count,
                "packing_lists": pl_count,
                "purchase_orders": po_count,
                "pending_approvals": pending_count,
            },
            "recent_activity": activity,
        })
