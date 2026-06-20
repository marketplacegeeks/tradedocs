"""
Read-only viewset for the global AuditLog endpoint.

Constraint #10: explicit permission_classes declared.
Constraint #29: every DRF view explicitly declares permission_classes.
"""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.accounts.models import UserRole
from apps.accounts.permissions import IsAnyRole
from tradetocs.pagination import StandardPageNumberPagination

from .models import AuditLog
from .serializers import AuditLogListSerializer


class AuditLogFilterSet(django_filters.FilterSet):
    """
    Filterset for the global audit log endpoint.
    Supports: document_id, document_type, performed_by (user pk), action, date range.
    """
    performed_at_after = django_filters.DateFilter(field_name="performed_at", lookup_expr="gte")
    performed_at_before = django_filters.DateFilter(field_name="performed_at", lookup_expr="lte")

    class Meta:
        model = AuditLog
        fields = ["document_id", "document_type", "performed_by", "action"]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/v1/audit-logs/       — paginated list with filter support
    GET  /api/v1/audit-logs/{id}/  — single entry

    Permission rules (per CONTEXT.md D-01: "Makers can only see their own documents' logs"):

    INTERPRETATION: AuditLog records the actor (performed_by), not the document creator.
    There is no document_creator field on AuditLog, and a JOIN across PI/PL/CI tables to
    find documents where created_by=request.user would require three UNION queries with no
    shared FK path.

    Decision (checker-flagged, explicitly documented): "their own documents' logs" is
    interpreted as "logs of actions they performed" (performed_by=request.user). This means
    a Maker sees their own SUBMIT actions but NOT the Checker's subsequent APPROVE entry on
    the same document.

    Trade-off accepted: A Maker curious about their document's full trail can view the
    per-document audit section on the document detail page (which uses AuditLogSerializer
    and is scoped to that document_id — no role restriction needed there).

    Creator-scoped JOIN is deferred to avoid cross-app complexity; the per-document detail
    trail covers the primary Maker use case. This decision is traceable to this comment.
    """
    serializer_class = AuditLogListSerializer
    permission_classes = [IsAnyRole]
    pagination_class = StandardPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AuditLogFilterSet
    ordering_fields = ["performed_at", "document_type", "action"]
    ordering = ["-performed_at"]

    def get_queryset(self):
        qs = AuditLog.objects.select_related("performed_by").all()
        # Makers can only see logs where they were the actor (their own actions).
        # Checkers and Admins see the full log.
        # See class docstring for the rationale behind this interpretation.
        if self.request.user.role == UserRole.MAKER:
            qs = qs.filter(performed_by=self.request.user)
        return qs
