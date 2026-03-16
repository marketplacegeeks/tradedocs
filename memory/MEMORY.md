# TradeDocs — Session Memory

## Completed
- Bootstrap: project structure, venv, docker-compose, initial Django migrations committed.
- pytest.ini fixed (missing [pytest] header added).
- PostgreSQL running via OrbStack/Docker Compose.
- **Layer 1, Session 1 — `accounts` app** ✓
  - Custom User model (email login, role field, soft-delete via is_active)
  - JWT auth endpoints: login, logout (blacklist), token/refresh, me
  - Permission classes: IsCompanyAdmin, IsCheckerOrAdmin, IsAnyRole, IsDocumentOwner
  - User management endpoints (Company Admin only): list, create, update role/active
  - 26/26 tests passing

## Patterns & Notes
- factory-boy: use `@factory.post_generation` with explicit `self.save()` for password setting. `PostGenerationMethodCall` + `skip_postgeneration_save=True` does NOT persist the password to DB.
- Settings use `python-decouple` for all env vars. DB config uses DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT individually (not DATABASE_URL) for local dev.
- `apps/accounts/apps.py` uses `label = "accounts"` to avoid Django admin conflicts.

## Active Task
**Layer 1, Session 2 — `master_data` reference tables**
Country, Port, Location, Incoterm, UOM, PaymentTerm, PreCarriageBy models + API endpoints.
Branch: `feature/fr-06-reference-data`

## Failed / Unresolved
- None.

## Next Action
Implement Layer 1, Session 2: reference data models in `apps/master_data/` — Country, Port, Location, Incoterm, UOM, PaymentTerm, PreCarriageBy. Simple lookup tables managed by Company Admin.
