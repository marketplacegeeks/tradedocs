import pytest
from apps.accounts.models import User, UserRole
from .factories import CompanyAdminFactory, MakerFactory, CheckerFactory


@pytest.mark.django_db
class TestUserModel:
    def test_default_role_is_maker(self):
        user = MakerFactory()
        assert user.role == UserRole.MAKER

    def test_is_active_defaults_to_true(self):
        user = MakerFactory()
        assert user.is_active is True

    def test_soft_delete_sets_is_active_false(self):
        user = MakerFactory()
        user.is_active = False
        user.save()
        # confirm the user still exists in the database (never hard-deleted)
        assert User.objects.filter(pk=user.pk).exists()
        assert not User.objects.get(pk=user.pk).is_active

    def test_full_name_property(self):
        user = MakerFactory(first_name="Aniket", last_name="Shah")
        assert user.full_name == "Aniket Shah"

    def test_role_properties(self):
        assert MakerFactory().is_maker is True
        assert CheckerFactory().is_checker is True
        assert CompanyAdminFactory().is_company_admin is True

    def test_email_is_username_field(self):
        assert User.USERNAME_FIELD == "email"

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match="Email is required"):
            User.objects.create_user(email="", password="pass")

    def test_superuser_gets_company_admin_role(self):
        user = User.objects.create_superuser(email="admin@test.com", password="pass123")
        assert user.role == UserRole.COMPANY_ADMIN
        assert user.is_staff is True
        assert user.is_superuser is True
