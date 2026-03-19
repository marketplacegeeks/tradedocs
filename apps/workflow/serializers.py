"""
Shared serializers for the workflow app.

AuditLogSerializer is used by every document app (PI, PL, CI) so it lives
here rather than being duplicated per app.
"""

from rest_framework import serializers


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
