from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_super_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    email = "mehareac@gmail.com"
    if not User.objects.filter(email=email).exists():
        User.objects.create(
            email=email,
            first_name="Super",
            last_name="Admin",
            role="SUPER_ADMIN",
            is_active=True,
            is_staff=True,
            is_superuser=True,
            # Unusable password — set a real password via Django admin or password reset.
            password=make_password(None),
        )
    else:
        # User already exists — promote to SUPER_ADMIN
        User.objects.filter(email=email).update(role="SUPER_ADMIN", is_staff=True, is_superuser=True)


def reverse_super_admin(apps, schema_editor):
    # Demote back to COMPANY_ADMIN (safest reversible state)
    User = apps.get_model("accounts", "User")
    User.objects.filter(email="mehareac@gmail.com").update(role="COMPANY_ADMIN")


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_super_admin_role")]

    operations = [
        migrations.RunPython(create_super_admin, reverse_super_admin),
    ]
