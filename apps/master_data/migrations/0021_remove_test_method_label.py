from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("master_data", "0020_remove_parameter_label"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="producttesttemplaterow",
            name="test_method_label",
        ),
    ]
