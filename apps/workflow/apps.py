from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.workflow"
    label = "workflow"

    def ready(self):
        # Import signals module to register the post_save handler on AuditLog.
        # This must live in ready() to ensure models are fully loaded first.
        import apps.workflow.signals  # noqa: F401
