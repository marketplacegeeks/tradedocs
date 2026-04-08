"""
Migration: replace old ContainerItem weight/packaging fields with the new structured model.

Removed:  packages_kind, quantity, net_weight, inner_packing_weight
Added:    no_of_packages, type_of_package (FK), qty_per_package,
          weight_per_unit_packaging, net_material_weight (computed)

Data-migration: any existing rows have type_of_package set to the first
active TypeOfPackage (seeded by master_data 0015), and numeric fields set to 0.
"""
from django.db import migrations, models
import django.db.models.deletion


def assign_default_package_type(apps, schema_editor):
    """Set type_of_package on any existing ContainerItem rows."""
    TypeOfPackage = apps.get_model("master_data", "TypeOfPackage")
    ContainerItem = apps.get_model("packing_list", "ContainerItem")
    first_pkg = TypeOfPackage.objects.order_by("id").first()
    if first_pkg and ContainerItem.objects.filter(type_of_package__isnull=True).exists():
        ContainerItem.objects.filter(type_of_package__isnull=True).update(type_of_package=first_pkg)


class Migration(migrations.Migration):

    dependencies = [
        ("packing_list", "0003_hsn_code_max_length_10"),
        ("master_data", "0015_typeofpackage"),
    ]

    operations = [
        # Remove old fields
        migrations.RemoveField(model_name="containeritem", name="packages_kind"),
        migrations.RemoveField(model_name="containeritem", name="quantity"),
        migrations.RemoveField(model_name="containeritem", name="net_weight"),
        migrations.RemoveField(model_name="containeritem", name="inner_packing_weight"),

        # Add new numeric fields (default=0 handles any existing rows safely)
        migrations.AddField(
            model_name="containeritem",
            name="no_of_packages",
            field=models.DecimalField(max_digits=12, decimal_places=3, default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="containeritem",
            name="qty_per_package",
            field=models.DecimalField(max_digits=12, decimal_places=3, default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="containeritem",
            name="weight_per_unit_packaging",
            field=models.DecimalField(max_digits=12, decimal_places=3, default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="containeritem",
            name="net_material_weight",
            field=models.DecimalField(max_digits=12, decimal_places=3, editable=False, default=0),
        ),

        # Add type_of_package as nullable first so existing rows don't violate the NOT NULL constraint
        migrations.AddField(
            model_name="containeritem",
            name="type_of_package",
            field=models.ForeignKey(
                to="master_data.TypeOfPackage",
                on_delete=django.db.models.deletion.PROTECT,
                null=True,
            ),
        ),

        # Populate type_of_package for any existing rows
        migrations.RunPython(assign_default_package_type, migrations.RunPython.noop),

        # Now make it non-nullable
        migrations.AlterField(
            model_name="containeritem",
            name="type_of_package",
            field=models.ForeignKey(
                to="master_data.TypeOfPackage",
                on_delete=django.db.models.deletion.PROTECT,
            ),
        ),
    ]
