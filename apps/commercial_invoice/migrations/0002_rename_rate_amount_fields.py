# Rename rate_usd → rate, amount_usd → amount for CommercialInvoiceLineItem

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commercial_invoice', '0001_initial'),
    ]

    operations = [
        # Rename fields in one step (no data loss, just metadata change)
        migrations.RenameField(
            model_name='commercialinvoicelineitem',
            old_name='rate_usd',
            new_name='rate',
        ),
        migrations.RenameField(
            model_name='commercialinvoicelineitem',
            old_name='amount_usd',
            new_name='amount',
        ),
    ]
