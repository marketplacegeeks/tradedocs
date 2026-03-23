import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from .factories import CompanyAdminFactory, MakerFactory, CheckerFactory, SuperAdminFactory


@pytest.fixture
def api_client():
    return APIClient()


def get_tokens(client, email, password):
    """Helper: log in and return access + refresh tokens."""
    response = client.post(reverse("auth-login"), {"email": email, "password": password})
    return response.data


@pytest.mark.django_db
class TestLoginView:
    def test_valid_credentials_return_tokens(self, api_client):
        user = MakerFactory()
        data = get_tokens(api_client, user.email, "testpass123")
        assert "access" in data
        assert "refresh" in data

    def test_wrong_password_returns_401(self, api_client):
        user = MakerFactory()
        response = api_client.post(reverse("auth-login"), {"email": user.email, "password": "wrongpass"})
        assert response.status_code == 401

    def test_unknown_email_returns_401(self, api_client):
        response = api_client.post(reverse("auth-login"), {"email": "nobody@test.com", "password": "pass"})
        assert response.status_code == 401

    def test_inactive_user_cannot_login(self, api_client):
        user = MakerFactory(is_active=False)
        response = api_client.post(reverse("auth-login"), {"email": user.email, "password": "testpass123"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestMeView:
    def test_authenticated_user_gets_profile(self, api_client):
        user = MakerFactory(first_name="Aniket", last_name="Shah")
        tokens = get_tokens(api_client, user.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.get(reverse("auth-me"))
        assert response.status_code == 200
        assert response.data["email"] == user.email
        assert response.data["role"] == "MAKER"
        assert response.data["full_name"] == "Aniket Shah"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse("auth-me"))
        assert response.status_code == 401


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_blacklists_refresh_token(self, api_client):
        user = MakerFactory()
        tokens = get_tokens(api_client, user.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.post(reverse("auth-logout"), {"refresh": tokens["refresh"]})
        assert response.status_code == 204

    def test_logout_without_refresh_token_returns_400(self, api_client):
        user = MakerFactory()
        tokens = get_tokens(api_client, user.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.post(reverse("auth-logout"), {})
        assert response.status_code == 400

    def test_unauthenticated_logout_returns_401(self, api_client):
        response = api_client.post(reverse("auth-logout"), {"refresh": "faketoken"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenRefreshView:
    def test_valid_refresh_token_returns_new_access(self, api_client):
        user = MakerFactory()
        tokens = get_tokens(api_client, user.email, "testpass123")
        response = api_client.post(reverse("auth-token-refresh"), {"refresh": tokens["refresh"]})
        assert response.status_code == 200
        assert "access" in response.data


@pytest.mark.django_db
class TestUserListCreateView:
    def test_company_admin_can_list_users(self, api_client):
        admin = CompanyAdminFactory()
        MakerFactory()
        tokens = get_tokens(api_client, admin.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.get(reverse("user-list-create"))
        assert response.status_code == 200
        assert len(response.data) >= 2

    def test_maker_cannot_list_users(self, api_client):
        maker = MakerFactory()
        tokens = get_tokens(api_client, maker.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.get(reverse("user-list-create"))
        assert response.status_code == 403

    def test_checker_cannot_list_users(self, api_client):
        checker = CheckerFactory()
        tokens = get_tokens(api_client, checker.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.get(reverse("user-list-create"))
        assert response.status_code == 403

    def test_company_admin_can_create_user(self, api_client):
        admin = CompanyAdminFactory()
        tokens = get_tokens(api_client, admin.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        payload = {
            "email": "newmaker@test.com",
            "first_name": "New",
            "last_name": "Maker",
            "role": "MAKER",
            "password": "securepass123",
        }
        response = api_client.post(reverse("user-list-create"), payload)
        assert response.status_code == 201

    def test_unauthenticated_cannot_list_users(self, api_client):
        response = api_client.get(reverse("user-list-create"))
        assert response.status_code == 401


@pytest.mark.django_db
class TestUserDetailView:
    def test_company_admin_can_deactivate_user(self, api_client):
        admin = CompanyAdminFactory()
        maker = MakerFactory()
        tokens = get_tokens(api_client, admin.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.patch(reverse("user-detail", kwargs={"pk": maker.pk}), {"is_active": False})
        assert response.status_code == 200

    def test_company_admin_can_change_role(self, api_client):
        admin = CompanyAdminFactory()
        maker = MakerFactory()
        tokens = get_tokens(api_client, admin.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.patch(reverse("user-detail", kwargs={"pk": maker.pk}), {"role": "CHECKER"})
        assert response.status_code == 200

    def test_maker_cannot_access_user_detail(self, api_client):
        maker = MakerFactory()
        other = MakerFactory()
        tokens = get_tokens(api_client, maker.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.get(reverse("user-detail", kwargs={"pk": other.pk}))
        assert response.status_code == 403

    def test_company_admin_cannot_deactivate_themselves(self, api_client):
        admin = CompanyAdminFactory()
        tokens = get_tokens(api_client, admin.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.patch(reverse("user-detail", kwargs={"pk": admin.pk}), {"is_active": False})
        assert response.status_code == 400

    def test_company_admin_cannot_change_their_own_role(self, api_client):
        admin = CompanyAdminFactory()
        tokens = get_tokens(api_client, admin.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.patch(reverse("user-detail", kwargs={"pk": admin.pk}), {"role": "MAKER"})
        assert response.status_code == 400

    def test_cannot_deactivate_last_company_admin(self, api_client):
        # Only one admin exists — deactivating should be blocked.
        admin = CompanyAdminFactory()
        maker = MakerFactory()
        tokens = get_tokens(api_client, admin.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.patch(reverse("user-detail", kwargs={"pk": admin.pk}), {"is_active": False})
        assert response.status_code == 400

    def test_admin_can_set_phone_on_user(self, api_client):
        admin = CompanyAdminFactory()
        maker = MakerFactory()
        tokens = get_tokens(api_client, admin.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.patch(
            reverse("user-detail", kwargs={"pk": maker.pk}),
            {"phone_country_code": "+91", "phone_number": "9876543210"},
        )
        assert response.status_code == 200
        assert response.data["phone_country_code"] == "+91"
        assert response.data["phone_number"] == "9876543210"

    def test_phone_requires_both_fields(self, api_client):
        # Providing only country code without a number should return 400.
        admin = CompanyAdminFactory()
        maker = MakerFactory()
        tokens = get_tokens(api_client, admin.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.patch(
            reverse("user-detail", kwargs={"pk": maker.pk}),
            {"phone_country_code": "+91"},
        )
        assert response.status_code == 400

    def test_me_endpoint_includes_phone_fields(self, api_client):
        maker = MakerFactory(phone_country_code="+44", phone_number="7911123456")
        tokens = get_tokens(api_client, maker.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.get(reverse("auth-me"))
        assert response.status_code == 200
        assert response.data["phone_country_code"] == "+44"
        assert response.data["phone_number"] == "7911123456"


@pytest.mark.django_db
class TestUserCreateWithPhone:
    """Tests for phone number fields on the invite (create) endpoint."""

    def _auth(self, api_client):
        admin = CompanyAdminFactory()
        tokens = get_tokens(api_client, admin.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def _base_payload(self):
        return {
            "email": "newuser@test.com",
            "first_name": "New",
            "last_name": "User",
            "role": "MAKER",
            "password": "securepass123",
        }

    def test_create_user_with_phone_succeeds(self, api_client):
        self._auth(api_client)
        payload = {**self._base_payload(), "phone_country_code": "+91", "phone_number": "9876543210"}
        response = api_client.post(reverse("user-list-create"), payload)
        assert response.status_code == 201
        assert response.data["phone_country_code"] == "+91"
        assert response.data["phone_number"] == "9876543210"

    def test_create_user_without_phone_succeeds(self, api_client):
        # Phone is optional — omitting both fields should still create the user.
        self._auth(api_client)
        response = api_client.post(reverse("user-list-create"), self._base_payload())
        assert response.status_code == 201
        assert response.data["phone_country_code"] == ""
        assert response.data["phone_number"] == ""

    def test_create_user_with_only_country_code_fails(self, api_client):
        # Providing a dial code without a number should be rejected.
        self._auth(api_client)
        payload = {**self._base_payload(), "phone_country_code": "+91"}
        response = api_client.post(reverse("user-list-create"), payload)
        assert response.status_code == 400
        assert "phone" in response.data

    def test_create_user_with_only_number_fails(self, api_client):
        # Providing a number without a dial code should be rejected.
        self._auth(api_client)
        payload = {**self._base_payload(), "phone_number": "9876543210"}
        response = api_client.post(reverse("user-list-create"), payload)
        assert response.status_code == 400
        assert "phone" in response.data

    def test_create_user_with_invalid_phone_fails(self, api_client):
        # A syntactically valid dial code but nonsense number should be rejected.
        self._auth(api_client)
        payload = {**self._base_payload(), "phone_country_code": "+91", "phone_number": "000"}
        response = api_client.post(reverse("user-list-create"), payload)
        assert response.status_code == 400
        assert "phone" in response.data


@pytest.mark.django_db
class TestResetPasswordView:
    """Tests for POST /api/v1/users/{id}/reset-password/"""

    def _auth(self, client, user):
        tokens = get_tokens(client, user.email, "testpass123")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def test_company_admin_can_reset_password(self, api_client):
        admin = CompanyAdminFactory()
        maker = MakerFactory()
        self._auth(api_client, admin)
        response = api_client.post(
            reverse("user-reset-password", kwargs={"pk": maker.pk}),
            {"new_password": "newpassword123"},
        )
        assert response.status_code == 200
        assert response.data["detail"] == "Password reset successfully."

    def test_super_admin_can_reset_password(self, api_client):
        super_admin = SuperAdminFactory()
        maker = MakerFactory()
        self._auth(api_client, super_admin)
        response = api_client.post(
            reverse("user-reset-password", kwargs={"pk": maker.pk}),
            {"new_password": "newpassword123"},
        )
        assert response.status_code == 200

    def test_maker_cannot_reset_password(self, api_client):
        maker = MakerFactory()
        other = MakerFactory()
        self._auth(api_client, maker)
        response = api_client.post(
            reverse("user-reset-password", kwargs={"pk": other.pk}),
            {"new_password": "newpassword123"},
        )
        assert response.status_code == 403

    def test_checker_cannot_reset_password(self, api_client):
        checker = CheckerFactory()
        maker = MakerFactory()
        self._auth(api_client, checker)
        response = api_client.post(
            reverse("user-reset-password", kwargs={"pk": maker.pk}),
            {"new_password": "newpassword123"},
        )
        assert response.status_code == 403

    def test_short_password_rejected(self, api_client):
        admin = CompanyAdminFactory()
        maker = MakerFactory()
        self._auth(api_client, admin)
        response = api_client.post(
            reverse("user-reset-password", kwargs={"pk": maker.pk}),
            {"new_password": "short"},
        )
        assert response.status_code == 400
        assert "new_password" in response.data

    def test_empty_password_rejected(self, api_client):
        admin = CompanyAdminFactory()
        maker = MakerFactory()
        self._auth(api_client, admin)
        response = api_client.post(
            reverse("user-reset-password", kwargs={"pk": maker.pk}),
            {"new_password": ""},
        )
        assert response.status_code == 400

    def test_nonexistent_user_returns_404(self, api_client):
        admin = CompanyAdminFactory()
        self._auth(api_client, admin)
        response = api_client.post(
            reverse("user-reset-password", kwargs={"pk": 99999}),
            {"new_password": "validpassword123"},
        )
        assert response.status_code == 404

    def test_password_actually_changes(self, api_client):
        # After reset, the user can log in with the new password.
        admin = CompanyAdminFactory()
        maker = MakerFactory()
        self._auth(api_client, admin)
        api_client.post(
            reverse("user-reset-password", kwargs={"pk": maker.pk}),
            {"new_password": "brandnewpass456"},
        )
        # Clear credentials, then try logging in with the new password.
        api_client.credentials()
        login_response = api_client.post(
            reverse("auth-login"),
            {"email": maker.email, "password": "brandnewpass456"},
        )
        assert login_response.status_code == 200
        assert "access" in login_response.data

    def test_unauthenticated_cannot_reset_password(self, api_client):
        maker = MakerFactory()
        response = api_client.post(
            reverse("user-reset-password", kwargs={"pk": maker.pk}),
            {"new_password": "validpassword123"},
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestSuperAdminPermissions:
    """
    Every endpoint guarded by IsCompanyAdmin or IsCheckerOrAdmin must also
    grant access to SUPER_ADMIN. These tests guard against regressions where
    a new role is added to the permission classes but missed elsewhere
    (e.g. route guards, serialiser checks).
    """

    def _auth(self, client, user):
        tokens = get_tokens(client, user.email, "testpass123")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def test_super_admin_can_list_users(self, api_client):
        super_admin = SuperAdminFactory()
        MakerFactory()
        self._auth(api_client, super_admin)
        response = api_client.get(reverse("user-list-create"))
        assert response.status_code == 200

    def test_super_admin_can_create_user(self, api_client):
        super_admin = SuperAdminFactory()
        self._auth(api_client, super_admin)
        payload = {
            "email": "newmakerbysa@test.com",
            "first_name": "New",
            "last_name": "Maker",
            "role": "MAKER",
            "password": "securepass123",
        }
        response = api_client.post(reverse("user-list-create"), payload)
        assert response.status_code == 201

    def test_super_admin_can_deactivate_user(self, api_client):
        super_admin = SuperAdminFactory()
        maker = MakerFactory()
        self._auth(api_client, super_admin)
        response = api_client.patch(reverse("user-detail", kwargs={"pk": maker.pk}), {"is_active": False})
        assert response.status_code == 200

    def test_super_admin_can_change_user_role(self, api_client):
        super_admin = SuperAdminFactory()
        maker = MakerFactory()
        self._auth(api_client, super_admin)
        response = api_client.patch(reverse("user-detail", kwargs={"pk": maker.pk}), {"role": "CHECKER"})
        assert response.status_code == 200
