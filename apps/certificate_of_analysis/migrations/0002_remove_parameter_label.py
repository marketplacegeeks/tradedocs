from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("certificate_of_analysis", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="coaparameter",
            name="parameter_label",
        ),
    ]
