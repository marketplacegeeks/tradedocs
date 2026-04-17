# Multi-Currency Support Design Specification

**Date:** 2026-04-17
**Feature:** Multi-Currency Support for Proforma Invoice & Commercial Invoice
**Approach:** Field Renaming + Data Migration (Approach 1)

---

## Overview

Enable Proforma Invoices and Commercial Invoices to support multiple currencies beyond USD. Each PI will have a single currency for all line items and charges. Commercial Invoices will inherit currency from their linked Proforma Invoice.

### Key Design Decisions

1. **Single currency per PI** - All line items, charges, and totals use the same currency
2. **No currency conversion** - Users enter amounts directly in the selected currency
3. **Currency mandatory** - No defaults, no fallback logic; currency must be selected
4. **CI inherits from PI** - Commercial Invoice uses the same currency as its linked PI
5. **Clean field names** - Rename `rate_usd`/`amount_usd` → `rate`/`amount` (no "_usd" suffix)
6. **Backward compatibility** - Data migration sets all existing records to USD

---

## Backend Architecture

### 1. Model Changes

#### ProformaInvoice Model

**New field:**
```python
currency = models.ForeignKey(
    "master_data.Currency",
    on_delete=models.PROTECT,
    help_text="Currency for all monetary values on this Proforma Invoice"
)
```

**Constraints:**
- `NOT NULL` (required field)
- `on_delete=PROTECT` - Cannot delete Currency if PIs reference it (matches constraint #7)

#### Field Renames

**ProformaInvoiceLineItem:**
- `rate_usd` → `rate` (DecimalField, max_digits=15, decimal_places=2)
- `amount_usd` → `amount` (DecimalField, max_digits=15, decimal_places=2, editable=False)

**ProformaInvoiceCharge:**
- `amount_usd` → `amount` (DecimalField, max_digits=15, decimal_places=2)

**CommercialInvoiceLineItem:**
- `rate_usd` → `rate` (DecimalField, max_digits=15, decimal_places=2)
- `amount_usd` → `amount` (DecimalField, max_digits=15, decimal_places=2, editable=False)

**No changes to:**
- ProformaInvoice incoterm cost fields: `freight`, `insurance_amount`, `import_duty`, `destination_charges` (already generic names)
- CommercialInvoice cost fields: `fob_rate`, `freight`, `insurance` (already generic names)
- CommercialInvoice model - no currency field needed (inherits from PI via `packing_list.proforma_invoice`)

### 2. Database Migration Strategy

Three-step migration process to ensure zero data loss:

#### Migration 1: Add Fields
```python
# apps/proforma_invoice/migrations/000X_add_currency_and_rename_fields.py

operations = [
    # Add currency FK (nullable initially)
    migrations.AddField(
        model_name='proformainvoice',
        name='currency',
        field=models.ForeignKey(
            'master_data.Currency',
            on_delete=models.PROTECT,
            null=True,
            blank=True
        ),
    ),
    # Add new "rate" field (copy data from rate_usd)
    migrations.AddField(
        model_name='proformainvoicelineitem',
        name='rate',
        field=models.DecimalField(max_digits=15, decimal_places=2, null=True),
    ),
    migrations.AddField(
        model_name='proformainvoicelineitem',
        name='amount',
        field=models.DecimalField(max_digits=15, decimal_places=2, editable=False, null=True),
    ),
    # Repeat for ProformaInvoiceCharge
    migrations.AddField(
        model_name='proformainvoicecharge',
        name='amount',
        field=models.DecimalField(max_digits=15, decimal_places=2, null=True),
    ),
    # Repeat for CommercialInvoiceLineItem
    migrations.AddField(
        model_name='commercialinvoicelineitem',
        name='rate',
        field=models.DecimalField(max_digits=15, decimal_places=2, null=True),
    ),
    migrations.AddField(
        model_name='commercialinvoicelineitem',
        name='amount',
        field=models.DecimalField(max_digits=15, decimal_places=2, editable=False, null=True),
    ),
]
```

#### Migration 2: Data Migration
```python
# apps/proforma_invoice/migrations/000Y_migrate_usd_data.py

def forward(apps, schema_editor):
    ProformaInvoice = apps.get_model('proforma_invoice', 'ProformaInvoice')
    ProformaInvoiceLineItem = apps.get_model('proforma_invoice', 'ProformaInvoiceLineItem')
    ProformaInvoiceCharge = apps.get_model('proforma_invoice', 'ProformaInvoiceCharge')
    CommercialInvoiceLineItem = apps.get_model('commercial_invoice', 'CommercialInvoiceLineItem')
    Currency = apps.get_model('master_data', 'Currency')

    # Get or create USD currency
    usd, created = Currency.objects.get_or_create(
        code='USD',
        defaults={
            'name': 'US Dollar',
            'is_active': True
        }
    )

    # Set all existing PIs to USD
    ProformaInvoice.objects.filter(currency__isnull=True).update(currency=usd)

    # Copy rate_usd → rate, amount_usd → amount for PI line items
    for item in ProformaInvoiceLineItem.objects.all():
        item.rate = item.rate_usd
        item.amount = item.amount_usd
        item.save(update_fields=['rate', 'amount'])

    # Copy amount_usd → amount for PI charges
    for charge in ProformaInvoiceCharge.objects.all():
        charge.amount = charge.amount_usd
        charge.save(update_fields=['amount'])

    # Copy rate_usd → rate, amount_usd → amount for CI line items
    for item in CommercialInvoiceLineItem.objects.all():
        item.rate = item.rate_usd
        item.amount = item.amount_usd
        item.save(update_fields=['rate', 'amount'])

def backward(apps, schema_editor):
    # Reverse migration: copy data back to old fields if needed
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('proforma_invoice', '000X_add_currency_and_rename_fields'),
    ]
    operations = [
        migrations.RunPython(forward, backward),
    ]
```

#### Migration 3: Cleanup
```python
# apps/proforma_invoice/migrations/000Z_remove_usd_fields.py

operations = [
    # Make currency NOT NULL
    migrations.AlterField(
        model_name='proformainvoice',
        name='currency',
        field=models.ForeignKey(
            'master_data.Currency',
            on_delete=models.PROTECT,
        ),
    ),
    # Make new fields NOT NULL
    migrations.AlterField(
        model_name='proformainvoicelineitem',
        name='rate',
        field=models.DecimalField(max_digits=15, decimal_places=2),
    ),
    migrations.AlterField(
        model_name='proformainvoicelineitem',
        name='amount',
        field=models.DecimalField(max_digits=15, decimal_places=2, editable=False),
    ),
    # Drop old USD fields
    migrations.RemoveField('proformainvoicelineitem', 'rate_usd'),
    migrations.RemoveField('proformainvoicelineitem', 'amount_usd'),
    migrations.RemoveField('proformainvoicecharge', 'amount_usd'),
    migrations.RemoveField('commercialinvoicelineitem', 'rate_usd'),
    migrations.RemoveField('commercialinvoicelineitem', 'amount_usd'),
]
```

### 3. Serializer Changes

#### ProformaInvoiceSerializer

**New fields:**
```python
currency = serializers.PrimaryKeyRelatedField(
    queryset=Currency.objects.filter(is_active=True),
    required=True,
    help_text="Currency for all monetary values on this PI"
)
currency_display = serializers.SerializerMethodField()

def get_currency_display(self, obj):
    return {
        "id": obj.currency.id,
        "code": obj.currency.code,
        "name": obj.currency.name
    }
```

**Validation rules:**
- Currency is required on create (no default)
- Currency cannot be changed once PI has line items (enforce in `update()` method)

**Field name updates:**
- All references to `rate_usd` → `rate`
- All references to `amount_usd` → `amount`

#### ProformaInvoiceLineItemSerializer

**Field renames:**
```python
rate = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
```

No currency field - inherited from parent PI.

#### CommercialInvoiceSerializer

**Add read-only currency display:**
```python
currency_display = serializers.SerializerMethodField()

def get_currency_display(self, obj):
    pi = obj.packing_list.proforma_invoice
    return {
        "id": pi.currency.id,
        "code": pi.currency.code,
        "name": pi.currency.name
    }
```

#### CommercialInvoiceLineItemSerializer

**Field renames:**
```python
rate = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
```

### 4. API Response Format

**PI Detail Response:**
```json
{
  "id": 24,
  "pi_number": "PI-2026-0016",
  "currency": 2,
  "currency_display": {
    "id": 2,
    "code": "INR",
    "name": "Indian Rupee"
  },
  "line_items": [
    {
      "id": 45,
      "hsn_code": "28371100",
      "item_code": "123456",
      "description": "SODIUM CYANIDE",
      "quantity": "20.000",
      "rate": "2.15",
      "amount": "43.00"
    }
  ],
  "charges": [
    {
      "id": 12,
      "description": "Freight",
      "amount": "500.00"
    }
  ]
}
```

**CI Detail Response:**
```json
{
  "id": 89,
  "ci_number": "CI-2026-0024",
  "currency_display": {
    "id": 2,
    "code": "INR",
    "name": "Indian Rupee"
  },
  "line_items": [
    {
      "item_code": "Item1",
      "description": "ANDO",
      "total_quantity": "3500.000",
      "rate": "100.00",
      "amount": "350000.00"
    }
  ]
}
```

---

## PDF Generation Updates

### 1. Proforma Invoice PDF (`pdf/proforma_invoice.py`)

#### Changes Required

**Get currency code (no fallback):**
```python
def generate_proforma_invoice_pdf_bytes(invoice) -> bytes:
    # Currency is mandatory - no if/else
    currency_code = invoice.currency.code
```

**Update table headers:**
```python
li_header = [
    Paragraph("<b>Sr.</b>", style_table_header),
    Paragraph("<b>HSN Code</b>", style_table_header),
    Paragraph("<b>Item Code</b>", style_table_header),
    Paragraph("<b>Description of Goods</b>", style_table_header),
    Paragraph("<b>Qty</b>", style_table_header),
    Paragraph(f"<b>Rate ({currency_code})</b>", style_table_header),  # Dynamic
    Paragraph(f"<b>Amount ({currency_code})</b>", style_table_header),  # Dynamic
]
```

**Update totals section:**
```python
# OLD:
Paragraph(f"${fmt_money(grand_total)}", style_text)

# NEW:
Paragraph(f"{currency_code} {fmt_money(grand_total)}", style_text)
```

**Update amount in words:**
```python
# Pass actual currency code instead of hardcoded "USD"
amount_to_words(final_total, currency=currency_code)
```

**All locations to update:**
1. Line items table header (lines 476-482)
2. Totals section - FOB Value (line 596)
3. Totals section - Cost breakdown labels (lines 599-606)
4. Invoice Total label (line 611)
5. Amount in Words (line 634)

### 2. Commercial Invoice PDF (`pdf/commercial_invoice_generator.py`)

#### Changes Required

**Get currency from linked PI (no fallback):**
```python
def build_ci_story(ci, styles) -> list:
    pl = ci.packing_list
    pi = pl.proforma_invoice
    currency_code = pi.currency.code  # Mandatory - no if/else
```

**Update table headers:**
```python
li_header = [
    Paragraph("<b>Sr.</b>", style_table_header),
    Paragraph("<b>HSN Code</b>", style_table_header),
    Paragraph("<b>No &amp; Kind of Packages</b>", style_table_header),
    Paragraph("<b>Item Code</b>", style_table_header),
    Paragraph("<b>Description of Goods</b>", style_table_header),
    Paragraph("<b>Qty</b>", style_table_header),
    Paragraph(f"<b>Rate ({currency_code})</b>", style_table_header),  # Dynamic
    Paragraph(f"<b>Amount ({currency_code})</b>", style_table_header),  # Dynamic
]
```

**Update cost breakdown:**
```python
breakdown_rows = [
    [Paragraph(f"<b>{breakdown_header}</b>", style_text), Paragraph("", style_text)],
    [Paragraph("FOB Value (Line Items):", style_text),
     Paragraph(f"{currency_code} {_fmt_money(total_amount_usd)}", style_amt)],  # Dynamic
]
if show_freight:
    breakdown_rows.append([
        Paragraph("Freight:", style_text),
        Paragraph(f"{currency_code} {_fmt_money(freight_amount)}", style_amt),  # Dynamic
    ])
if show_insurance:
    breakdown_rows.append([
        Paragraph("Insurance Amount:", style_text),
        Paragraph(f"{currency_code} {_fmt_money(insurance_amount)}", style_amt),  # Dynamic
    ])
```

**Update invoice total:**
```python
Paragraph(f"<b>${_fmt_money(invoice_total)}</b>", style_label)
# becomes:
Paragraph(f"<b>{currency_code} {_fmt_money(invoice_total)}</b>", style_label)
```

**Update amount in words:**
```python
_amount_to_words(invoice_total, currency=currency_code)
```

**All locations to update:**
1. Line items table header (lines 492-501)
2. Cost breakdown - FOB Value (line 629)
3. Cost breakdown - Freight (line 634)
4. Cost breakdown - Insurance (line 639)
5. Invoice Total (line 673)
6. Amount in Words (line 692)

---

## Frontend Changes

### 1. PI Detail Page (`ProformaInvoiceDetailPage.tsx`)

#### Currency Selection Section

**Placement:** Above line items table, after header information

**Behavior:**
- Show currency dropdown if no line items exist yet
- Lock currency selector once first line item is added
- Display selected currency as read-only if line items exist

**Implementation:**
```tsx
{/* Currency Selection - appears before line items table */}
{status === DOCUMENT_STATUS.DRAFT && !hasLineItems && (
  <div style={CARD}>
    <h3 style={SECTION_TITLE}>Currency</h3>
    <div style={{ marginBottom: 16 }}>
      <label style={LABEL}>
        Select Currency <span style={{ color: 'red' }}>*</span>
      </label>
      <Select
        style={{ width: '100%' }}
        value={pi.currency}
        onChange={(value) => updateCurrencyMutation.mutate(value)}
        options={currencies.map(c => ({
          label: `${c.code} - ${c.name}`,
          value: c.id
        }))}
        placeholder="Select currency for this Proforma Invoice"
      />
      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
        Currency cannot be changed after adding line items
      </p>
    </div>
  </div>
)}

{/* Show locked currency if line items exist */}
{hasLineItems && (
  <div style={{ ...CARD, background: 'var(--bg-base)' }}>
    <label style={LABEL}>Currency</label>
    <p style={{ fontSize: 14, fontWeight: 600 }}>
      {pi.currency_display?.code} - {pi.currency_display?.name}
    </p>
  </div>
)}
```

#### Block Line Item Addition Until Currency Selected

```tsx
const canAddLineItems = pi.currency !== null;

{/* Line Items Section */}
<div style={CARD}>
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
    <h3 style={SECTION_TITLE}>Line Items</h3>
    {status === DOCUMENT_STATUS.DRAFT && (
      <button
        style={canAddLineItems ? BTN_PRIMARY : BTN_DISABLED}
        onClick={() => setShowLineItemModal(true)}
        disabled={!canAddLineItems}
      >
        <Plus size={16} style={{ marginRight: 6 }} />
        Add Line Item
      </button>
    )}
  </div>

  {!canAddLineItems && (
    <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>
      Please select a currency above before adding line items
    </div>
  )}

  {/* Line items table ... */}
</div>
```

#### Update Table Headers

```tsx
<thead>
  <tr>
    <th>HSN Code</th>
    <th>Item Code</th>
    <th>Description</th>
    <th>Qty</th>
    <th>Rate ({pi.currency_display?.code})</th>  {/* Dynamic */}
    <th>Amount ({pi.currency_display?.code})</th>  {/* Dynamic */}
    <th>Actions</th>
  </tr>
</thead>
```

#### Display Amounts with Currency Code

```tsx
<td>{pi.currency_display?.code} {formatMoney(lineItem.amount)}</td>
```

### 2. PI List Page (`ProformaInvoiceListPage.tsx`)

**Show currency code with total amount:**
```tsx
<td>{pi.currency_display?.code} {formatMoney(pi.total_amount)}</td>
```

### 3. Packing List + CI Creation (`PackingListCreatePage.tsx`)

#### Step 4: Final Rates Section

**Currency display (read-only from PI):**
```tsx
{/* Step 4: Final Rates */}
<div style={CARD}>
  <h3 style={SECTION_TITLE}>Final Rates</h3>

  {/* Show currency (read-only from PI) */}
  <div style={{ marginBottom: 20, padding: 12, background: 'var(--bg-base)', borderRadius: 8 }}>
    <label style={LABEL}>Currency (from Proforma Invoice)</label>
    <p style={{ fontSize: 14, fontWeight: 600, margin: 0 }}>
      {selectedPI?.currency_display?.code} - {selectedPI?.currency_display?.name}
    </p>
  </div>

  {/* Final Rates Table */}
  <table>
    <thead>
      <tr>
        <th>Item Code</th>
        <th>Description</th>
        <th>No. & Kind of Packages</th>
        <th>Total Qty</th>
        <th>UOM</th>
        <th>Rate ({selectedPI?.currency_display?.code})</th>  {/* Dynamic */}
        <th>Amount ({selectedPI?.currency_display?.code})</th>  {/* Dynamic */}
      </tr>
    </thead>
    <tbody>
      {finalRatesItems.map(item => (
        <tr key={item.item_code}>
          {/* ... */}
          <td>{selectedPI?.currency_display?.code} {formatMoney(item.amount)}</td>
        </tr>
      ))}
    </tbody>
  </table>

  {/* Cost Breakdown */}
  <div style={{ marginTop: 20 }}>
    <p>FOB Value (Line Items): {selectedPI?.currency_display?.code} {formatMoney(fobTotal)}</p>
    {/* ... */}
    <p><strong>Invoice Total: {selectedPI?.currency_display?.code} {formatMoney(invoiceTotal)}</strong></p>
  </div>
</div>
```

### 4. CI Detail Page (`CommercialInvoiceDetailPage.tsx`)

**Show currency from linked PI:**
```tsx
{/* Header Section */}
<div style={CARD}>
  <div style={GRID2}>
    <div>
      <label style={LABEL}>Currency</label>
      <p>{ci.currency_display?.code} - {ci.currency_display?.name}</p>
    </div>
    {/* ... */}
  </div>
</div>

{/* Line Items Table */}
<thead>
  <tr>
    <th>Item Code</th>
    <th>Description</th>
    <th>Qty</th>
    <th>Rate ({ci.currency_display?.code})</th>
    <th>Amount ({ci.currency_display?.code})</th>
  </tr>
</thead>
```

### 5. API Client Updates

**Fetch currencies list:**
```typescript
// src/api/currencies.ts already exists - no changes needed
export const listCurrencies = async (): Promise<Currency[]> => {
  const response = await axiosInstance.get('/api/v1/currencies/');
  return response.data;
};
```

**Update PI creation payload:**
```typescript
// src/api/proformaInvoices.ts
export interface CreateProformaInvoicePayload {
  exporter: number;
  consignee: number;
  currency: number;  // NEW: Required field
  // ... other fields
}
```

---

## Testing Requirements

### Backend Tests

**Model tests:**
- ✅ ProformaInvoice requires currency field
- ✅ Cannot delete Currency if PIs reference it (PROTECT constraint)
- ✅ LineItem.save() recalculates `amount` from `quantity * rate`
- ✅ Field names are `rate` and `amount` (not `rate_usd`/`amount_usd`)

**Serializer tests:**
- ✅ Currency is required on PI create (validation error if missing)
- ✅ Currency cannot be changed once PI has line items
- ✅ CI serializer returns `currency_display` from linked PI
- ✅ Field names in API responses are `rate` and `amount`

**PDF tests:**
- ✅ PI PDF shows correct currency code in table headers
- ✅ PI PDF shows currency code in totals section
- ✅ PI PDF shows currency in "Amount in Words"
- ✅ CI PDF inherits currency code from linked PI
- ✅ CI PDF shows correct currency code throughout

**Migration tests:**
- ✅ Migration sets all existing PIs to USD
- ✅ Migration copies `rate_usd` → `rate` correctly
- ✅ Migration copies `amount_usd` → `amount` correctly
- ✅ No data loss after running all 3 migrations

### Frontend Tests

**PI Detail Page:**
- ✅ Currency dropdown appears when PI has no line items
- ✅ Currency dropdown is locked after first line item added
- ✅ "Add Line Item" button disabled until currency selected
- ✅ Table headers show dynamic currency code
- ✅ Amounts display with currency code prefix

**Packing List Creation (Step 4):**
- ✅ Currency displays as read-only from selected PI
- ✅ Final Rates table headers show PI currency code
- ✅ Amounts display with currency code prefix

**CI Detail Page:**
- ✅ Currency displays from linked PI
- ✅ Table headers show currency code
- ✅ Amounts display with currency code prefix

---

## Implementation Checklist

### Phase 1: Backend Core
- [ ] Create migration 1: Add `currency` field + renamed fields (nullable)
- [ ] Create migration 2: Data migration (set existing records to USD, copy rate_usd → rate)
- [ ] Create migration 3: Make `currency` NOT NULL, drop old `*_usd` fields
- [ ] Update ProformaInvoice model: add `currency` field
- [ ] Update ProformaInvoiceLineItem model: rename `rate_usd` → `rate`, `amount_usd` → `amount`
- [ ] Update ProformaInvoiceCharge model: rename `amount_usd` → `amount`
- [ ] Update CommercialInvoiceLineItem model: rename `rate_usd` → `rate`, `amount_usd` → `amount`
- [ ] Run migrations and verify data integrity

### Phase 2: Serializers & API
- [ ] Update ProformaInvoiceSerializer: add `currency` and `currency_display` fields
- [ ] Update ProformaInvoiceLineItemSerializer: rename fields
- [ ] Update ProformaInvoiceChargeSerializer: rename fields
- [ ] Update CommercialInvoiceSerializer: add `currency_display` (read-only from PI)
- [ ] Update CommercialInvoiceLineItemSerializer: rename fields
- [ ] Add validation: currency required on PI create
- [ ] Add validation: currency cannot be changed once PI has line items
- [ ] Test all API endpoints

### Phase 3: PDF Generation
- [ ] Update `pdf/proforma_invoice.py`: use `invoice.currency.code` (no fallback)
- [ ] Update PI PDF table headers to show dynamic currency
- [ ] Update PI PDF totals section to show currency code
- [ ] Update PI PDF "Amount in Words" to use actual currency
- [ ] Update `pdf/commercial_invoice_generator.py`: get currency from `pi.currency.code`
- [ ] Update CI PDF table headers to show dynamic currency
- [ ] Update CI PDF cost breakdown to show currency code
- [ ] Update CI PDF "Amount in Words" to use actual currency
- [ ] Test PDF generation for multiple currencies

### Phase 4: Frontend - PI Pages
- [ ] Update `ProformaInvoiceDetailPage.tsx`: add currency selector above line items
- [ ] Block "Add Line Item" until currency selected
- [ ] Lock currency selector after first line item added
- [ ] Update line items table headers to show dynamic currency
- [ ] Display amounts with currency code prefix
- [ ] Update `ProformaInvoiceListPage.tsx`: show currency code in totals column
- [ ] Add currency query to fetch active currencies list

### Phase 5: Frontend - Packing List + CI
- [ ] Update `PackingListCreatePage.tsx` Step 4: show read-only currency from PI
- [ ] Update Final Rates table headers to show PI currency
- [ ] Display amounts with currency code prefix in Final Rates
- [ ] Update `CommercialInvoiceDetailPage.tsx`: show currency from linked PI
- [ ] Update CI line items table headers to show dynamic currency
- [ ] Display amounts with currency code prefix

### Phase 6: Testing
- [ ] Write backend model tests
- [ ] Write serializer tests
- [ ] Write PDF generation tests
- [ ] Manual QA: Create new PI with non-USD currency
- [ ] Manual QA: Verify old PIs still show USD correctly
- [ ] Manual QA: Create PL+CI from multi-currency PI
- [ ] Manual QA: Download PDFs and verify currency displays correctly
- [ ] Run full test suite (`pytest`)

---

## Edge Cases & Validations

### Backend Validations

1. **Currency is required** - PI create fails if currency is null/missing
2. **Currency immutable after line items** - PI update fails if trying to change currency when line items exist
3. **Currency must be active** - Only active currencies selectable (filter in serializer queryset)
4. **Decimal precision preserved** - All monetary fields remain `DecimalField(15,2)`

### Frontend Validations

1. **Currency selection gated** - Cannot add line items until currency selected
2. **Currency locked** - Cannot change currency after first line item added
3. **Display formatting** - Show currency code consistently across all pages
4. **Null handling** - Gracefully handle missing `currency_display` (shouldn't happen, but defensive coding)

### Migration Safety

1. **Idempotent** - Migrations can be run multiple times safely
2. **Atomic** - Wrapped in `transaction.atomic()` blocks
3. **Tested on backup** - Run on copy of production DB before deploying
4. **Reversible** - Backward migration copies data back to old fields if needed

---

## Deployment Notes

### Pre-Deployment

1. **Backup database** - Full backup before running migrations
2. **Test migrations on staging** - Verify data integrity on copy of production data
3. **Ensure USD currency exists** - Migration will create it, but verify manually

### Deployment Steps

1. Deploy backend code with migrations
2. Run migrations: `python manage.py migrate`
3. Verify migration success: check PI/CI records have currency set
4. Deploy frontend code
5. Clear browser cache (if needed)
6. Smoke test: create new PI with non-USD currency

### Rollback Plan

If issues arise:
1. Revert frontend deployment
2. Revert backend deployment
3. Run backward migrations to restore `*_usd` fields
4. Restore database from backup (last resort)

---

## Success Criteria

- ✅ All existing PI/CI records migrated to USD with zero data loss
- ✅ Users can select any active currency when creating new PI
- ✅ Currency selection is mandatory (no default, no bypassing)
- ✅ Currency cannot be changed after adding line items
- ✅ CI inherits currency from linked PI automatically
- ✅ PDFs display correct currency code in all locations
- ✅ All monetary amounts show currency code prefix in frontend
- ✅ All tests pass (backend + frontend)
- ✅ No breaking changes to existing API contracts (field names changed but types/structure same)
