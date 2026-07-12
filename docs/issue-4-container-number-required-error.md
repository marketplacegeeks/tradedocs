# Issue 4 — "Container Number Required" Error Investigation

## User Report
The system generates an error stating the "Container Number" field is required on Invoice & Packing List. User attempted to bypass using the space bar but the error persists.

## Investigation Findings

### The Field in Question

The field the user sees as "Container Number" is technically named `container_ref` throughout the codebase. It is labelled:
- **"Container Ref"** on the Create page (`PackingListCreatePage.tsx`)
- **"Container Reference"** on the Detail page

### Is `container_ref` Actually Required?

**No.** It is optional at every layer:

| Layer | Definition | Required? |
|---|---|---|
| Model (`apps/packing_list/models.py:192`) | `CharField(max_length=100, blank=True)` | No |
| Serializer (`apps/packing_list/serializers.py:110–112`) | `required=False, allow_blank=True, default=""` | No |
| Create frontend (`PackingListCreatePage.tsx:860`) | Validation skips `container_ref` entirely | No |
| Edit frontend (`PackingListEditPage.tsx:591`) | Displayed without `*`, no validation | No |

The serializer has an explicit note explaining why the override exists:
> "container_ref is optional — blank=True in the model but DRF still generates required=True without an explicit default"

### The Actual Cause of the Error

The create-page validation at `PackingListCreatePage.tsx:860–861` checks only these two fields:

```typescript
if (!c.marks_numbers || !c.seal_number) {
    message.error("Marks & Numbers and Seal Number are required.");
    return;
}
```

**`marks_numbers` and `seal_number` are required**, not `container_ref`. Both have:
- No `blank=True` on the model (Django enforces non-empty)
- No `required=False` override in the serializer
- An asterisk `*` next to their label in the Edit page UI

The user appears to be leaving `marks_numbers` or `seal_number` empty (or filling them only with a space, which may still fail server-side validation), and the error message "X is required" is being attributed to the wrong field.

### Why the Space Bar Workaround Fails

A single space character passes the JavaScript `!c.marks_numbers` check (a non-empty string is truthy), but Django's model validator or DRF's `CharField` with `allow_blank=False` (the default) will reject it server-side, returning a 400 error. So the space bar bypasses the frontend check but not the backend.

## What Proforma Invoice Has to Do With This

Nothing. There are no container fields on the Proforma Invoice form at all — `container_ref`, `marks_numbers`, and `seal_number` are exclusively Packing List fields.

## Recommended Action

No code change needed. Clarify with the user:
1. Which specific field is showing the error message?
2. Are `Marks & Numbers` and `Seal Number` being filled in?

If the error message wording is misleading, the frontend message at `PackingListCreatePage.tsx:861` could be updated to be more specific, e.g.:
```
"Marks & Numbers and Seal Number are required for each container."
```
