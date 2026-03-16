# TradeDocs — Session Memory

## Completed
- Bootstrap: project structure, venv, docker-compose, initial Django migrations committed.
- pytest.ini fixed (missing [pytest] header added).
- PostgreSQL running via OrbStack/Docker Compose.
- **Layer 1, Session 1 — ****`accounts`**** app** ✓
  - Custom User model (email login, role field, soft-delete via is_active)
  - JWT auth endpoints: login, logout (blacklist), token/refresh, me
  - Permission classes: IsCompanyAdmin, IsCheckerOrAdmin, IsAnyRole, IsDocumentOwner
  - User management endpoints (Company Admin only): list, create, update role/active
  - 26/26 tests passing

## Patterns & Notes
- factory-boy: use `@factory.post_generation` with explicit `self.save()` for password setting. `PostGenerationMethodCall` + `skip_postgeneration_save=True` does NOT persist the password to DB.
- Settings use `python-decouple` for all env vars. DB config uses DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT individually (not DATABASE_URL) for local dev.
- `apps/accounts/apps.py` uses `label = "accounts"` to avoid Django admin conflicts.

- **Layer 1, Session 2 — ****`master_data`**** reference tables** ✓
  - 7 lookup models: Country, Port, Location, Incoterm, UOM, PaymentTerm, PreCarriageBy
  - DRF ModelViewSet with read/write permission split (IsAnyRole for GET, IsCheckerOrAdmin for writes)
  - All endpoints under `/api/v1/master-data/`
  - 41/41 tests passing; 67/67 total

## Patterns & Notes
- factory-boy: use `@factory.post_generation` with explicit `self.save()` for password setting. `PostGenerationMethodCall` + `skip_postgeneration_save=True` does NOT persist the password to DB.
- CountryFactory iso2/iso3 sequences: use letter-pair formula `chr(65 + (n//26)%26) + chr(65 + n%26)` — never use string slicing `[:2]` on sequences as it causes collisions when n≥10.
- Settings use `python-decouple` for all env vars. DB config uses DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT individually (not DATABASE_URL) for local dev.
- `apps/accounts/apps.py` uses `label = "accounts"` to avoid Django admin conflicts.

## Active Task
**Layer 1, Session 3 — Organisation model (FR-04)**
Organisation with addresses, tax codes, and role tags. Most complex master data model.
Branch: `feature/fr-04-organisation`

## Failed / Unresolved
- None.

## Next Action
Implement Layer 1, Session 3: Organisation model (FR-04.1–04.4) — header fields, OrganisationAddress (with Country FK), OrganisationTaxCode, OrganisationTag (EXPORTER/CONSIGNEE/BUYER/NOTIFY_PARTY).
