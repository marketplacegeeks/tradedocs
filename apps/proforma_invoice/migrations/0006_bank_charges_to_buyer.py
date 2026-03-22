from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proforma_invoice', '0005_hsn_code_max_length_10'),
    ]

    operations = [
        migrations.AddField(
            model_name='proformainvoice',
            name='bank_charges_to_buyer',
            field=models.BooleanField(default=False),
        ),
    ]
