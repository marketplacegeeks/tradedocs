from django.conf import settings
from django.db import models


class DocumentEditTracking(models.Model):
    """
    One row per document across all document types (PI/PL/CI/PO/COA).
    Tracks when a document's PDF/Word was first generated, and the most
    recently uploaded manually-edited replacement file (if any).
    Backs the "Manual Edits" page.
    """

    document_type = models.CharField(
        max_length=50,
        help_text="e.g. 'proforma_invoice', 'packing_list' — matches AuditLog.document_type",
    )
    document_id = models.PositiveIntegerField(help_text="PK of the affected document")
    document_number = models.CharField(max_length=30)

    first_generated_at = models.DateTimeField(null=True, blank=True)

    edited_word_file = models.FileField(upload_to="manual_edits/word/", null=True, blank=True)
    edited_pdf_file = models.FileField(upload_to="manual_edits/pdf/", null=True, blank=True)
    edit_comment = models.TextField(blank=True, default="")
    # Constraint #7: PROTECT so deleting a User doesn't erase the manual-edit trail.
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="manual_document_edits",
    )
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "manual_edits_document_tracking"
        constraints = [
            models.UniqueConstraint(
                fields=["document_type", "document_id"],
                name="unique_document_tracking",
            ),
        ]

    def __str__(self):
        return f"{self.document_number} ({self.document_type})"
