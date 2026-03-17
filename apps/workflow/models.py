from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Immutable record of every document status change.
    Written inside the same transaction.atomic() as the status update (constraint #12).
    Never deleted by the application.
    """
    document_type = models.CharField(
        max_length=50,
        help_text="e.g. 'proforma_invoice', 'packing_list', 'commercial_invoice'",
    )
    document_id = models.PositiveIntegerField(help_text="PK of the affected document")
    # Snapshot of the document number at time of action (documents can be renumbered in theory)
    document_number = models.CharField(max_length=30)

    action = models.CharField(max_length=30, help_text="e.g. SUBMIT, APPROVE, REWORK")
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)

    # comment is nullable — only required for REJECT/REWORK/PERMANENTLY_REJECT (constraint #15)
    comment = models.TextField(blank=True, default="")

    # Constraint #7: PROTECT so deleting a User doesn't erase audit history
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_logs",
    )
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workflow_audit_log"
        ordering = ["-performed_at"]
        indexes = [
            # Constraint: index on (document_type, document_id) for audit trail queries
            models.Index(fields=["document_type", "document_id"], name="audit_log_doc_idx"),
        ]

    def __str__(self):
        return f"{self.document_number} | {self.action} by {self.performed_by_id} at {self.performed_at}"
