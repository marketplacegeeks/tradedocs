# Generated manually for multi-currency support

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0013_currency_is_active'),
        ('proforma_invoice', '0006_bank_charges_to_buyer'),
    ]

    operations = [
        # Add currency FK to ProformaInvoice (nullable initially for safe migration)
        migrations.AddField(
            model_name='proformainvoice',
            name='currency',
            field=models.ForeignKey(
                blank=True,
                help_text='Currency for all monetary values on this Proforma Invoice',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='master_data.currency'
            ),
        ),

        # ProformaInvoiceLineItem: add new "rate" and "amount" fields
        migrations.AddField(
            model_name='proformainvoicelineitem',
            name='rate',
            field=models.DecimalField(decimal_places=2, max_digits=15, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='proformainvoicelineitem',
            name='amount',
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=15, null=True, blank=True),
        ),

        # ProformaInvoiceCharge: add new "amount" field
        migrations.AddField(
            model_name='proformainvoicecharge',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=15, null=True, blank=True),
        ),
    ]
