from django.apps import AppConfig


class ManualEditsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.manual_edits"
    label = "manual_edits"
    verbose_name = "Manual Edits"
