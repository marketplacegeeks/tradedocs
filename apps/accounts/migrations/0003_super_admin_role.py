from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_user_phone_fields")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("SUPER_ADMIN", "Super Admin"),
                    ("COMPANY_ADMIN", "Company Admin"),
                    ("CHECKER", "Checker"),
                    ("MAKER", "Maker"),
                ],
                default="MAKER",
                max_length=20,
            ),
        ),
    ]
