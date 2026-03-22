from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="phone_country_code",
            field=models.CharField(
                blank=True,
                help_text="E.164 dial code, e.g. +91",
                max_length=10,
                default="",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="phone_number",
            field=models.CharField(blank=True, max_length=20, default=""),
            preserve_default=False,
        ),
    ]
