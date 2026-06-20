"""
Views for Certificate of Analysis (FR-COA-05 through FR-COA-08).
Rule #10: All views explicitly declare permission_classes.
"""
import django_filters
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import UserRole
from apps.accounts.permissions import IsAnyRole, IsMakerOrAdmin
from apps.workflow.constants import EDITABLE_STATES
from apps.workflow.models import AuditLog
from apps.workflow.services import WorkflowService

from tradetocs.pagination import StandardPageNumberPagination

from .models import CertificateOfAnalysis
from .serializers import AuditLogSerializer, CertificateOfAnalysisSerializer


class COAFilterSet(django_filters.FilterSet):
    class Meta:
        model = CertificateOfAnalysis
        fields = ["status", "customer"]


class CertificateOfAnalysisViewSet(viewsets.ModelViewSet):
    """
    CRUD for Certificate of Analysis.
    GET  /coas/       — list
    POST /coas/       — create (Maker)
    GET  /coas/{id}/  — retrieve
    PATCH /coas/{id}/ — update (only in DRAFT/REWORK)
    """
    permission_classes = [IsAnyRole]
    # Opt in to the ScopedRateThrottle scope configured in settings.py (100/day).
    throttle_scope = "document_creation"
    pagination_class = StandardPageNumberPagination
    serializer_class = CertificateOfAnalysisSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = COAFilterSet
    search_fields = ["coa_number", "batch_number"]
    ordering_fields = ["created_at", "coa_number"]
    ordering = ["-created_at"]

    def get_permissions(self):
        # Makers and Admins can create and edit COAs; Checkers approve via workflow actions.
        # IsAuthenticated is explicit because get_permissions() overrides the global default.
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsMakerOrAdmin()]
        return [IsAuthenticated(), IsAnyRole()]

    def get_queryset(self):
        return (
            CertificateOfAnalysis.objects
            .select_related(
                "product_grade__product",
                "customer",
                "package_uom",
                "package_type",
                "footer_organisation",
                "created_by",
            )
            .prefetch_related("parameters__unit", "parameters__parameter", "parameters__test_method")
            .all()
        )

    def perform_create(self, serializer):
        if self.request.user.role not in (UserRole.MAKER, UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN):
            raise PermissionDenied("Only Makers can create COAs.")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot edit a COA with status '{instance.status}'."}
            )
        if self.request.user.role == UserRole.CHECKER:
            raise PermissionDenied("Checkers cannot edit COAs.")
        serializer.save()

    @action(detail=True, methods=["post"], url_path="submit", permission_classes=[IsAuthenticated, IsAnyRole])
    def submit(self, request, pk=None):
        """POST /coas/{id}/submit/ — Maker submits for approval."""
        coa = self.get_object()
        if not coa.parameters.exists():
            raise ValidationError(
                {"detail": "A COA must have at least one test parameter before it can be submitted."}
            )
        new_status = WorkflowService.transition(
            document=coa,
            document_type="certificate_of_analysis",
            action="SUBMIT",
            performed_by=request.user,
        )
        return Response({"status": new_status})

    @action(detail=True, methods=["post"], url_path="approve", permission_classes=[IsAuthenticated, IsAnyRole])
    def approve(self, request, pk=None):
        """POST /coas/{id}/approve/ — Checker approves."""
        coa = self.get_object()
        new_status = WorkflowService.transition(
            document=coa,
            document_type="certificate_of_analysis",
            action="APPROVE",
            performed_by=request.user,
        )
        return Response({"status": new_status})

    @action(detail=True, methods=["post"], url_path="reject", permission_classes=[IsAuthenticated, IsAnyRole])
    def reject(self, request, pk=None):
        """POST /coas/{id}/reject/ — Checker permanently rejects (comment required)."""
        coa = self.get_object()
        comment = request.data.get("comment", "")
        new_status = WorkflowService.transition(
            document=coa,
            document_type="certificate_of_analysis",
            action="PERMANENTLY_REJECT",
            performed_by=request.user,
            comment=comment,
        )
        return Response({"status": new_status})

    @action(detail=True, methods=["post"], url_path="rework", permission_classes=[IsAuthenticated, IsAnyRole])
    def rework(self, request, pk=None):
        """POST /coas/{id}/rework/ — Checker sends back for rework (comment required)."""
        coa = self.get_object()
        comment = request.data.get("comment", "")
        new_status = WorkflowService.transition(
            document=coa,
            document_type="certificate_of_analysis",
            action="REWORK",
            performed_by=request.user,
            comment=comment,
        )
        return Response({"status": new_status})

    @action(detail=True, methods=["get"], url_path="pdf", permission_classes=[IsAuthenticated, IsAnyRole])
    def pdf(self, request, pk=None):
        """GET /coas/{id}/pdf/ — Streams COA PDF. Never writes to disk (Rule #9)."""
        from pdf.certificate_of_analysis import generate_coa_pdf
        coa = self.get_object()
        pdf_buffer = generate_coa_pdf(coa)
        return FileResponse(
            pdf_buffer,
            content_type="application/pdf",
            as_attachment=True,
            filename=f"{coa.coa_number}.pdf",
        )

    @action(detail=True, methods=["get"], url_path="audit-log", permission_classes=[IsAuthenticated, IsAnyRole])
    def audit_log(self, request, pk=None):
        """GET /coas/{id}/audit-log/"""
        coa = self.get_object()
        logs = AuditLog.objects.filter(
            document_type="certificate_of_analysis",
            document_id=coa.pk,
        ).select_related("performed_by")
        return Response(AuditLogSerializer(logs, many=True).data)
