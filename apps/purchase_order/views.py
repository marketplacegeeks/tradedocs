"""
Views for Purchase Order (FR-PO-09, FR-PO-11).

Constraint #29: All views explicitly declare permission_classes.
Constraint #20: PDF is streamed directly; never written to disk.
"""

import django_filters
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from apps.accounts.permissions import IsAnyRole
from apps.workflow.constants import EDITABLE_STATES
from apps.workflow.models import AuditLog
from apps.workflow.services import WorkflowService

from .models import PurchaseOrder, PurchaseOrderLineItem
from .serializers import AuditLogSerializer, PurchaseOrderLineItemSerializer, PurchaseOrderSerializer


# ---- Filterset --------------------------------------------------------------

class PurchaseOrderFilterSet(django_filters.FilterSet):
    po_number = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = PurchaseOrder
        fields = ["status", "created_by", "vendor", "po_number"]


# ---- PurchaseOrder ViewSet --------------------------------------------------

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    CRUD for Purchase Order headers.

    GET  /purchase-orders/        — list all POs
    POST /purchase-orders/        — create a new PO
    GET  /purchase-orders/{id}/   — retrieve PO with nested line items
    PUT/PATCH  /purchase-orders/{id}/ — update header (only in DRAFT/REWORK, by creator)
    """
    permission_classes = [IsAnyRole]  # Constraint #29
    serializer_class = PurchaseOrderSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PurchaseOrderFilterSet
    ordering_fields = ["created_at", "po_date", "po_number"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            PurchaseOrder.objects
            .select_related(
                "vendor",
                "internal_contact",
                "delivery_address",
                "bank",
                "currency",
                "payment_terms",
                "country_of_origin",
                "tc_template",
                "created_by",
            )
            .prefetch_related("line_items")
            .all()
        )

    def perform_create(self, serializer):
        # Any authenticated user can create a PO (FR-PO-11)
        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot edit a Purchase Order with status '{instance.status}'."}
            )
        if (instance.created_by != self.request.user
                and self.request.user.role != UserRole.COMPANY_ADMIN):
            raise PermissionDenied("Only the document creator can edit this Purchase Order.")
        serializer.save()

    # ---- Workflow action endpoint -------------------------------------------

    @action(detail=True, methods=["post"], url_path="workflow", permission_classes=[IsAnyRole])
    def workflow(self, request, pk=None):
        """
        POST /purchase-orders/{id}/workflow/
        Body: { "action": "SUBMIT" | "APPROVE" | "REWORK" | "PERMANENTLY_REJECT", "comment": "" }
        """
        po = self.get_object()
        action_name = request.data.get("action", "").strip().upper()
        comment = request.data.get("comment", "")

        if not action_name:
            raise ValidationError({"action": "This field is required."})

        # At least one line item must exist before the PO can be submitted (FR-PO-15)
        if action_name == "SUBMIT" and not po.line_items.exists():
            raise ValidationError(
                {"detail": "A Purchase Order must have at least one line item before it can be submitted."}
            )

        new_status = WorkflowService.transition(
            document=po,
            document_type="purchase_order",
            action=action_name,
            performed_by=request.user,
            comment=comment,
        )
        return Response({"status": new_status})

    # ---- PDF endpoint -------------------------------------------------------

    @action(detail=True, methods=["get"], url_path="pdf", permission_classes=[IsAnyRole])
    def pdf(self, request, pk=None):
        """
        GET /purchase-orders/{id}/pdf/
        Streams the PO PDF in memory. Constraint #20: never writes to disk.
        """
        from pdf.purchase_order import generate_po_pdf  # local import; pdf/ package

        po = self.get_object()
        pdf_buffer = generate_po_pdf(po)
        response = FileResponse(
            pdf_buffer,
            content_type="application/pdf",
            as_attachment=True,
            filename=f"{po.po_number}.pdf",
        )
        return response

    # ---- Audit log endpoint -------------------------------------------------

    @action(detail=True, methods=["get"], url_path="audit-log", permission_classes=[IsAnyRole])
    def audit_log(self, request, pk=None):
        """GET /purchase-orders/{id}/audit-log/"""
        po = self.get_object()
        logs = AuditLog.objects.filter(
            document_type="purchase_order",
            document_id=po.pk,
        ).select_related("performed_by")
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)


# ---- Line item views --------------------------------------------------------

class LineItemListCreateView(APIView):
    """
    GET  /purchase-orders/{po_id}/line-items/   — list line items
    POST /purchase-orders/{po_id}/line-items/   — add a line item
    """
    permission_classes = [IsAnyRole]  # Constraint #29

    def _get_po(self, po_id):
        try:
            return PurchaseOrder.objects.get(pk=po_id)
        except PurchaseOrder.DoesNotExist:
            raise NotFound("Purchase Order not found.")

    def _check_editable(self, po, user):
        if po.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot modify line items when PO status is '{po.status}'."}
            )
        if po.created_by != user and user.role != UserRole.COMPANY_ADMIN:
            raise PermissionDenied("Only the document creator can modify line items.")

    def get(self, request, po_id):
        po = self._get_po(po_id)
        serializer = PurchaseOrderLineItemSerializer(po.line_items.all(), many=True)
        return Response(serializer.data)

    def post(self, request, po_id):
        po = self._get_po(po_id)
        self._check_editable(po, request.user)
        serializer = PurchaseOrderLineItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(purchase_order=po)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LineItemDetailView(APIView):
    """
    PUT    /purchase-orders/{po_id}/line-items/{lid}/ — update
    PATCH  /purchase-orders/{po_id}/line-items/{lid}/ — partial update
    DELETE /purchase-orders/{po_id}/line-items/{lid}/ — delete
    """
    permission_classes = [IsAnyRole]  # Constraint #29

    def _get_objects(self, po_id, lid, user):
        try:
            po = PurchaseOrder.objects.get(pk=po_id)
        except PurchaseOrder.DoesNotExist:
            raise NotFound("Purchase Order not found.")
        try:
            item = PurchaseOrderLineItem.objects.get(pk=lid, purchase_order=po)
        except PurchaseOrderLineItem.DoesNotExist:
            raise NotFound("Line item not found.")
        if po.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot modify line items when PO status is '{po.status}'."}
            )
        if po.created_by != user and user.role != UserRole.COMPANY_ADMIN:
            raise PermissionDenied("Only the document creator can modify line items.")
        return po, item

    def put(self, request, po_id, lid):
        po, item = self._get_objects(po_id, lid, request.user)
        serializer = PurchaseOrderLineItemSerializer(item, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, po_id, lid):
        po, item = self._get_objects(po_id, lid, request.user)
        serializer = PurchaseOrderLineItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, po_id, lid):
        po, item = self._get_objects(po_id, lid, request.user)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
