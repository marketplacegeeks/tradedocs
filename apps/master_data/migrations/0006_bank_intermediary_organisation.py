from django.db import migrations, models
import django.db.models.deletion
import apps.master_data.models


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0005_reference_data_soft_delete"),
    ]

    operations = [
        # 1. Organisation FK (nullable so existing rows are unaffected)
        migrations.AddField(
            model_name="bank",
            name="organisation",
            field=models.ForeignKey(
                blank=True,
                help_text="Exporter organisation this bank account belongs to",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="banks",
                to="master_data.organisation",
            ),
        ),
        # 2. Intermediary institution fields
        migrations.AddField(
            model_name="bank",
            name="intermediary_bank_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="bank",
            name="intermediary_account_number",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="bank",
            name="intermediary_swift_code",
            field=models.CharField(
                blank=True,
                max_length=11,
                validators=[apps.master_data.models._validate_swift],
                help_text="Optional. 8 or 11 uppercase alphanumeric characters (ISO 9362).",
            ),
        ),
        migrations.AddField(
            model_name="bank",
            name="intermediary_currency",
            field=models.ForeignKey(
                blank=True,
                help_text="Currency for which this intermediary routing applies (e.g. USD)",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="intermediary_banks",
                to="master_data.currency",
            ),
        ),
    ]
