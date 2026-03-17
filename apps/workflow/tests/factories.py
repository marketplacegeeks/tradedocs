import factory
from apps.workflow.models import AuditLog
from apps.accounts.tests.factories import UserFactory


class AuditLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuditLog

    document_type = "proforma_invoice"
    document_id = factory.Sequence(lambda n: n + 1)
    document_number = factory.Sequence(lambda n: f"PI-2026-{n + 1:04d}")
    action = "SUBMIT"
    from_status = "DRAFT"
    to_status = "PENDING_APPROVAL"
    comment = ""
    performed_by = factory.SubFactory(UserFactory)
