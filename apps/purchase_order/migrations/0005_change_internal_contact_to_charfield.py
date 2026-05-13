from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchase_order', '0004_add_internal_contract_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchaseorder',
            name='internal_contact',
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='internal_contact',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]
