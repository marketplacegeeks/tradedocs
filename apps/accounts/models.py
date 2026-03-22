from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserRole(models.TextChoices):
    COMPANY_ADMIN = "COMPANY_ADMIN", "Company Admin"
    CHECKER = "CHECKER", "Checker"
    MAKER = "MAKER", "Maker"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.COMPANY_ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model. Email is the login identifier.
    Users are never hard-deleted — set is_active=False instead (constraint #8).
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.MAKER)

    # Phone stored as two fields: dial code (e.g. +91) and local number.
    # Both are optional overall, but if one is provided the other must be too (enforced in serializer).
    phone_country_code = models.CharField(
        max_length=10, blank=True,
        help_text="E.164 dial code, e.g. +91"
    )
    phone_number = models.CharField(max_length=20, blank=True)

    # is_active=False is the soft-delete mechanism — never delete user rows
    is_active = models.BooleanField(default=True)
    # is_staff allows access to the Django admin panel
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "accounts_user"

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_company_admin(self):
        return self.role == UserRole.COMPANY_ADMIN

    @property
    def is_checker(self):
        return self.role == UserRole.CHECKER

    @property
    def is_maker(self):
        return self.role == UserRole.MAKER
