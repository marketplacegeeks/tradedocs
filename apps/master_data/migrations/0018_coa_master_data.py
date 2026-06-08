"""
Migration: add COA master data tables.
Adds: Product, ProductGrade, TestParameter, TestMethod,
      ProductTestTemplate, ProductTestTemplateRow.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0017_add_shipment_fields"),
    ]

    operations = [
        # 1. Product — one row per chemical
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("cas_number", models.CharField(blank=True, max_length=20)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "master_data_product",
                "ordering": ["name"],
            },
        ),
        # 2. ProductGrade — one row per (product, grade) pair
        migrations.CreateModel(
            name="ProductGrade",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grades",
                        to="master_data.product",
                    ),
                ),
                ("grade", models.CharField(max_length=100)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "master_data_product_grade",
                "ordering": ["product__name", "grade"],
            },
        ),
        migrations.AddConstraint(
            model_name="productgrade",
            constraint=models.UniqueConstraint(
                fields=["product", "grade"],
                name="unique_product_grade",
            ),
        ),
        # 3. TestParameter — library of test characteristics
        migrations.CreateModel(
            name="TestParameter",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                (
                    "default_unit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="test_parameters",
                        to="master_data.uom",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "master_data_test_parameter",
                "ordering": ["name"],
            },
        ),
        # 4. TestMethod — library of test method codes
        migrations.CreateModel(
            name="TestMethod",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=50, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "master_data_test_method",
                "ordering": ["code"],
            },
        ),
        # 5. ProductTestTemplate — one per product grade (1:1)
        migrations.CreateModel(
            name="ProductTestTemplate",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "product_grade",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="test_template",
                        to="master_data.productgrade",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "master_data_product_test_template",
            },
        ),
        # 6. ProductTestTemplateRow — individual parameter rows of a template
        migrations.CreateModel(
            name="ProductTestTemplateRow",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rows",
                        to="master_data.producttesttemplate",
                    ),
                ),
                ("s_no", models.PositiveIntegerField()),
                (
                    "parameter",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="template_rows",
                        to="master_data.testparameter",
                    ),
                ),
                ("parameter_label", models.CharField(max_length=255)),
                (
                    "unit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="template_rows",
                        to="master_data.uom",
                    ),
                ),
                (
                    "spec_type",
                    models.CharField(
                        choices=[("QUANTITATIVE", "Quantitative"), ("QUALITATIVE", "Qualitative")],
                        max_length=20,
                    ),
                ),
                ("spec_min", models.DecimalField(blank=True, decimal_places=6, max_digits=15, null=True)),
                ("spec_max", models.DecimalField(blank=True, decimal_places=6, max_digits=15, null=True)),
                ("spec_description", models.TextField(blank=True)),
                (
                    "test_method",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="template_rows",
                        to="master_data.testmethod",
                    ),
                ),
                ("test_method_label", models.CharField(blank=True, max_length=100)),
            ],
            options={
                "db_table": "master_data_product_test_template_row",
                "ordering": ["s_no"],
            },
        ),
    ]
