"""
Views for Proforma Invoice (FR-09).

Constraint #10: All authenticated views explicitly declare permission_classes.
Constraint #19: List endpoints support filtering by status and created_by via django-filter.
Constraint #20: PDF is streamed directly; never written to disk.
"""

import django_filters
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings

from apps.accounts.models import UserRole
from apps.accounts.permissions import IsAnyRole, IsSuperAdmin
from apps.workflow.constants import APPROVED, EDITABLE_STATES
from apps.workflow.models import AuditLog
from apps.workflow.services import WorkflowService

from .models import ProformaInvoice, ProformaInvoiceCharge, ProformaInvoiceLineItem
from .serializers import (
    AuditLogSerializer,
    ProformaInvoiceChargeSerializer,
    ProformaInvoiceLineItemSerializer,
    ProformaInvoiceSerializer,
)


# ---- Filterset for the R-02 report -----------------------------------------

class ProformaInvoiceFilterSet(django_filters.FilterSet):
    """
    Extends the base status/created_by filters with the full set required by the
    R-02 Proforma Invoice Register report: date range, exporter, consignee,
    country of final destination, incoterms, and payment terms.
    """
    pi_date_after = django_filters.DateFilter(field_name="pi_date", lookup_expr="gte")
    pi_date_before = django_filters.DateFilter(field_name="pi_date", lookup_expr="lte")

    class Meta:
        model = ProformaInvoice
        fields = [
            "status",
            "created_by",
            "exporter",
            "consignee",
            "country_of_final_destination",
            "incoterms",
            "payment_terms",
        ]


# ---- Proforma Invoice viewset -----------------------------------------------

class ProformaInvoiceViewSet(viewsets.ModelViewSet):
    """
    CRUD for Proforma Invoice headers.

    GET  /proforma-invoices/        — list all PIs (filterable by status, created_by)
    POST /proforma-invoices/        — create a new PI (Maker only)
    GET  /proforma-invoices/{id}/   — retrieve PI with nested line items + charges
    PUT/PATCH  /proforma-invoices/{id}/ — update header (only in DRAFT/REWORK, by creator)
    """
    # Constraint #29: explicit permission_classes
    permission_classes = [IsAnyRole]
    serializer_class = ProformaInvoiceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProformaInvoiceFilterSet
    ordering_fields = ["created_at", "pi_date", "pi_number"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            ProformaInvoice.objects
            .select_related(
                "exporter", "consignee", "buyer",
                "country_of_origin", "country_of_final_destination",
                "pre_carriage_by", "place_of_receipt",
                "port_of_loading", "port_of_discharge", "final_destination",
                "payment_terms", "incoterms", "bank",
                "tc_template", "created_by",
            )
            .prefetch_related("line_items", "charges")
            .all()
        )

    def perform_create(self, serializer):
        # Only Makers (and Company Admins) can create documents.
        if self.request.user.role not in (UserRole.MAKER, UserRole.COMPANY_ADMIN):
            raise PermissionDenied("Only Makers can create Proforma Invoices.")
        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        # Document must be in an editable state (DRAFT or REWORK).
        if instance.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot edit a Proforma Invoice with status '{instance.status}'."}
            )
        # Only the Maker who created the document (or Company Admin) can edit it.
        if (instance.created_by != self.request.user
                and self.request.user.role != UserRole.COMPANY_ADMIN):
            raise PermissionDenied("Only the document creator can edit this Proforma Invoice.")
        serializer.save()

    # ---- Workflow action endpoint -------------------------------------------

    @action(detail=True, methods=["post"], url_path="workflow", permission_classes=[IsAnyRole])
    def workflow(self, request, pk=None):
        """
        POST /proforma-invoices/{id}/workflow/
        Body: { "action": "SUBMIT" | "APPROVE" | "REWORK" | "PERMANENTLY_REJECT", "comment": "" }
        """
        pi = self.get_object()
        action_name = request.data.get("action", "").strip().upper()
        comment = request.data.get("comment", "")

        if not action_name:
            raise ValidationError({"action": "This field is required."})

        # FR-09 / requirements.md §13.2.1: at least one line item must exist before submission.
        if action_name == "SUBMIT" and not pi.line_items.exists():
            raise ValidationError(
                {"detail": "A Proforma Invoice must have at least one line item before it can be submitted."}
            )

        new_status = WorkflowService.transition(
            document=pi,
            document_type="proforma_invoice",
            action=action_name,
            performed_by=request.user,
            comment=comment,
        )
        return Response({"status": new_status})

    # ---- PDF endpoint -------------------------------------------------------

    @action(detail=True, methods=["get"], url_path="pdf", permission_classes=[IsAnyRole])
    def pdf(self, request, pk=None):
        """
        GET /proforma-invoices/{id}/pdf/
        Streams the PI PDF in memory. Constraint #20: never writes to disk.
        """
        from pdf.proforma_invoice import generate_pi_pdf  # local import; pdf/ package

        pi = self.get_object()
        pdf_buffer = generate_pi_pdf(pi)
        response = FileResponse(
            pdf_buffer,
            content_type="application/pdf",
            as_attachment=True,
            filename=f"{pi.pi_number}.pdf",
        )
        return response

    # ---- Signed copy upload endpoint ----------------------------------------

    @action(detail=True, methods=["post"], url_path="signed-copy", permission_classes=[IsAnyRole])
    def signed_copy(self, request, pk=None):
        """
        POST /proforma-invoices/{id}/signed-copy/
        Accepts multipart/form-data with a single field named 'file'.
        Only allowed when the PI is in Approved status (FR-08.4).
        File size is capped at SIGNED_COPY_MAX_BYTES (3 MB).
        """
        pi = self.get_object()

        if pi.status != APPROVED:
            raise ValidationError(
                {"detail": "Signed copy can only be uploaded for Approved documents."}
            )

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError({"file": "A file is required."})

        max_bytes = getattr(settings, "SIGNED_COPY_MAX_BYTES", 3 * 1024 * 1024)
        if uploaded_file.size > max_bytes:
            raise ValidationError(
                {"file": f"File size must not exceed {max_bytes // (1024 * 1024)} MB."}
            )

        # Replace any previously uploaded signed copy with the new one.
        if pi.signed_copy:
            pi.signed_copy.delete(save=False)

        pi.signed_copy = uploaded_file
        pi.save(update_fields=["signed_copy"])

        serializer = self.get_serializer(pi)
        return Response({"signed_copy_url": serializer.data["signed_copy_url"]})

    # ---- Hard delete endpoint (Super Admin only) ----------------------------

    @action(detail=True, methods=["delete"], url_path="hard-delete", permission_classes=[IsSuperAdmin])
    def hard_delete(self, request, pk=None):
        """
        DELETE /proforma-invoices/{id}/hard-delete/
        Permanently removes the PI and all its line items + charges from the database.
        Restricted to SUPER_ADMIN only.
        """
        pi = self.get_object()
        pi.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ---- Audit log endpoint -------------------------------------------------

    @action(detail=True, methods=["get"], url_path="audit-log", permission_classes=[IsAnyRole])
    def audit_log(self, request, pk=None):
        """GET /proforma-invoices/{id}/audit-log/"""
        pi = self.get_object()
        logs = AuditLog.objects.filter(
            document_type="proforma_invoice",
            document_id=pi.pk,
        ).select_related("performed_by")
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)


# ---- Line item views --------------------------------------------------------

class LineItemListCreateView(APIView):
    """
    GET  /proforma-invoices/{pi_id}/line-items/   — list line items
    POST /proforma-invoices/{pi_id}/line-items/   — add a line item
    """
    permission_classes = [IsAnyRole]  # Constraint #29

    def _get_pi(self, pi_id):
        try:
            return ProformaInvoice.objects.get(pk=pi_id)
        except ProformaInvoice.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Proforma Invoice not found.")

    def _check_editable(self, pi, user):
        if pi.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot modify line items when PI status is '{pi.status}'."}
            )
        if pi.created_by != user and user.role != UserRole.COMPANY_ADMIN:
            raise PermissionDenied("Only the document creator can modify line items.")

    def get(self, request, pi_id):
        pi = self._get_pi(pi_id)
        serializer = ProformaInvoiceLineItemSerializer(pi.line_items.all(), many=True)
        return Response(serializer.data)

    def post(self, request, pi_id):
        pi = self._get_pi(pi_id)
        self._check_editable(pi, request.user)
        serializer = ProformaInvoiceLineItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(pi=pi)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LineItemDetailView(APIView):
    """
    PUT  /proforma-invoices/{pi_id}/line-items/{lid}/ — update
    DELETE /proforma-invoices/{pi_id}/line-items/{lid}/ — delete
    """
    permission_classes = [IsAnyRole]

    def _get_objects(self, pi_id, lid, user):
        try:
            pi = ProformaInvoice.objects.get(pk=pi_id)
        except ProformaInvoice.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Proforma Invoice not found.")
        try:
            item = ProformaInvoiceLineItem.objects.get(pk=lid, pi=pi)
        except ProformaInvoiceLineItem.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Line item not found.")
        if pi.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot modify line items when PI status is '{pi.status}'."}
            )
        if pi.created_by != user and user.role != UserRole.COMPANY_ADMIN:
            raise PermissionDenied("Only the document creator can modify line items.")
        return pi, item

    def put(self, request, pi_id, lid):
        pi, item = self._get_objects(pi_id, lid, request.user)
        serializer = ProformaInvoiceLineItemSerializer(item, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pi_id, lid):
        pi, item = self._get_objects(pi_id, lid, request.user)
        serializer = ProformaInvoiceLineItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pi_id, lid):
        pi, item = self._get_objects(pi_id, lid, request.user)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---- Charge views -----------------------------------------------------------

class ChargeListCreateView(APIView):
    """
    GET  /proforma-invoices/{pi_id}/charges/   — list charges
    POST /proforma-invoices/{pi_id}/charges/   — add a charge
    """
    permission_classes = [IsAnyRole]

    def _get_pi(self, pi_id):
        try:
            return ProformaInvoice.objects.get(pk=pi_id)
        except ProformaInvoice.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Proforma Invoice not found.")

    def _check_editable(self, pi, user):
        if pi.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot modify charges when PI status is '{pi.status}'."}
            )
        if pi.created_by != user and user.role != UserRole.COMPANY_ADMIN:
            raise PermissionDenied("Only the document creator can modify charges.")

    def get(self, request, pi_id):
        pi = self._get_pi(pi_id)
        serializer = ProformaInvoiceChargeSerializer(pi.charges.all(), many=True)
        return Response(serializer.data)

    def post(self, request, pi_id):
        pi = self._get_pi(pi_id)
        self._check_editable(pi, request.user)
        serializer = ProformaInvoiceChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(pi=pi)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChargeDetailView(APIView):
    """
    PUT  /proforma-invoices/{pi_id}/charges/{cid}/ — update
    DELETE /proforma-invoices/{pi_id}/charges/{cid}/ — delete
    """
    permission_classes = [IsAnyRole]

    def _get_objects(self, pi_id, cid, user):
        try:
            pi = ProformaInvoice.objects.get(pk=pi_id)
        except ProformaInvoice.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Proforma Invoice not found.")
        try:
            charge = ProformaInvoiceCharge.objects.get(pk=cid, pi=pi)
        except ProformaInvoiceCharge.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Charge not found.")
        if pi.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot modify charges when PI status is '{pi.status}'."}
            )
        if pi.created_by != user and user.role != UserRole.COMPANY_ADMIN:
            raise PermissionDenied("Only the document creator can modify charges.")
        return pi, charge

    def put(self, request, pi_id, cid):
        pi, charge = self._get_objects(pi_id, cid, request.user)
        serializer = ProformaInvoiceChargeSerializer(charge, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pi_id, cid):
        pi, charge = self._get_objects(pi_id, cid, request.user)
        serializer = ProformaInvoiceChargeSerializer(charge, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pi_id, cid):
        pi, charge = self._get_objects(pi_id, cid, request.user)
        charge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
