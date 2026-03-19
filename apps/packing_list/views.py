"""
Views for PackingList, Container, ContainerItem (FR-14M).

Constraint #10: All views explicitly declare permission_classes.
Constraint #11 / #12: workflow transitions go through WorkflowService only.
"""

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.accounts.models import UserRole
from apps.accounts.permissions import IsAnyRole
from apps.workflow.constants import DRAFT, EDITABLE_STATES
from apps.workflow.models import AuditLog
from apps.workflow.services import WorkflowService

from .models import Container, ContainerItem, PackingList
from .serializers import (
    ContainerItemSerializer,
    ContainerSerializer,
    PackingListSerializer,
    PackingListWriteSerializer,
)


# ---- PackingList viewset ----------------------------------------------------

class PackingListViewSet(viewsets.ModelViewSet):
    """
    CRUD for PackingList headers (FR-14M).
    Creating a PL also creates the linked CI atomically.

    GET  /packing-lists/          — list
    POST /packing-lists/          — create PL+CI (Maker/Admin only)
    GET  /packing-lists/{id}/     — retrieve with nested containers + CI info
    PATCH /packing-lists/{id}/    — update header (Draft/Rework, creator only)
    DELETE /packing-lists/{id}/   — delete PL+CI (Draft only, creator only)
    POST /packing-lists/{id}/workflow/ — joint workflow action
    GET  /packing-lists/{id}/audit-log/ — audit history
    """
    permission_classes = [IsAnyRole]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "created_by"]
    ordering_fields = ["created_at", "pl_date", "pl_number"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            PackingList.objects
            .select_related(
                "proforma_invoice",
                "exporter", "consignee", "buyer", "notify_party",
                "pre_carriage_by",
                "place_of_receipt", "place_of_receipt_by_pre_carrier",
                "port_of_loading", "port_of_discharge", "final_destination",
                "country_of_origin", "country_of_final_destination",
                "incoterms", "payment_terms",
                "created_by",
            )
            .prefetch_related(
                "containers__items__uom",
            )
            .all()
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PackingListWriteSerializer
        return PackingListSerializer

    def create(self, request, *args, **kwargs):
        """Override to return the full read representation after create."""
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        self.perform_create(write_serializer)
        instance = write_serializer.instance
        read_serializer = PackingListSerializer(instance, context=self.get_serializer_context())
        from rest_framework import status as drf_status
        return Response(read_serializer.data, status=drf_status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Override to return the full read representation after update."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        write_serializer = self.get_serializer(instance, data=request.data, partial=partial)
        write_serializer.is_valid(raise_exception=True)
        self.perform_update(write_serializer)
        read_serializer = PackingListSerializer(
            write_serializer.instance, context=self.get_serializer_context()
        )
        return Response(read_serializer.data)

    def perform_create(self, serializer):
        if self.request.user.role not in (UserRole.MAKER, UserRole.COMPANY_ADMIN):
            raise PermissionDenied("Only Makers can create Packing Lists.")

        # Pop CI-specific fields before saving the PL.
        ci_data = {
            "ci_date": serializer.validated_data.pop("ci_date", None),
            "bank_id": serializer.validated_data.pop("bank", None),
            "fob_rate": serializer.validated_data.pop("fob_rate", None),
            "freight": serializer.validated_data.pop("freight", None),
            "insurance": serializer.validated_data.pop("insurance", None),
            "lc_details": serializer.validated_data.pop("lc_details", ""),
        }

        from apps.packing_list.services import generate_document_number as gen_pl
        from apps.commercial_invoice.services import generate_document_number as gen_ci
        from apps.commercial_invoice.models import CommercialInvoice
        import datetime

        with transaction.atomic():
            pl_number = gen_pl()
            pl = serializer.save(
                pl_number=pl_number,
                created_by=self.request.user,
            )

            ci_number = gen_ci()
            CommercialInvoice.objects.create(
                ci_number=ci_number,
                ci_date=ci_data["ci_date"] or datetime.date.today(),
                packing_list=pl,
                bank_id=ci_data["bank_id"],
                fob_rate=ci_data["fob_rate"],
                freight=ci_data["freight"],
                insurance=ci_data["insurance"],
                lc_details=ci_data["lc_details"],
                status=DRAFT,
                created_by=self.request.user,
            )

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot edit a Packing List with status '{instance.status}'."}
            )
        if (instance.created_by != self.request.user
                and self.request.user.role != UserRole.COMPANY_ADMIN):
            raise PermissionDenied("Only the document creator can edit this Packing List.")

        # Pop CI fields and apply them to the linked CI.
        ci_data = {
            "ci_date": serializer.validated_data.pop("ci_date", None),
            "bank_id": serializer.validated_data.pop("bank", None),
            "fob_rate": serializer.validated_data.pop("fob_rate", None),
            "freight": serializer.validated_data.pop("freight", None),
            "insurance": serializer.validated_data.pop("insurance", None),
            "lc_details": serializer.validated_data.pop("lc_details", None),
        }

        with transaction.atomic():
            pl = serializer.save()
            try:
                ci = pl.commercial_invoice
            except Exception:
                ci = None
            update_fields = []
            if ci_data["ci_date"] is not None:
                ci.ci_date = ci_data["ci_date"]
                update_fields.append("ci_date")
            if ci_data["bank_id"] is not None:
                ci.bank_id = ci_data["bank_id"]
                update_fields.append("bank_id")
            if ci_data["fob_rate"] is not None:
                ci.fob_rate = ci_data["fob_rate"]
                update_fields.append("fob_rate")
            if ci_data["freight"] is not None:
                ci.freight = ci_data["freight"]
                update_fields.append("freight")
            if ci_data["insurance"] is not None:
                ci.insurance = ci_data["insurance"]
                update_fields.append("insurance")
            if ci_data["lc_details"] is not None:
                ci.lc_details = ci_data["lc_details"]
                update_fields.append("lc_details")
            if update_fields and ci is not None:
                update_fields.append("updated_at")
                ci.save(update_fields=update_fields)

    def perform_destroy(self, instance):
        """FR-14M.12: Delete only allowed in Draft state; also deletes the linked CI."""
        if instance.status != DRAFT:
            raise ValidationError(
                {"detail": "Only Draft documents can be deleted."}
            )
        if (instance.created_by != self.request.user
                and self.request.user.role != UserRole.COMPANY_ADMIN):
            raise PermissionDenied("Only the document creator can delete this Packing List.")
        # Cascade: CI will be deleted by the database (CASCADE on packing_list FK is OneToOne).
        # But CommercialInvoice uses PROTECT, so we delete CI explicitly first.
        with transaction.atomic():
            try:
                instance.commercial_invoice.delete()
            except Exception:
                pass
            instance.delete()

    # ---- Workflow action endpoint -------------------------------------------

    @action(detail=True, methods=["post"], url_path="workflow", permission_classes=[IsAnyRole])
    def workflow(self, request, pk=None):
        """
        POST /packing-lists/{id}/workflow/
        Body: { "action": "SUBMIT"|"APPROVE"|"REWORK"|"PERMANENTLY_REJECT", "comment": "" }
        Transitions both PL and CI atomically (FR-14M.12).
        """
        pl = self.get_object()
        action_name = request.data.get("action", "").strip().upper()
        comment = request.data.get("comment", "")

        if not action_name:
            raise ValidationError({"action": "This field is required."})

        new_status = WorkflowService.transition_joint(
            packing_list=pl,
            action=action_name,
            performed_by=request.user,
            comment=comment,
        )
        return Response({"status": new_status})

    # ---- PDF endpoint -------------------------------------------------------

    @action(detail=True, methods=["get"], url_path="pdf", permission_classes=[IsAnyRole])
    def pdf(self, request, pk=None):
        """
        GET /packing-lists/{id}/pdf/
        Streams the combined PL+CI PDF.

        Access rules (FR-14M.13):
          Maker / Checker — Approved state only
          Company Admin   — any state
        Constraint #20: PDF is generated in-memory and streamed; never written to disk.
        """
        from django.http import FileResponse
        from pdf.packing_list import generate_pl_ci_pdf
        from apps.workflow.constants import APPROVED

        pl = self.get_object()

        # Gate by role + status
        if request.user.role != UserRole.COMPANY_ADMIN:
            if pl.status != APPROVED:
                raise PermissionDenied(
                    "PDF download is only available for Approved documents."
                )

        buffer = generate_pl_ci_pdf(pl)
        filename = f"{pl.pl_number}.pdf"
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )

    # ---- Signed copy upload endpoint ----------------------------------------

    @action(detail=True, methods=["post"], url_path="signed-copy", permission_classes=[IsAnyRole])
    def signed_copy(self, request, pk=None):
        """
        POST /packing-lists/{id}/signed-copy/
        Accepts multipart/form-data with a single field named 'file'.
        Only allowed when the PL is in Approved status (FR-08.4).
        File size is capped at SIGNED_COPY_MAX_BYTES (3 MB).
        """
        from django.conf import settings as django_settings
        from apps.workflow.constants import APPROVED

        pl = self.get_object()

        if pl.status != APPROVED:
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
        if pl.signed_copy:
            pl.signed_copy.delete(save=False)

        pl.signed_copy = uploaded_file
        pl.save(update_fields=["signed_copy"])

        serializer = self.get_serializer(pl)
        return Response({"signed_copy_url": serializer.data["signed_copy_url"]})

    # ---- Audit log endpoint -------------------------------------------------

    @action(detail=True, methods=["get"], url_path="audit-log", permission_classes=[IsAnyRole])
    def audit_log(self, request, pk=None):
        pl = self.get_object()
        from apps.workflow.models import AuditLog
        # Return audit entries for both PL and its CI.
        ci_id = None
        try:
            ci_id = pl.commercial_invoice.pk
        except Exception:
            pass

        entries = AuditLog.objects.filter(
            document_type="packing_list", document_id=pl.pk
        ).order_by("-created_at")

        data = [
            {
                "id": e.pk,
                "document_type": e.document_type,
                "document_number": e.document_number,
                "action": e.action,
                "from_status": e.from_status,
                "to_status": e.to_status,
                "comment": e.comment,
                "performed_by": e.performed_by.full_name or e.performed_by.email,
                "created_at": e.created_at,
            }
            for e in entries
        ]
        return Response(data)


# ---- Container viewset ------------------------------------------------------

class ContainerViewSet(viewsets.ModelViewSet):
    """
    CRUD for Container records (FR-14M.4).

    GET  /containers/?packing_list={id}  — list containers for a PL
    POST /containers/                    — add container
    GET/PATCH/PUT /containers/{id}/      — update
    DELETE /containers/{id}/             — remove (Draft/Rework only)
    """
    permission_classes = [IsAnyRole]
    serializer_class = ContainerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["packing_list"]

    def get_queryset(self):
        return Container.objects.prefetch_related("items__uom").all()

    def _check_pl_editable(self, packing_list):
        """Raise if the parent PL is not in an editable state."""
        if packing_list.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot modify containers when Packing List status is '{packing_list.status}'."}
            )
        if (packing_list.created_by != self.request.user
                and self.request.user.role != UserRole.COMPANY_ADMIN):
            raise PermissionDenied("Only the document creator can modify containers.")

    def perform_create(self, serializer):
        pl = serializer.validated_data.get("packing_list")
        self._check_pl_editable(pl)
        container = serializer.save()
        # Rebuild CI line items after structure changes.
        from apps.commercial_invoice.services import rebuild_ci_line_items
        rebuild_ci_line_items(pl)

    def perform_update(self, serializer):
        instance = self.get_object()
        self._check_pl_editable(instance.packing_list)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_pl_editable(instance.packing_list)
        pl = instance.packing_list
        instance.delete()
        from apps.commercial_invoice.services import rebuild_ci_line_items
        rebuild_ci_line_items(pl)

    @action(detail=True, methods=["post"], url_path="copy", permission_classes=[IsAnyRole])
    def copy(self, request, pk=None):
        """
        POST /containers/{id}/copy/
        Duplicates the container and all its items (FR-14M.4 Copy Container).
        Rates are not copied — those live on CI line items.
        Container ref, marks & numbers, and seal number are left blank.
        """
        source = self.get_object()
        self._check_pl_editable(source.packing_list)

        with transaction.atomic():
            new_container = Container.objects.create(
                packing_list=source.packing_list,
                container_ref="",
                marks_numbers="",
                seal_number="",
                tare_weight=source.tare_weight,
            )
            for item in source.items.all():
                ContainerItem.objects.create(
                    container=new_container,
                    hsn_code=item.hsn_code,
                    item_code=item.item_code,
                    packages_kind=item.packages_kind,
                    description=item.description,
                    batch_details=item.batch_details,
                    uom=item.uom,
                    quantity=item.quantity,
                    net_weight=item.net_weight,
                    inner_packing_weight=item.inner_packing_weight,
                )

        serializer = self.get_serializer(new_container)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ---- ContainerItem viewset --------------------------------------------------

class ContainerItemViewSet(viewsets.ModelViewSet):
    """
    CRUD for ContainerItem records (FR-14M.8A).

    GET  /container-items/?container={id}  — list items for a container
    POST /container-items/                 — add item
    GET/PATCH/PUT /container-items/{id}/   — update
    DELETE /container-items/{id}/          — remove
    """
    permission_classes = [IsAnyRole]
    serializer_class = ContainerItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["container", "container__packing_list"]

    def get_queryset(self):
        return ContainerItem.objects.select_related("uom", "container__packing_list").all()

    def _check_editable(self, container):
        pl = container.packing_list
        if pl.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot modify items when Packing List status is '{pl.status}'."}
            )
        if (pl.created_by != self.request.user
                and self.request.user.role != UserRole.COMPANY_ADMIN):
            raise PermissionDenied("Only the document creator can modify container items.")

    def perform_create(self, serializer):
        container = serializer.validated_data.get("container")
        self._check_editable(container)
        serializer.save()
        from apps.commercial_invoice.services import rebuild_ci_line_items
        rebuild_ci_line_items(container.packing_list)

    def perform_update(self, serializer):
        self._check_editable(self.get_object().container)
        serializer.save()
        from apps.commercial_invoice.services import rebuild_ci_line_items
        rebuild_ci_line_items(self.get_object().container.packing_list)

    def perform_destroy(self, instance):
        pl = instance.container.packing_list
        self._check_editable(instance.container)
        instance.delete()
        from apps.commercial_invoice.services import rebuild_ci_line_items
        rebuild_ci_line_items(pl)
