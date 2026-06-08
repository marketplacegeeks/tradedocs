from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("certificate_of_analysis", "0002_remove_parameter_label"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="coaparameter",
            name="test_method_label",
        ),
    ]
