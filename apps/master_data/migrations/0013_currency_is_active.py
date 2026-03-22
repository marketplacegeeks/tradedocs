from django.db import migrations, models


# Minimum set of currencies required by FR-PO-01.
# Uses get_or_create so running this migration twice is safe.
SEED_CURRENCIES = [
    ("AED", "UAE Dirham"),
    ("EUR", "Euro"),
    ("GBP", "Pound Sterling"),
    ("INR", "Indian Rupee"),
    ("USD", "US Dollar"),
]


def seed_currencies(apps, schema_editor):
    Currency = apps.get_model("master_data", "Currency")
    for code, name in SEED_CURRENCIES:
        Currency.objects.get_or_create(code=code, defaults={"name": name, "is_active": True})


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0012_make_email_contact_name_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="currency",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(seed_currencies, migrations.RunPython.noop),
    ]
