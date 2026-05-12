from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proforma_invoice", "0010_add_packaging_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="proformainvoicelineitem",
            name="rate",
            field=models.DecimalField(max_digits=15, decimal_places=4),
        ),
    ]
