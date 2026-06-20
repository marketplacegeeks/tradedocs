"""
Shared serializers for the workflow app.

AuditLogSerializer is used by every document app (PI, PL, CI) so it lives
here rather than being duplicated per app.

AuditLogListSerializer is used by the global AuditLogViewSet endpoint.
"""

from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.Serializer):
    """Read-only serializer for AuditLog entries."""
    id = serializers.IntegerField()
    action = serializers.CharField()
    from_status = serializers.CharField()
    to_status = serializers.CharField()
    # comment is blank string when no comment was given — never null
    comment = serializers.CharField()
    performed_by_name = serializers.SerializerMethodField()
    performed_at = serializers.DateTimeField()

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.full_name or obj.performed_by.email
        return None


class AuditLogListSerializer(serializers.ModelSerializer):
    """Full serializer for the global audit log list endpoint."""
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id", "document_type", "document_id", "document_number",
            "action", "from_status", "to_status", "comment",
            "performed_by_name", "performed_at",
        ]
        read_only_fields = fields

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.full_name or obj.performed_by.email
        return None
