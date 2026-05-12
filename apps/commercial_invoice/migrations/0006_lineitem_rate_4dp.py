from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("commercial_invoice", "0005_merge_20260417_1818"),
    ]

    operations = [
        migrations.AlterField(
            model_name="commercialinvoicelineitem",
            name="rate",
            field=models.DecimalField(max_digits=15, decimal_places=4),
        ),
    ]
