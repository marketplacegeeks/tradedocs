from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0013_currency_is_active"),
    ]

    operations = [
        # Update choices to include DELIVERY (records the change in migration history).
        migrations.AlterField(
            model_name="organisationaddress",
            name="address_type",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("REGISTERED", "Registered"),
                    ("FACTORY", "Factory"),
                    ("OFFICE", "Office"),
                    ("DELIVERY", "Delivery"),
                ],
            ),
        ),
        # Drop the old blanket unique constraint (blocked all duplicate address types).
        migrations.RemoveConstraint(
            model_name="organisationaddress",
            name="unique_address_type_per_organisation",
        ),
        # Add a conditional constraint — only enforces uniqueness for non-DELIVERY types.
        migrations.AddConstraint(
            model_name="organisationaddress",
            constraint=models.UniqueConstraint(
                fields=["organisation", "address_type"],
                condition=~models.Q(address_type="DELIVERY"),
                name="unique_non_delivery_address_type_per_organisation",
            ),
        ),
    ]
