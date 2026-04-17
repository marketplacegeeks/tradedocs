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

    # Copy rate_usd → rate, amount_usd → amount for PI line items (bulk update for performance)
    items = list(ProformaInvoiceLineItem.objects.exclude(rate_usd__isnull=True))
    for item in items:
        item.rate = item.rate_usd
        item.amount = item.amount_usd
    if items:
        ProformaInvoiceLineItem.objects.bulk_update(items, ['rate', 'amount'], batch_size=500)
        print(f"Migrated {len(items)} line items")

    # Copy amount_usd → amount for PI charges (bulk update for performance)
    charges = list(ProformaInvoiceCharge.objects.exclude(amount_usd__isnull=True))
    for charge in charges:
        charge.amount = charge.amount_usd
    if charges:
        ProformaInvoiceCharge.objects.bulk_update(charges, ['amount'], batch_size=500)
        print(f"Migrated {len(charges)} charges")

    print("Data migration complete: copied all USD values to new fields")


def backward(apps, schema_editor):
    # Reverse: copy data back to old fields (bulk update for performance)
    ProformaInvoiceLineItem = apps.get_model('proforma_invoice', 'ProformaInvoiceLineItem')
    ProformaInvoiceCharge = apps.get_model('proforma_invoice', 'ProformaInvoiceCharge')

    items = list(ProformaInvoiceLineItem.objects.exclude(rate__isnull=True))
    for item in items:
        item.rate_usd = item.rate
        item.amount_usd = item.amount
    if items:
        ProformaInvoiceLineItem.objects.bulk_update(items, ['rate_usd', 'amount_usd'], batch_size=500)

    charges = list(ProformaInvoiceCharge.objects.exclude(amount__isnull=True))
    for charge in charges:
        charge.amount_usd = charge.amount
    if charges:
        ProformaInvoiceCharge.objects.bulk_update(charges, ['amount_usd'], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ('proforma_invoice', '0007_add_currency_and_rename_fields'),
        ('master_data', '0013_currency_is_active'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
