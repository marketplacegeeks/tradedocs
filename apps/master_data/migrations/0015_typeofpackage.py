"""
Migration: add master_data_typeofpackage table and seed common packaging types.
"""
from django.db import migrations, models


SEED_PACKAGES = [
    "Bags", "Bales", "Bottles", "Boxes", "Bundles",
    "Cartons", "Cases", "Crates", "Cylinders", "Drums",
    "Jerricans", "Pallets", "Rolls", "Tins",
]


def seed_package_types(apps, schema_editor):
    TypeOfPackage = apps.get_model("master_data", "TypeOfPackage")
    for name in SEED_PACKAGES:
        TypeOfPackage.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0014_add_delivery_address_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="TypeOfPackage",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Type of Package",
                "verbose_name_plural": "Types of Package",
                "db_table": "master_data_typeofpackage",
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(seed_package_types, migrations.RunPython.noop),
    ]
