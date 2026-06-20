# Coding Conventions

**Analysis Date:** 2026-06-20

## Naming Patterns

**Files:**
- Python models: `PascalCase` with model name + `.py` (e.g., `models.py`, `views.py`, `services.py`, `serializers.py`)
- Python test files: `test_*.py` format (e.g., `test_models.py`, `test_views.py`)
- React components: `PascalCase` with `.tsx` extension (e.g., `LoginPage.tsx`, `AppLayout.tsx`)
- React pages: `PascalCase` with `Page` suffix (e.g., `ProformaInvoicePage.tsx`, `LoginPage.tsx`)
- API files: lowercase with snake_case (e.g., `proformaInvoices.ts`, `packingLists.ts`)
- Utility files: lowercase with snake_case (e.g., `constants.ts`, `apiErrors.ts`)

**Functions:**
- Python: `snake_case` (e.g., `generate_document_number()`, `perform_create()`, `select_for_update()`)
- TypeScript/React: `camelCase` (e.g., `onSubmit()`, `handleChange()`, `getTokens()`)
- Service methods: `snake_case` in Python (e.g., `transition()`, `get_queryset()`)

**Variables:**
- Python: `snake_case` (e.g., `pi_number`, `exporter`, `payment_terms`)
- TypeScript: `camelCase` for runtime variables (e.g., `activeSlide`, `errorMsg`)
- TypeScript: `UPPERCASE` for constants (e.g., `ROLES`, `DOCUMENT_STATUS`, `NAV_ITEMS`)

**Types:**
- TypeScript interfaces: `PascalCase` with suffix (e.g., `ProformaInvoiceLineItem`, `AuthUser`, `LoginFormValues`)
- Python constants: `UPPERCASE` for module-level constants (e.g., `DRAFT`, `PENDING_APPROVAL`, `EDITABLE_STATES`)
- Django model `TextChoices`: `PascalCase` (e.g., `ShipmentAllowance`)

## Code Style

**Formatting:**
- Backend: Follow PEP 8 — 4-space indentation, max 100-char line length (by convention in Django projects)
- Frontend: No formatter enforced via config — code follows pattern of inline styles and structured organization
- Comments: Always add a brief comment above functions that do something non-obvious

**Linting:**
- Frontend: ESLint with recommended rules via `eslint.config.js`
  - Base: `@eslint/js` recommended rules
  - TypeScript: `typescript-eslint` recommended rules
  - React: `eslint-plugin-react-hooks` and `eslint-plugin-react-refresh`
- Backend: No linter configured — relies on human review and PEP 8 discipline

## Import Organization

**Order (Backend - Python):**
1. Standard library imports (e.g., `from datetime import date`, `from decimal import Decimal`)
2. Third-party imports (e.g., `from django.conf import settings`, `from rest_framework import viewsets`)
3. App imports (relative to project root: `from apps.workflow.constants import DRAFT`)
4. Local app imports (within same app: `from .models import ProformaInvoice`)

**Order (Frontend - TypeScript):**
1. React/library imports (e.g., `import { useState } from "react"`, `import { useNavigate } from "react-router-dom"`)
2. Icon/UI library imports (e.g., `import { FileText, Package } from "lucide-react"`, `import { Dropdown, message } from "antd"`)
3. API/service imports (e.g., `import { loginUser } from "../../api/auth"`)
4. Store/context imports (e.g., `import { useAuth } from "../../store/AuthContext"`)
5. Type imports (e.g., `import type { AuthUser } from "../../api/auth"`)
6. Utility imports (e.g., `import { ROLES } from "../../utils/constants"`)

**Path Aliases:**
- Frontend: Paths are relative (e.g., `../api/auth`, `../../utils/constants`) — no configured aliases
- Backend: Django app paths use absolute imports from project root (e.g., `from apps.accounts.models import User`)

## Error Handling

**Patterns:**
- Backend views: Use DRF exceptions for HTTP errors — `ValidationError`, `PermissionDenied` from `rest_framework.exceptions`
  - Example from `apps/proforma_invoice/views.py`:
    ```python
    if instance.status not in EDITABLE_STATES:
        raise ValidationError(
            {"detail": f"Cannot edit a Proforma Invoice with status '{instance.status}'."}
        )
    ```
- Frontend: Try-catch blocks with user-facing error messages. Set error state and display in UI
  - Example from `LoginPage.tsx`:
    ```typescript
    try {
      const { user, accessToken, refreshToken } = await loginUser(values.email, values.password);
      login(user as AuthUser, accessToken, refreshToken);
    } catch {
      setErrorMsg("Invalid email or password. Please try again.");
    }
    ```

## Logging

**Framework:** Console logging only (no structured logging configured)

**Patterns:**
- Backend: Print statements for debugging (no observability framework in place)
- Frontend: Browser console for debugging — no server-side logging configured
- No log levels enforced

## Comments

**When to Comment:**
- Always add brief comment above functions that do something non-obvious
- Above models: docstring explaining the model's purpose and constraints
- Above views: docstring explaining the endpoint's purpose and restrictions
- Above complex business logic: explain the "why" not the "what"

**JSDoc/TSDoc:**
- Frontend: Minimal type-level comments — rely on TypeScript inference and interface names
- Backend: Django docstrings on models and services explaining business constraints
  - Example from `apps/proforma_invoice/models.py`:
    ```python
    class ProformaInvoice(models.Model):
        """
        Header record for a Proforma Invoice (FR-09).
        Line items and additional charges are stored as related models.
        """
    ```

## Function Design

**Size:** Keep functions focused on a single responsibility. Services contain business logic; views handle HTTP mapping.

**Parameters:**
- Backend views: Use class-based viewsets with methods — avoid long parameter lists
- Backend services: Accept document instance and action parameters
  - Example from `WorkflowService.transition()`:
    ```python
    @staticmethod
    def transition(document, document_type, action, performed_by, comment=""):
    ```

**Return Values:**
- Views return DRF Response objects with serialized data
- Services return modified model instances or None
- Factories return model instances via factory-boy

## Module Design

**Exports:**
- Backend apps export via `__init__.py` or explicit imports in views/serializers
- Frontend pages and API modules export as default exports or named exports depending on component type
  - API files export multiple named functions (e.g., `export async function createProformaInvoice()`)
  - Pages export default React components (e.g., `export default function LoginPage()`)

**Barrel Files:**
- Frontend: No barrel files used — all imports are direct (e.g., `from ../../api/auth` not `from ../../api`)
- Backend: Models imported from `.models`, views from `.views`, services from `.services`

## Status String Conventions

**Critical Rule:** Status strings in frontend come from `src/utils/constants.ts` — never hardcode "DRAFT", "APPROVED", etc.

From `src/utils/constants.ts`:
```typescript
export const DOCUMENT_STATUS = {
  DRAFT: "DRAFT",
  PENDING_APPROVAL: "PENDING_APPROVAL",
  APPROVED: "APPROVED",
  REWORK: "REWORK",
  PERMANENTLY_REJECTED: "PERMANENTLY_REJECTED",
} as const;
```

Usage in views: Access via `DOCUMENT_STATUS.DRAFT` not `"DRAFT"` string literals.

## Permission Classes

**Constraint #10 from technical_architecture.md:** All DRF views must explicitly declare `permission_classes`.

Example from `apps/proforma_invoice/views.py`:
```python
class ProformaInvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAnyRole]
```

Never omit `permission_classes` — even if using default permissions, must be explicit.

## Foreign Key Constraints

**Constraint #3:** All FK references to master data must use `on_delete=PROTECT`.

Example from `apps/proforma_invoice/models.py`:
```python
exporter = models.ForeignKey(
    "master_data.Organisation",
    on_delete=models.PROTECT,
    related_name="pi_as_exporter",
)
```

This prevents accidental deletion of referenced master data records.

## Field Types for Monetary/Weight Values

**Constraint #1:** All monetary amounts use `DecimalField(max_digits=15, decimal_places=2)` — never FloatField.
**Constraint #2:** All weights use `DecimalField(max_digits=12, decimal_places=3)` — never FloatField.

Decimal precision is required for financial accuracy and weight calculations.

---

*Convention analysis: 2026-06-20*
