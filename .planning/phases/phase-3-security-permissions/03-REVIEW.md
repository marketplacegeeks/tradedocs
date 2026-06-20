---
phase: 03-security-permissions
reviewed: 2026-06-20T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - apps/accounts/permissions.py
  - apps/certificate_of_analysis/serializers.py
  - apps/certificate_of_analysis/tests/test_views.py
  - apps/certificate_of_analysis/views.py
  - apps/commercial_invoice/tests/test_views.py
  - apps/commercial_invoice/views.py
  - apps/packing_list/serializers.py
  - apps/packing_list/tests/test_views.py
  - apps/packing_list/views.py
  - apps/proforma_invoice/tests/test_views.py
  - apps/proforma_invoice/views.py
  - apps/workflow/services.py
  - tradetocs/settings.py
findings:
  critical: 1
  warning: 5
  info: 2
  total: 8
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-06-20
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

This phase added security hardening for all document viewsets (PI, PL/CI, COA) — implementing `IsMakerOrAdmin` permission guards, role-based write restrictions, and new tests confirming Checker read-only enforcement. The core workflow service and permission classes are well-structured. However, one critical logic bug was found where `SUPER_ADMIN` is silently denied CI update access by an object-level ownership check that only names `COMPANY_ADMIN`, and five warnings covering a time-of-check race condition shared across PI/COA/CI, missing `updated_at` in signed-copy saves, no MIME-type validation on uploads, and a missing pagination class on the CI list endpoint.

---

## Critical Issues

### CR-01: SUPER_ADMIN blocked from editing Commercial Invoice and CI line items

**File:** `apps/commercial_invoice/views.py:85-87` and `apps/commercial_invoice/views.py:169-171`

**Issue:** `CommercialInvoiceViewSet.perform_update()` and `CommercialInvoiceLineItemViewSet.perform_update()` both gate object-level write access with:

```python
if (pl.created_by != self.request.user
        and self.request.user.role != UserRole.COMPANY_ADMIN):
    raise PermissionDenied("Only the document creator can edit this Commercial Invoice.")
```

`SUPER_ADMIN` is not listed. The view-level `IsMakerOrAdmin` permission (which does include `SUPER_ADMIN`) allows a Super Admin through, but the object-level check immediately denies them unless they personally created the CI. This contradicts the project rule that `SUPER_ADMIN` has at least `COMPANY_ADMIN`-level access everywhere, and breaks the Super Admin's ability to correct financial fields on any CI.

**Fix:**

```python
# In CommercialInvoiceViewSet.perform_update():
if (pl.created_by != self.request.user
        and self.request.user.role not in (
            UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN
        )):
    raise PermissionDenied("Only the document creator can edit this Commercial Invoice.")

# In CommercialInvoiceLineItemViewSet.perform_update():
if (pl.created_by != self.request.user
        and self.request.user.role not in (
            UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN
        )):
    raise PermissionDenied("Only the document creator can edit rates.")
```

Add a test in `apps/commercial_invoice/tests/test_views.py`:

```python
def test_super_admin_can_patch_ci(self):
    from apps.accounts.tests.factories import SuperAdminFactory
    maker = MakerFactory()
    pl = PackingListFactory(status=DRAFT, created_by=maker)
    ci = CommercialInvoiceFactory(packing_list=pl, status=DRAFT, created_by=maker)
    resp = auth_client(SuperAdminFactory()).patch(
        ci_detail_url(ci.pk), {"lc_details": "SUPER-ADMIN-EDIT"}, format="json"
    )
    assert resp.status_code == 200
```

---

## Warnings

### WR-01: Time-of-check race condition in PI, COA, and CI perform_update (no SELECT FOR UPDATE)

**File:** `apps/proforma_invoice/views.py:132-142`, `apps/certificate_of_analysis/views.py:79-87`, `apps/commercial_invoice/views.py:78-88`

**Issue:** All three `perform_update()` methods call `self.get_object()` a second time to check `instance.status`, without acquiring a row-level lock. The DRF `update()` flow already fetched the instance once (for object-level permission checks); the second fetch inside `perform_update` is redundant and creates a time-of-check to time-of-use window. A concurrent workflow transition (e.g., a Maker submitting while an Admin is patching) can change the document status between the status check and `serializer.save()`, allowing an edit to land on a `PENDING_APPROVAL` document.

The packing list view fixed this exact issue (commit WR-03) using `select_for_update()` at `apps/packing_list/views.py:231`. The other three views were not updated consistently.

**Fix** (shown for COA; apply the same pattern to PI and CI):

```python
# apps/certificate_of_analysis/views.py
def perform_update(self, serializer):
    with transaction.atomic():
        # Lock the row so a concurrent workflow transition cannot change status
        # between this check and save.
        instance = CertificateOfAnalysis.objects.select_for_update().get(
            pk=serializer.instance.pk
        )
        if instance.status not in EDITABLE_STATES:
            raise ValidationError(
                {"detail": f"Cannot edit a COA with status '{instance.status}'."}
            )
        if self.request.user.role == UserRole.CHECKER:
            raise PermissionDenied("Checkers cannot edit COAs.")
        serializer.save()
```

Add the missing `from django.db import transaction` import. Apply the same pattern in `ProformaInvoiceViewSet.perform_update()` and `CommercialInvoiceViewSet.perform_update()`.

---

### WR-02: PI and CI signed-copy saves omit "updated_at" from update_fields

**File:** `apps/proforma_invoice/views.py:227`, `apps/commercial_invoice/views.py:125`

**Issue:** When a signed copy is uploaded for a PI or CI, `updated_at` is not included in `update_fields`:

```python
# PI - line 227
pi.save(update_fields=["signed_copy"])

# CI - line 125
ci.save(update_fields=["signed_copy"])
```

The PL signed-copy endpoint correctly uses `update_fields=["signed_copy", "updated_at"]` (line 414 of `apps/packing_list/views.py`). The omission means `updated_at` is stale after a signed-copy upload on PI and CI, which breaks any audit/cache logic that relies on this field to detect document changes.

**Fix:**

```python
# apps/proforma_invoice/views.py line 227
pi.save(update_fields=["signed_copy", "updated_at"])

# apps/commercial_invoice/views.py line 125
ci.save(update_fields=["signed_copy", "updated_at"])
```

---

### WR-03: No MIME-type or file-extension validation on signed-copy uploads

**File:** `apps/proforma_invoice/views.py:197-230`, `apps/commercial_invoice/views.py:92-128`, `apps/packing_list/views.py:381-417`

**Issue:** All three signed-copy endpoints validate only file size. Any file type is accepted — a user can upload a `.html`, `.js`, or binary file and it will be stored without complaint. While Django's file storage does not execute files server-side, the stored file name (including extension) is surfaced in `signed_copy_url` and could mislead downstream consumers or be re-served with a dangerous MIME type.

**Fix:** Add a content-type check immediately after the file presence check in all three views:

```python
ALLOWED_SIGNED_COPY_TYPES = {"application/pdf"}

uploaded_file = request.FILES.get("file")
if not uploaded_file:
    raise ValidationError({"file": "A file is required."})

if uploaded_file.content_type not in ALLOWED_SIGNED_COPY_TYPES:
    raise ValidationError({"file": "Only PDF files are accepted as signed copies."})
```

Move the constant to a shared location (e.g., `tradetocs/constants.py`) so all three endpoints use the same list.

---

### WR-04: CommercialInvoiceViewSet missing pagination_class

**File:** `apps/commercial_invoice/views.py:30-67`

**Issue:** `CommercialInvoiceViewSet` does not declare `pagination_class`, whereas every other document-level viewset (`ProformaInvoiceViewSet`, `PackingListViewSet`, `CertificateOfAnalysisViewSet`) uses `StandardPageNumberPagination`. As the number of invoices grows, the list endpoint will return an unbounded payload that could exhaust memory or cause a slow response.

**Fix:**

```python
from tradetocs.pagination import StandardPageNumberPagination

class CommercialInvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAnyRole]
    pagination_class = StandardPageNumberPagination   # add this line
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ...
```

---

### WR-05: Any authenticated user (including Checker) can upload signed copies

**File:** `apps/proforma_invoice/views.py:197`, `apps/commercial_invoice/views.py:92`, `apps/packing_list/views.py:381`

**Issue:** All three `signed-copy` action endpoints use `permission_classes=[IsAnyRole]` (or `[IsAuthenticated, IsAnyRole]` on COA), which allows any authenticated user — including Checkers — to upload a signed copy. FR-08.4 describes signed-copy upload as a Maker action (confirming receipt of a signed physical document), not a Checker action. The existing tests (`test_upload_blocked_for_pending_approval`) use `CheckerFactory()` but only test the status guard, not a role guard. There is no test verifying that Checkers are blocked from uploading to an APPROVED document.

**Fix:** Change the `permission_classes` on the `signed_copy` action to restrict it to Makers and Admins:

```python
@action(
    detail=True, methods=["post"], url_path="signed-copy",
    permission_classes=[IsAuthenticated, IsMakerOrAdmin],
)
def signed_copy(self, request, pk=None):
    ...
```

Add a denial test:

```python
def test_checker_cannot_upload_signed_copy(self):
    pl = PackingListFactory(status=APPROVED)
    resp = auth_client(CheckerFactory()).post(
        pl_signed_copy_url(pl.pk),
        {"file": _small_pdf()},
        format="multipart",
    )
    assert resp.status_code == 403
```

Apply the same fix and tests to PI and CI signed-copy endpoints.

---

## Info

### IN-01: settings.py DEBUG defaults to True — risky if env var omitted in production

**File:** `tradetocs/settings.py:9`

**Issue:**

```python
DEBUG = config("TRADETOCS_DEBUG", default=True, cast=bool)
```

If `TRADETOCS_DEBUG` is not set in the environment (e.g., a deployment script omits it), Django runs in debug mode — exposing full tracebacks, SQL queries, and internal paths in error responses. The `.env` file (gitignored) sets this correctly for development, but there is no guard that fails loudly if the env var is missing in a non-development context.

**Fix:** Change the default to `False` so production deployments are safe by default. Development environments can set `TRADETOCS_DEBUG=True` explicitly in `.env`:

```python
DEBUG = config("TRADETOCS_DEBUG", default=False, cast=bool)
```

---

### IN-02: perform_update in PI, COA, and CI calls self.get_object() unnecessarily

**File:** `apps/proforma_invoice/views.py:133`, `apps/certificate_of_analysis/views.py:80`, `apps/commercial_invoice/views.py:79`

**Issue:** DRF's standard `ModelMixin.update()` already fetches the instance and passes it to `get_serializer()`, which sets `serializer.instance`. Calling `self.get_object()` again inside `perform_update()` issues an extra database query per update request and, more importantly, operates on a potentially stale object (the same race condition described in WR-01). The serializer already holds the correct instance via `serializer.instance`.

**Fix:** Remove the redundant `self.get_object()` call. Use `serializer.instance` directly:

```python
def perform_update(self, serializer):
    instance = serializer.instance   # already fetched by DRF update()
    if instance.status not in EDITABLE_STATES:
        raise ValidationError(...)
    ...
    serializer.save()
```

Note: WR-01 recommends wrapping this in `select_for_update()` — if that fix is applied, use `CertificateOfAnalysis.objects.select_for_update().get(pk=serializer.instance.pk)` rather than `serializer.instance` directly, so the lock is acquired.

---

_Reviewed: 2026-06-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
