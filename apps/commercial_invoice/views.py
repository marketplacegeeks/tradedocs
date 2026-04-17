"""
Views for CommercialInvoice and CommercialInvoiceLineItem (FR-14M).

CI is created and workflow-transitioned exclusively via the PackingList endpoint.
These views provide read access and targeted updates (financial fields, line item rates).

Constraint #10: All views explicitly declare permission_classes.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.accounts.models import UserRole
from apps.accounts.permissions import IsAnyRole
from apps.workflow.constants import EDITABLE_STATES

from .models import CommercialInvoice, CommercialInvoiceLineItem
from .serializers import (
    CommercialInvoiceLineItemSerializer,
    CommercialInvoiceSerializer,
    CommercialInvoiceUpdateSerializer,
)


class CommercialInvoiceViewSet(viewsets.ModelViewSet):
    """
    Read + limited write for CommercialInvoice records.

    GET  /commercial-invoices/          — list
    GET  /commercial-invoices/{id}/     — retrieve with nested line items
    PATCH /commercial-invoices/{id}/    — update financial fields only (Draft/Rework)

    Create, delete, and workflow actions are handled by the PackingList endpoint.
    """
    permission_classes = [IsAnyRole]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "created_by"]
    ordering_fields = ["created_at", "ci_date", "ci_number"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            CommercialInvoice.objects
            .select_related("packing_list", "bank__bank_country", "bank__currency", "created_by")
            .prefetch_related("line_items__uom")
            .all()
        )

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return CommercialInvoiceUpdateSerializer
        return CommercialInvoiceSerializer

    def create(self, request, *args, **kwargs):
        raise ValidationError(
            {"detail": "Commercial Invoices are created automatically via the Packing List endpoint."}
        )

    def destroy(self, request, *args, **kwargs):
        raise ValidationError(
            {"detail": "Commercial Invoices are deleted via the Packing List endpoint."}
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot edit a Commercial Invoice with status '{instance.status}'."}
            )
        pl = instance.packing_list
        if (pl.created_by != self.request.user
                and self.request.user.role != UserRole.COMPANY_ADMIN):
            raise PermissionDenied("Only the document creator can edit this Commercial Invoice.")
        serializer.save()

    # ---- Signed copy upload endpoint ----------------------------------------

    @action(detail=True, methods=["post"], url_path="signed-copy", permission_classes=[IsAnyRole])
    def signed_copy(self, request, pk=None):
        """
        POST /commercial-invoices/{id}/signed-copy/
        Accepts multipart/form-data with a single field named 'file'.
        Only allowed when the CI is in Approved status (FR-08.4).
        File size is capped at SIGNED_COPY_MAX_BYTES (3 MB).
        """
        from django.conf import settings as django_settings
        from apps.workflow.constants import APPROVED

        ci = self.get_object()

        if ci.status != APPROVED:
            raise ValidationError(
                {"detail": "Signed copy can only be uploaded for Approved documents."}
            )

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError({"file": "A file is required."})

        max_bytes = getattr(django_settings, "SIGNED_COPY_MAX_BYTES", 3 * 1024 * 1024)
        if uploaded_file.size > max_bytes:
            raise ValidationError(
                {"file": f"File size must not exceed {max_bytes // (1024 * 1024)} MB."}
            )

        # Replace any previously uploaded signed copy with the new one.
        if ci.signed_copy:
            ci.signed_copy.delete(save=False)

        ci.signed_copy = uploaded_file
        ci.save(update_fields=["signed_copy"])

        serializer = self.get_serializer(ci)
        return Response({"signed_copy_url": serializer.data["signed_copy_url"]})


class CommercialInvoiceLineItemViewSet(viewsets.ModelViewSet):
    """
    Line item updates for the Final Rates section (FR-14M.8B).

    GET  /ci-line-items/?ci={id}   — list line items for a CI
    PATCH /ci-line-items/{id}/     — update rate and/or packages_kind
    """
    permission_classes = [IsAnyRole]
    serializer_class = CommercialInvoiceLineItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["ci"]

    def get_queryset(self):
        return CommercialInvoiceLineItem.objects.select_related("uom", "ci__packing_list").all()

    def create(self, request, *args, **kwargs):
        raise ValidationError(
            {"detail": "Line items are generated automatically from container items."}
        )

    def destroy(self, request, *args, **kwargs):
        raise ValidationError(
            {"detail": "Line items are managed automatically. Delete container items instead."}
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        ci = instance.ci
        if ci.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot edit rates when status is '{ci.status}'."}
            )
        pl = ci.packing_list
        if (pl.created_by != self.request.user
                and self.request.user.role != UserRole.COMPANY_ADMIN):
            raise PermissionDenied("Only the document creator can edit rates.")
        serializer.save()
