import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0006_bank_intermediary_organisation"),
        ("proforma_invoice", "0002_signed_copy"),
    ]

    operations = [
        migrations.AddField(
            model_name="proformainvoice",
            name="place_of_receipt_by_pre_carrier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="pi_place_of_receipt_by_pre_carrier",
                to="master_data.location",
            ),
        ),
    ]
