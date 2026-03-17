from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("document_type", models.CharField(help_text="e.g. 'proforma_invoice', 'packing_list', 'commercial_invoice'", max_length=50)),
                ("document_id", models.PositiveIntegerField(help_text="PK of the affected document")),
                ("document_number", models.CharField(max_length=30)),
                ("action", models.CharField(help_text="e.g. SUBMIT, APPROVE, REWORK", max_length=30)),
                ("from_status", models.CharField(max_length=30)),
                ("to_status", models.CharField(max_length=30)),
                ("comment", models.TextField(blank=True, default="")),
                ("performed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "performed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "workflow_audit_log",
                "ordering": ["-performed_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["document_type", "document_id"], name="audit_log_doc_idx"),
        ),
    ]
