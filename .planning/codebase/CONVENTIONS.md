# Coding Conventions

**Analysis Date:** 2026-07-26

## Naming Patterns

**Python Files:**
- `models.py` - Django model definitions
- `views.py` - DRF view classes
- `serializers.py` - DRF serializers
- `services.py` - Business logic / service layer (non-model domain logic)
- `permissions.py` - Custom DRF permission classes
- `urls.py` - URL routing
- `management/commands/` - Django management commands
- `tests/` - All test files (factories, test_models, test_views, test_bulk_workflow, etc.)

**Python Functions & Methods:**
- Use `snake_case` for all function and method names
- Property getters use `@property` decorator: `def full_name(self)` → `user.full_name`
- Helper functions: `snake_case`, e.g., `generate_document_number()`, `auth_client()`
- Test functions: `test_*` prefix, descriptive names describing the scenario
  - Example: `test_maker_can_create`, `test_checker_cannot_list_users`, `test_pi_date_defaults_to_today`

**Python Variables & Attributes:**
- Model fields: `snake_case` (e.g., `pi_number`, `phone_country_code`, `is_active`)
- Local variables: `snake_case` (e.g., `response`, `user`, `api_client`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DRAFT`, `COMMENT_REQUIRED_ACTIONS`)
- Enums / TextChoices: `UPPER_SNAKE_CASE` for choice keys
  - Example: `UserRole.SUPER_ADMIN`, `UserRole.COMPANY_ADMIN`

**Django Model Names:**
- Singular form, PascalCase: `ProformaInvoice`, `ProformaInvoiceLineItem`, `AuditLog`
- Relationships named for clarity: `pi_as_exporter`, `pi_as_consignee`, `pi_port_of_loading`
- Meta.db_table uses explicit lowercase table name: `accounts_user`, `proforma_invoice`

**TypeScript Files:**
- Component files: `PascalCase.tsx` (e.g., `PurchaseOrderListPage.tsx`, `AppLayout.tsx`)
- Hook/utility files: `camelCase.ts` (e.g., `axiosInstance.ts`, `constants.ts`, `apiErrors.ts`)
- API module files: `camelCase.ts` (e.g., `banks.ts`, `organisations.ts`, `purchaseOrders.ts`)

**TypeScript Functions & Variables:**
- Functions: `camelCase` (e.g., `listBanks()`, `createBank()`, `extractApiError()`)
- Variables: `camelCase` (e.g., `activeStatus`, `searchQuery`, `vendorFilter`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `PI_LIST_URL`, `STATUS_TABS`, `COLUMNS`)
- React Components: `PascalCase` (e.g., `PurchaseOrderListPage`, `AppLayout`)
- Types/Interfaces: `PascalCase` (e.g., `Bank`, `BankPayload`, `SortKey`)

**TypeScript Enums & Constants:**
- Import from `src/utils/constants.ts` and use as `DOCUMENT_STATUS.DRAFT`, `ROLES.MAKER`
- Never hardcode status strings ("DRAFT", "APPROVED") in components
- Status label mappings: `DOCUMENT_STATUS_LABELS`, `DOCUMENT_STATUS_CHIP`
- Role labels: `ROLES` exported as const objects with TypeScript `as const`

## Code Style

**Formatting:**
- Python: PEP 8 style (4-space indentation)
- TypeScript: 2-space indentation
- Max line length: No hard limit enforced, but prefer readable widths (~100 characters for Python, flexible for TypeScript)

**Linting:**
- Frontend: ESLint with `eslint.config.js` at `frontend/eslint.config.js`
- Backend: No explicit linter configured; relies on conventions
- All TypeScript: ESLint rules in flat config, targets `**/*.{ts,tsx}` files

**Linter Configuration:**
```javascript
// frontend/eslint.config.js
- Extends: @eslint/js recommended, TypeScript ESLint recommended, React Hooks recommended
- React Refresh plugin for dev HMR safety
```

**Type Safety (TypeScript):**
- Use explicit return types on exported functions: `async function listBanks(): Promise<Bank[]>`
- Define interfaces for API responses: `interface Bank { id: number; is_active: boolean; ... }`
- Use mapped types to derive payload types: `interface BankPayload { ... }`
- Use `as const` for literal types in constant objects
- Use `Record<Key, Value>` for mappings: `DOCUMENT_STATUS_LABELS: Record<string, string>`

## Import Organization

**Python:**
1. Standard library imports: `import re`, `from datetime import date`
2. Third-party imports: `from django.db import models`, `from rest_framework import generics`
3. Local app imports: `from apps.accounts.models import User`, `from .models import ProformaInvoice`
4. Relative imports within same app: `from .serializers import UserCreateSerializer`

**Example (Python):**
```python
import factory
from datetime import date

from apps.accounts.tests.factories import MakerFactory
from apps.master_data.tests.factories import OrganisationFactory
from apps.proforma_invoice.models import ProformaInvoice
from apps.workflow.constants import DRAFT
```

**TypeScript:**
1. External libraries: `import axios from "axios"`, `import { useState } from "react"`
2. Tanstack React Query: `import { useQuery } from "@tanstack/react-query"`
3. UI libraries: `import { Select } from "antd"`, `import { Plus } from "lucide-react"`
4. Local API modules: `import { listBanks } from "../../api/banks"`
5. Local components: `import PaginationBar from "../../components/common/Pagination"`
6. Utilities & constants: `import { DOCUMENT_STATUS } from "../../utils/constants"`
7. Hooks: `import { useAuth } from "../../store/AuthContext"`

**Path Aliases:**
- No configured path aliases; use relative imports (`../../api/banks`)

**Comments at Top of File:**
- TypeScript API files start with header comment: `// All API calls for the {Resource} resource.`
- TypeScript page components start with header comment: `// {Feature} page (FR-XX). ...`
- Python service files document constraints: `"""Constraint #16: ... Constraint #17: ..."""`

## Error Handling

**Python (Backend):**
- REST API errors: Always return a `Response` with appropriate status code and serialized error message
- Validation errors: Raise `serializers.ValidationError({"field": "error message"})`
- Permission errors: Raise `rest_framework.permissions.PermissionDenied("Reason")`
- Not found: Use DRF's built-in 404 (generics.RetrieveUpdateAPIView raises automatically)
- Workflow violations: Raise `ValidationError` with `{"action": "..."}` key
- Database integrity: PROTECT on all FK references to master data — let DB reject deletes with detailed errors

**Example (Python):**
```python
# In serializer.validate():
if attrs.get("role") == UserRole.COMPANY_ADMIN:
    if not request or request.user.role != UserRole.SUPER_ADMIN:
        raise serializers.ValidationError(
            {"role": "Only a Super Admin can create Company Admin users."}
        )

# In WorkflowService:
if action not in allowed_actions:
    raise ValidationError({
        "action": (
            f"Action '{action}' is not allowed when status is '{current_status}'. "
            f"Allowed actions: {list(allowed_actions.keys())}."
        )
    })
```

**TypeScript (Frontend):**
- API errors extracted to human-readable text via `extractApiError()` helper
- Single detail message: `obj.detail` (permissions, workflow blocks)
- Field-level errors: `{ field: [messages] }` converted to lines
- 500-level errors: Return generic "contact admin" message, never show raw error
- Nested serializer errors: `{ field: [{ subField: "error" }] }` → `Row N — subField: error`

**Example (TypeScript):**
```typescript
// frontend/src/utils/apiErrors.ts
export function extractApiError(err: unknown, fallback = "..."): string {
  const response = (err as { response?: { ... } })?.response;
  if (response?.status && response.status >= 500) {
    return "An unexpected server error occurred...";
  }
  // Handle { detail: "…" } or { field: […] }
  if (typeof obj.detail === "string") return obj.detail;
  // Collect all field errors into readable lines
}
```

## Logging

**Framework:** Python `print()` or Django logging (no centralized logging middleware configured)

**Patterns:**
- Minimal logging in views — rely on DRF's automatic response logging
- Service layer logs critical business decisions (status transitions, document number generation)
- WorkflowService logs every transition to AuditLog (always written in `transaction.atomic()`)

**Example (Python):**
```python
# apps/workflow/services.py
@staticmethod
def transition(document, document_type, action, performed_by, comment=""):
    # Validate, apply action, write AuditLog in same transaction
    with transaction.atomic():
        document.status = next_status
        document.save()
        AuditLog.objects.create(
            document_type=document_type,
            document_id=document.pk,
            action=action,
            performed_by=performed_by,
            comment=comment,
        )
```

## Comments

**When to Comment:**
- Non-obvious business logic: Explain the "why" not the "what"
- Constraints from technical_architecture.md: Reference the constraint number
- Temporary workarounds: Mark with "FIXME" or "TODO"
- Complex calculations: Brief explanation of formula or algorithm
- External API quirks: Document non-obvious behavior

**JSDoc/TSDoc:**
- TypeScript exported functions: Include JSDoc block with brief description
- Python not required but appreciated for complex service methods

**Example (TypeScript):**
```typescript
/** Fetch all bank accounts. Used for the Bank list page and PI/CI dropdowns. */
export async function listBanks(): Promise<Bank[]> {
  const { data } = await api.get<Bank[]>("/master-data/banks/");
  return data;
}

/** Deactivate a bank account. It will no longer appear in document dropdowns. */
export async function deactivateBank(id: number): Promise<Bank> {
  const { data } = await api.patch<Bank>(`/master-data/banks/${id}/`, { is_active: false });
  return data;
}
```

**Example (Python):**
```python
def create_user(self, email, password=None, **extra_fields):
    if not email:
        raise ValueError("Email is required")
    email = self.normalize_email(email)
    user = self.model(email=email, **extra_fields)
    user.set_password(password)
    user.save(using=self._db)
    return user

# Constraint #8: Users are never hard-deleted — set is_active=False instead.
is_active = models.BooleanField(default=True)
```

## Function Design

**Size (Python):**
- Aim for <50 lines per function in views/serializers
- Service methods can be longer if they're focused on one business operation
- Generics-based views often <20 lines when using DRF's built-in patterns

**Parameters:**
- Avoid excessive parameters; use a config dict or model instance when >3 params
- Service methods accept a model instance + metadata (user, comment) not field values

**Return Values:**
- Views return `Response` objects (DRF handles serialization)
- Service methods return the modified model instance or a tuple of (instance, success)
- Factory methods return created model instance

**Example (Python):**
```python
class UserListCreateView(generics.ListCreateAPIView):
    """GET /api/v1/users/ — list. POST /api/v1/users/ — create."""
    permission_classes = [IsCompanyAdmin]
    queryset = User.objects.all().order_by("date_joined")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserListSerializer
```

**Size (TypeScript):**
- Component functions <200 lines (split large pages into sub-components)
- Utility functions <30 lines
- API functions <15 lines (just handle request/response transformation)

**Parameters (TypeScript):**
- Use object destructuring for optional props: `{ page = 1, limit = 10 } = {}`
- React components use named props, not positional
- API functions accept strongly-typed objects: `(payload: BankPayload)`

**Return Values (TypeScript):**
- API functions return typed promises: `Promise<Bank[]>`, `Promise<Bank>`
- Components return JSX elements
- Hooks return typed data: `{ data: Bank[], isLoading: boolean, error: Error | null }`

**Example (TypeScript):**
```typescript
export async function createBank(payload: BankPayload): Promise<Bank> {
  const { data } = await api.post<Bank>("/master-data/banks/", payload);
  return data;
}

export async function updateBank(id: number, payload: Partial<BankPayload>): Promise<Bank> {
  const { data } = await api.patch<Bank>(`/master-data/banks/${id}/`, payload);
  return data;
}
```

## Module Design

**Python Exports:**
- Models export the model class + any related enums (e.g., `UserRole`)
- Serializers export the serializer class (often multiple per model)
- Views export the view class
- Services export service functions or service class with static methods
- Permissions export permission classes

**Barrel Files:**
- Not used in backend
- Not used in frontend (imports are direct)

**Example (Python):**
```python
# apps/accounts/models.py
class UserRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    COMPANY_ADMIN = "COMPANY_ADMIN", "Company Admin"
    # ...

class User(AbstractBaseUser, PermissionsMixin):
    role = models.CharField(max_length=20, choices=UserRole.choices)
    # ...

# apps/accounts/permissions.py
class IsCompanyAdmin(BasePermission):
    """Grants access to COMPANY_ADMIN and SUPER_ADMIN."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    request.user.role in _ADMIN_ROLES)
```

**TypeScript Module Exports:**
- API modules export: types + async functions
- Constant modules export: typed const objects with `as const`
- Component modules export: React component (default) + optional types

**Example (TypeScript):**
```typescript
// src/api/banks.ts
export interface Bank { id: number; is_active: boolean; ... }
export interface BankPayload { organisation: number; ... }
export async function listBanks(): Promise<Bank[]> { ... }
export async function createBank(payload: BankPayload): Promise<Bank> { ... }

// src/utils/constants.ts
export const ROLES = {
  SUPER_ADMIN: "SUPER_ADMIN",
  COMPANY_ADMIN: "COMPANY_ADMIN",
  CHECKER: "CHECKER",
  MAKER: "MAKER",
} as const;
export type Role = (typeof ROLES)[keyof typeof ROLES];
```

---

*Convention analysis: 2026-07-26*
