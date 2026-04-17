# Remove old rate_usd/amount_usd fields and make currency NOT NULL

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proforma_invoice', '0008_migrate_usd_data'),
    ]

    operations = [
        # Make currency NOT NULL now that all records have been set
        migrations.AlterField(
            model_name='proformainvoice',
            name='currency',
            field=models.ForeignKey(
                help_text='Currency for all monetary values on this Proforma Invoice',
                on_delete=django.db.models.deletion.PROTECT,
                to='master_data.currency'
            ),
        ),

        # Make new fields NOT NULL
        migrations.AlterField(
            model_name='proformainvoicelineitem',
            name='rate',
            field=models.DecimalField(decimal_places=2, max_digits=15),
        ),
        migrations.AlterField(
            model_name='proformainvoicelineitem',
            name='amount',
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=15),
        ),
        migrations.AlterField(
            model_name='proformainvoicecharge',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=15),
        ),

        # Drop old USD fields
        migrations.RemoveField(
            model_name='proformainvoicelineitem',
            name='rate_usd',
        ),
        migrations.RemoveField(
            model_name='proformainvoicelineitem',
            name='amount_usd',
        ),
        migrations.RemoveField(
            model_name='proformainvoicecharge',
            name='amount_usd',
        ),
    ]
