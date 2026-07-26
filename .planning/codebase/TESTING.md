# Testing Patterns

**Analysis Date:** 2026-07-26

## Test Framework

**Backend (Python):**
- Runner: `pytest`
- Config: `pytest.ini` at project root
- Django integration: `pytest-django`

**Configuration:**
```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = tradetocs.settings
python_files = tests/*.py          # Only files in tests/ dir
python_classes = Test*             # Classes starting with Test
python_functions = test_*          # Functions starting with test_
addopts = -v --tb=short           # Verbose output, short tracebacks
```

**Frontend (TypeScript):**
- E2E runner: Playwright
- Config: `frontend/playwright.config.ts`
- Unit tests: Not currently implemented (Playwright only)

**Playwright Configuration:**
```typescript
// frontend/playwright.config.ts
{
  testDir: './tests/e2e',
  timeout: 30_000,
  use: { baseURL: 'http://localhost:5173', trace: 'retain-on-failure' },
  reporter: 'html',
}
```

**Run Commands:**

```bash
# Backend: Run all tests
pytest

# Backend: Run tests for a specific app
pytest apps/accounts/tests/

# Backend: Run a specific test file
pytest apps/accounts/tests/test_views.py

# Backend: Run a specific test class
pytest apps/accounts/tests/test_views.py::TestLoginView

# Backend: Run a specific test function
pytest apps/accounts/tests/test_views.py::TestLoginView::test_valid_credentials_return_tokens

# Backend: Watch mode (with pytest-watch)
ptw

# Backend: Coverage report
pytest --cov=apps/{app} --cov-report=term-missing

# Frontend: Run E2E tests
npm --prefix frontend run e2e

# Frontend: Run E2E tests with UI
npm --prefix frontend run e2e -- --ui

# Frontend: Run E2E tests for a specific file
npm --prefix frontend run e2e -- tests/e2e/create-organisations.spec.ts
```

## Test File Organization

**Backend Location:**
- Pattern: `apps/{app}/tests/` — co-located with the app being tested
- Structure:
  ```
  apps/accounts/tests/
  ├── __init__.py           # Empty, makes tests/ a package
  ├── factories.py          # factory-boy factories for all models in the app
  ├── test_models.py        # Model-level tests (save behavior, properties, constraints)
  ├── test_views.py         # API endpoint tests (permissions, happy paths, error cases)
  └── test_bulk_workflow.py # (Optional) Tests for workflows affecting multiple documents
  ```

**Backend Naming:**
- Test files: `test_*.py`
- Test classes: `Test*` (e.g., `TestLoginView`, `TestProformaInvoiceModel`)
- Test functions: `test_*` (e.g., `test_valid_credentials_return_tokens`)

**Frontend Location:**
- Path: `frontend/tests/e2e/`
- Naming: `*.spec.ts` (e.g., `create-organisations.spec.ts`)

## Test Structure

**Backend: Basic Pytest Class Structure**

```python
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.tests.factories import MakerFactory

@pytest.mark.django_db
class TestLoginView:
    def test_valid_credentials_return_tokens(self, api_client):
        """Happy path: correct email + password return JWT tokens."""
        user = MakerFactory()
        data = get_tokens(api_client, user.email, "testpass123")
        assert "access" in data
        assert "refresh" in data

    def test_wrong_password_returns_401(self, api_client):
        """Error case: wrong password returns 401 Unauthorized."""
        user = MakerFactory()
        response = api_client.post(reverse("auth-login"), {"email": user.email, "password": "wrongpass"})
        assert response.status_code == 401

    def test_unauthenticated_denied(self, api_client):
        """Permission case: unauthenticated request denied."""
        response = APIClient().get("/api/v1/users/")
        assert response.status_code == 401
```

**Pytest Fixtures:**
- `@pytest.mark.django_db` — Marks test as database-accessing
- `api_client` (pytest fixture) — APIClient instance used by DRF tests
- `monkeypatch` (pytest fixture) — Mock/patch objects (rarely used, factories preferred)
- Custom fixtures defined at file/conftest level as `@pytest.fixture`

**Backend: Test Patterns**

**Setup (each test is independent):**
```python
# Use factories to create test data; factories handle all defaults
user = MakerFactory()  # Creates a user with role=MAKER, password="testpass123"
pi = ProformaInvoiceFactory(created_by=user)  # Creates a PI assigned to that user
```

**Teardown:**
- Automatic: `@pytest.mark.django_db` rolls back after each test
- No explicit teardown needed

**Authentication:**
```python
def auth_client(user):
    """Helper: return authenticated APIClient."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client

# In test:
maker = MakerFactory()
response = auth_client(maker).get("/api/v1/proforma-invoices/")
```

**Assertions:**
- Use pytest assertions: `assert value == expected`
- Status codes: `assert response.status_code == 200`
- Data content: `assert response.data["email"] == user.email`
- Exceptions: `with pytest.raises(ValidationError):`

## Mocking

**Framework:** `unittest.mock` (built into Python) — no external mocking library required

**Patterns (Rarely Used):**
- Prefer factories + real DB over mocking (tests are faster with in-memory SQLite)
- Mock only external APIs (Stripe, S3) and slow/flaky operations

**Example: Mock datetime**
```python
from unittest.mock import patch
from datetime import date

@pytest.mark.django_db
def test_first_number_for_year(monkeypatch):
    """First PI of the year should be PI-YYYY-0001."""
    # Factories handle defaults; monkeypatch rarely needed
    assert ProformaInvoice.objects.filter(pi_number__startswith="PI-2026-").count() == 0
    number = generate_document_number()
    assert number.startswith("PI-")
```

**What to Mock:**
- External APIs (Stripe, payment providers) — use factory_boy fixtures instead of real calls
- File system operations (S3, PDF generation) — mock only if slow/unreliable

**What NOT to Mock:**
- Database queries — test with real in-memory SQLite DB
- Django models — test with real model instances
- Your own business logic (services, views) — test the real implementation
- Helper functions — test real implementations, they're fast

## Fixtures and Factories

**Factory Pattern (factory_boy):**
- Location: `apps/{app}/tests/factories.py`
- Base class: `factory.django.DjangoModelFactory`
- Each model gets a factory class

**Example Factories:**

```python
# apps/accounts/tests/factories.py
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")  # Generates realistic data
    last_name = factory.Faker("last_name")
    role = UserRole.MAKER
    is_active = True
    phone_country_code = ""
    phone_number = ""

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        # Custom password handling: allow override with password="mypass"
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
```

**Factory Features Used:**
- `factory.Sequence(lambda n: ...)` — Generate unique values
- `factory.Faker(...)` — Generate realistic data (names, emails, etc.)
- `factory.SubFactory(...)` — Create related instances (FK relationships)
- `factory.post_generation` — Custom logic after model creation (password hashing)

**Example with SubFactory:**

```python
# apps/proforma_invoice/tests/factories.py
class ProformaInvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProformaInvoice

    pi_number = factory.Sequence(lambda n: f"PI-2026-{n + 1:04d}")
    pi_date = factory.LazyFunction(date.today)
    exporter = factory.SubFactory(OrganisationFactory)  # Creates a related Organisation
    consignee = factory.SubFactory(OrganisationFactory)
    currency = factory.SubFactory(CurrencyFactory)
    payment_terms = factory.SubFactory(PaymentTermFactory)
    status = DRAFT
    created_by = factory.SubFactory(MakerFactory)

class ProformaInvoiceLineItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProformaInvoiceLineItem

    pi = factory.SubFactory(ProformaInvoiceFactory)
    description = factory.Sequence(lambda n: f"Item description {n}")
    quantity = factory.Faker("pydecimal", left_digits=4, right_digits=3, positive=True)
    uom = factory.SubFactory(UOMFactory)
    rate = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
```

**Test Data Location:**
- Factories live in `apps/{app}/tests/factories.py`
- Fixtures (seed data) not currently used; factories provide all test data
- E2E fixtures: `frontend/tests/e2e/fixtures/organisations.xlsx` — spreadsheet of test organisations

## Coverage

**Requirements:** No enforced minimum (0% → 100% accepted)

**View Coverage:**

```bash
# Generate coverage report for accounts app
pytest --cov=apps/accounts --cov-report=term-missing

# Shows:
# - Percentage of lines covered
# - Lines NOT covered (helpful for identifying untested code paths)
```

**Current Coverage Expectations:**
- Models: >80% (business logic matters)
- Views: >70% (at minimum: 1 happy path + 1 permission denial per endpoint)
- Services: >80% (critical domain logic)
- Serializers: >60% (validation logic important)
- Permissions: >70% (security-sensitive)

## Test Types

**Backend: Unit Tests**
- Scope: Individual model methods, factories, utility functions
- Approach: Fast, isolated, no external calls
- File: `apps/{app}/tests/test_models.py`
- Example: `test_pi_date_defaults_to_today()`, `test_amount_is_computed_on_save()`

**Backend: Integration Tests (API endpoint tests)**
- Scope: Full request/response cycle (view → serializer → DB)
- Approach: Slower, hit DB, test permissions + business logic
- File: `apps/{app}/tests/test_views.py`
- Minimum per endpoint: 1 happy path + 1 permission denial
- Example: `test_maker_can_create()`, `test_checker_cannot_create()`

**Backend: Workflow Tests**
- Scope: Multi-step workflows affecting multiple document types
- Approach: Test status transitions across PI → PL → CI
- File: `apps/{app}/tests/test_bulk_workflow.py`
- Example: `test_pi_to_pl_to_ci_workflow()`

**Frontend: E2E Tests (Playwright)**
- Scope: End-to-end user workflows (login → create organisations → view list)
- Approach: Slow, browser automation, full app stack required
- File: `frontend/tests/e2e/*.spec.ts`
- Currently: `create-organisations.spec.ts` — data-driven org creation from Excel

**No Frontend Unit Tests:**
- React components not unit tested
- API layer tested implicitly via E2E tests
- Utilities (like `extractApiError()`) tested manually or via E2E error paths

## Common Patterns

**Async Testing (Backend):**
- All Django tests are inherently async-safe via `@pytest.mark.django_db`
- Async views not currently used (no async endpoints)

**Error Testing:**

```python
# Test that a ValidationError is raised with specific message
def test_phone_requires_both_fields(self, api_client):
    admin = CompanyAdminFactory()
    maker = MakerFactory()
    tokens = get_tokens(api_client, admin.email, "testpass123")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    # Providing only country code without a number should return 400
    response = api_client.patch(
        reverse("user-detail", kwargs={"pk": maker.pk}),
        {"phone_country_code": "+91"}  # Missing phone_number
    )
    assert response.status_code == 400

# Test that model raises on invalid data
def test_pi_number_is_unique(self):
    pi1 = ProformaInvoiceFactory()
    with pytest.raises(Exception):
        # Creating a second PI with the same pi_number should fail at DB level
        ProformaInvoiceFactory(pi_number=pi1.pi_number)
```

**Status Code Assertions:**

```python
# Happy path
assert response.status_code == 200  # GET/PATCH success
assert response.status_code == 201  # POST success
assert response.status_code == 204  # DELETE success

# Permission errors
assert response.status_code == 401  # Unauthenticated
assert response.status_code == 403  # Forbidden (authenticated but no permission)

# Validation errors
assert response.status_code == 400  # Bad request (validation failed)

# Not found
assert response.status_code == 404  # Resource doesn't exist
```

**Permission Testing Pattern:**

```python
@pytest.mark.django_db
class TestProformaInvoiceCreate:

    def _payload(self):
        """Shared payload for all tests in this class."""
        exporter = OrganisationFactory()
        consignee = OrganisationFactory()
        currency = CurrencyFactory()
        return {
            "exporter": exporter.pk,
            "consignee": consignee.pk,
            "currency": currency.pk,
        }

    def test_maker_can_create(self):
        """Happy path: Maker successfully creates a PI."""
        maker = MakerFactory()
        resp = auth_client(maker).post(PI_LIST_URL, self._payload(), format="json")
        assert resp.status_code == 201
        assert resp.data["status"] == DRAFT
        assert resp.data["created_by"] == maker.pk

    def test_checker_cannot_create(self):
        """Permission denial: Checker cannot create a PI."""
        resp = auth_client(CheckerFactory()).post(PI_LIST_URL, self._payload(), format="json")
        assert resp.status_code == 403

    def test_unauthenticated_denied(self):
        """Permission denial: Unauthenticated user denied."""
        resp = APIClient().post(PI_LIST_URL, self._payload(), format="json")
        assert resp.status_code == 401
```

**Playwright E2E Pattern (Frontend):**

```typescript
import { test, expect, Page } from '@playwright/test';

async function login(page: Page) {
  await page.goto('/login');
  await page.getByRole('textbox', { name: 'you@example.com' }).fill(EMAIL);
  await page.getByRole('textbox', { name: '••••••••' }).fill(PASSWORD);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('button', { name: 'Master Data' })).toBeVisible();
}

test.describe('Create organisations from Excel fixture', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  for (const org of organisations) {
    test(`create organisation: ${org.name}`, async ({ page }) => {
      await page.goto('/master-data/organisations/new');
      await page.getByRole('textbox', { name: 'e.g. Sunrise Exports Pvt Ltd' }).fill(org.name);
      await page.getByRole('button', { name: 'Create Organisation' }).click();
      await page.waitForURL('**/master-data/organisations', { timeout: 15_000 });
    });
  }
});
```

## Test Checklist

**For Every API Endpoint (minimum coverage):**
- [ ] One happy-path test (correct input → 200/201 response)
- [ ] One permission-denial test (wrong role → 403, unauthenticated → 401)
- [ ] One validation-failure test (bad input → 400) if applicable
- [ ] One edge-case test (boundary conditions, empty data) if applicable

**For Every Model:**
- [ ] Test default values (e.g., `status` defaults to `DRAFT`)
- [ ] Test constraints (uniqueness, FK relationships, cascading deletes)
- [ ] Test computed fields (e.g., `amount` auto-calculated from `quantity × rate`)
- [ ] Test string representation (`__str__` method)

**For Every Service Function:**
- [ ] Happy path test
- [ ] Error case test (validation, permission, state conflict)
- [ ] Side-effect test (e.g., AuditLog written for status transitions)

---

*Testing analysis: 2026-07-26*
