# Testing Patterns

**Analysis Date:** 2026-06-20

## Test Framework

**Runner:**
- pytest 9.0.2+
- Config: `/Users/aniket/Documents/Development/TradeDocs/pytest.ini`

**Assertion Library:**
- pytest assertions (built-in `assert` statements)

**Run Commands:**
```bash
pytest                                           # Run all tests
pytest -v                                        # Verbose output
pytest --tb=short                                # Short traceback format
pytest apps/proforma_invoice/tests/              # Run app-specific tests
pytest --cov=apps/proforma_invoice --cov-report=term-missing  # Coverage report
```

**Configuration (pytest.ini):**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = tradetocs.settings
python_files = tests/*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## Test File Organization

**Location:** Co-located in `tests/` directory within each app

**Naming:**
- `tests/__init__.py` — Empty init file
- `tests/factories.py` — factory-boy factories for all models
- `tests/test_models.py` — Model-level tests
- `tests/test_views.py` — API view and serializer tests

**Structure:**
```
apps/{app}/tests/
├── __init__.py
├── factories.py
├── test_models.py
└── test_views.py
```

Examples:
- `apps/proforma_invoice/tests/`
- `apps/packing_list/tests/`
- `apps/accounts/tests/`

## Test Structure

**Suite Organization:**

From `apps/accounts/tests/test_views.py`:
```python
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
```

**Patterns:**

- Test classes: One class per view/model, named `Test{ModelName}` or `Test{ViewName}`
- Test methods: Named `test_{scenario}`, describing what is being tested
- Django DB access: Mark test classes with `@pytest.mark.django_db`
- Setup: Use factories to create test data (never hardcode IDs)
- Assertion: Simple pytest assertions, not unittest-style `self.assertEqual()`

## Mocking

**Framework:** pytest fixtures and factory-boy, no external mocking library configured

**Patterns:**

From `apps/accounts/tests/test_views.py`:
```python
@pytest.fixture
def api_client():
    return APIClient()

def get_tokens(client, email, password):
    """Helper: log in and return access + refresh tokens."""
    response = client.post(reverse("auth-login"), {"email": email, "password": password})
    return response.data
```

**What to Mock:**
- Database state: Use factories to set up records
- Authenticated users: Create user via factory and authenticate APIClient
- External API calls: Not mocked (no external integrations currently)

**What NOT to Mock:**
- Django models — test against real database (marked with `@pytest.mark.django_db`)
- Views — test full request-response cycle via APIClient
- Serializers — test with real model instances

## Fixtures and Factories

**Test Data:**

From `apps/proforma_invoice/tests/factories.py`:
```python
class ProformaInvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProformaInvoice

    pi_number = factory.Sequence(lambda n: f"PI-2026-{n + 1:04d}")
    pi_date = factory.LazyFunction(date.today)
    exporter = factory.SubFactory(OrganisationFactory)
    consignee = factory.SubFactory(OrganisationFactory)
    currency = factory.SubFactory(CurrencyFactory)
    status = DRAFT
    created_by = factory.SubFactory(MakerFactory)
```

**Key patterns:**
- Use `factory.Sequence()` for auto-incrementing values
- Use `factory.SubFactory()` for related models — never hardcode IDs
- Use `factory.LazyFunction()` for computed fields (e.g., today's date)
- Use `factory.Faker()` for realistic random data (weights, amounts)

**Location:**
- All factories live in `tests/factories.py` within each app
- Factories are reusable across test files in the same app
- Cross-app dependencies: factories import from other apps' factories
  - Example: `from apps.accounts.tests.factories import MakerFactory`

## Coverage

**Requirements:** No specific coverage target enforced — project is bootstrapped

**View Coverage:**

From `apps/proforma_invoice/tests/test_views.py`, every endpoint has:
1. **One happy-path test** — successful request with expected result
2. **One permission-denial test** — unauthenticated or unauthorized request

Example from `TestProformaInvoiceCreate`:
```python
def test_maker_can_create(self):
    maker = MakerFactory()
    resp = auth_client(maker).post(PI_LIST_URL, self._payload(), format="json")
    assert resp.status_code == 201
    assert resp.data["status"] == DRAFT

def test_checker_cannot_create(self):
    resp = auth_client(CheckerFactory()).post(PI_LIST_URL, self._payload(), format="json")
    assert resp.status_code == 403
```

## Test Types

**Unit Tests:**
- Scope: Model methods, field validation, computed properties
- Approach: Test model instance in isolation, use factories for related objects
- Location: `tests/test_models.py`
- Example from `apps/proforma_invoice/tests/test_models.py`:
  ```python
  def test_amount_is_computed_on_save(self):
      item = ProformaInvoiceLineItemFactory(
          quantity=Decimal("10.000"),
          rate=Decimal("50.00"),
      )
      assert item.amount == Decimal("500.00")
  ```

**Integration Tests:**
- Scope: API endpoints, permission checks, database transactions
- Approach: Full request-response cycle via DRF's APIClient, test data via factories
- Location: `tests/test_views.py`
- Example from `apps/accounts/tests/test_views.py`:
  ```python
  def test_valid_credentials_return_tokens(self, api_client):
      user = MakerFactory()
      data = get_tokens(api_client, user.email, "testpass123")
      assert "access" in data
      assert "refresh" in data
  ```

**E2E Tests:**
- Framework: Not used — project is backend + frontend separately
- Frontend testing: No test framework configured (Vite + React, no Jest)
- Backend testing: Integration tests via pytest + APIClient cover most scenarios

## Common Patterns

**Async Testing:**

Not applicable — Django views are synchronous, pytest doesn't require special async handling.

**Error Testing:**

From `apps/proforma_invoice/tests/test_models.py`:
```python
def test_pi_number_is_unique(self):
    pi1 = ProformaInvoiceFactory()
    with pytest.raises(Exception):
        # Creating a second PI with the same pi_number should fail at DB level
        ProformaInvoiceFactory(pi_number=pi1.pi_number)
```

From `apps/proforma_invoice/tests/test_views.py`:
```python
def test_maker_can_list(self):
    maker = MakerFactory()
    ProformaInvoiceFactory.create_batch(3, created_by=maker)
    resp = auth_client(maker).get(PI_LIST_URL)
    assert resp.status_code == 200
    assert len(resp.data) >= 3

def test_unauthenticated_denied(self):
    resp = APIClient().get(PI_LIST_URL)
    assert resp.status_code == 401
```

## Test Data Patterns

**Bulk Creation:**

From `apps/proforma_invoice/tests/test_views.py`:
```python
ProformaInvoiceFactory.create_batch(3, created_by=maker)
```

**Status-based Tests:**

From `apps/proforma_invoice/tests/test_views.py`:
```python
ProformaInvoiceFactory(created_by=maker, status=DRAFT)
ProformaInvoiceFactory(created_by=maker, status=PENDING_APPROVAL)
resp = auth_client(maker).get(PI_LIST_URL, {"status": DRAFT})
assert all(pi["status"] == DRAFT for pi in resp.data)
```

**Authenticated Client Helper:**

From `apps/proforma_invoice/tests/test_views.py`:
```python
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client
```

Used throughout tests to quickly create authenticated requests.

## Pre-commit Testing

**Requirement:** All tests must pass before any git commit.

Run before committing:
```bash
pytest
```

Confirm: **0 failures** required for commit to proceed.

## Notable Testing Gaps

- **Frontend**: No test framework configured — React components untested
- **E2E**: No browser automation (Playwright/Cypress) configured
- **Mocking external services**: No mocking setup (not needed until integrations added)
- **Performance tests**: Not implemented

---

*Testing analysis: 2026-06-20*
