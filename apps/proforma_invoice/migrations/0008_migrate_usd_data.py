# Data migration: copy rate_usd → rate, amount_usd → amount

from django.db import migrations


def forward(apps, schema_editor):
    ProformaInvoice = apps.get_model('proforma_invoice', 'ProformaInvoice')
    ProformaInvoiceLineItem = apps.get_model('proforma_invoice', 'ProformaInvoiceLineItem')
    ProformaInvoiceCharge = apps.get_model('proforma_invoice', 'ProformaInvoiceCharge')
    Currency = apps.get_model('master_data', 'Currency')

    # Get or create USD currency
    usd, created = Currency.objects.get_or_create(
        code='USD',
        defaults={
            'name': 'US Dollar',
            'is_active': True
        }
    )

    # Set all existing PIs to USD
    pi_count = ProformaInvoice.objects.filter(currency__isnull=True).update(currency=usd)
    print(f"Set currency to USD for {pi_count} Proforma Invoices")

    # Copy rate_usd → rate, amount_usd → amount for PI line items
    for item in ProformaInvoiceLineItem.objects.all():
        item.rate = item.rate_usd
        item.amount = item.amount_usd
        item.save(update_fields=['rate', 'amount'])

    # Copy amount_usd → amount for PI charges
    for charge in ProformaInvoiceCharge.objects.all():
        charge.amount = charge.amount_usd
        charge.save(update_fields=['amount'])

    print("Data migration complete: copied all USD values to new fields")


def backward(apps, schema_editor):
    # Reverse: copy data back to old fields
    ProformaInvoiceLineItem = apps.get_model('proforma_invoice', 'ProformaInvoiceLineItem')
    ProformaInvoiceCharge = apps.get_model('proforma_invoice', 'ProformaInvoiceCharge')

    for item in ProformaInvoiceLineItem.objects.all():
        item.rate_usd = item.rate
        item.amount_usd = item.amount
        item.save(update_fields=['rate_usd', 'amount_usd'])

    for charge in ProformaInvoiceCharge.objects.all():
        charge.amount_usd = charge.amount
        charge.save(update_fields=['amount_usd'])


class Migration(migrations.Migration):

    dependencies = [
        ('proforma_invoice', '0007_add_currency_and_rename_fields'),
        ('master_data', '0013_currency_is_active'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
