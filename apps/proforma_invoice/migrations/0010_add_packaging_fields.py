# Add kind_of_packages and marks_and_nos fields to ProformaInvoice

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proforma_invoice', '0009_remove_usd_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='proformainvoice',
            name='kind_of_packages',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='proformainvoice',
            name='marks_and_nos',
            field=models.TextField(blank=True, default=''),
        ),
    ]
