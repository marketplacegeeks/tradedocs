import factory
from apps.accounts.models import User, UserRole


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = UserRole.MAKER
    is_active = True
    phone_country_code = ""
    phone_number = ""

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        # Set the password hash and persist it to the database.
        raw = extracted or "testpass123"
        self.set_password(raw)
        if create:
            self.save()


class MakerFactory(UserFactory):
    role = UserRole.MAKER


class CheckerFactory(UserFactory):
    role = UserRole.CHECKER


class CompanyAdminFactory(UserFactory):
    role = UserRole.COMPANY_ADMIN
    is_staff = True


class SuperAdminFactory(UserFactory):
    role = UserRole.SUPER_ADMIN
    is_staff = True
    is_superuser = True
