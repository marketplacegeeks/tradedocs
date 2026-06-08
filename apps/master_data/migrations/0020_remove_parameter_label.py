from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0019_seed_coa_test_parameters_and_methods"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="producttesttemplaterow",
            name="parameter_label",
        ),
    ]
