// Purchase Order create / edit form — FR-PO-15.
// Handles both /purchase-orders/new (create) and /purchase-orders/:id/edit (edit).
// Four sections: Header, Line Items, Terms & Conditions, Remarks + Actions.

import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Select, DatePicker, message, Modal } from "antd";
import { ArrowLeft, Plus, Trash2, AlertTriangle } from "lucide-react";
import dayjs from "dayjs";

import {
  createPurchaseOrder,
  updatePurchaseOrder,
  getPurchaseOrder,
  createLineItem,
  updateLineItem,
  deleteLineItem,
  workflowPurchaseOrder,
} from "../../api/purchaseOrders";
import type { PurchaseOrderLineItem } from "../../api/purchaseOrders";
import { listOrganisations, getOrganisation } from "../../api/organisations";
import type { OrgAddress } from "../../api/organisations";
import { listCurrencies } from "../../api/currencies";
import { listBanks } from "../../api/banks";
import { listPaymentTerms, listUOMs } from "../../api/referenceData";
import { listCountries } from "../../api/countries";
import { listTCTemplates, getTCTemplate } from "../../api/tcTemplates";
import { listUsers } from "../../api/users";
import { TRANSACTION_TYPES, TRANSACTION_TYPE_LABELS } from "../../utils/constants";
import { extractApiError } from "../../utils/apiErrors";

// ---- Styles -----------------------------------------------------------------

const CARD: React.CSSProperties = {
  background: "var(--bg-surface)",
  borderRadius: 14,
  border: "1px solid var(--border-light)",
  boxShadow: "var(--shadow-card)",
  padding: "24px 28px",
  marginBottom: 20,
};

const SECTION_TITLE: React.CSSProperties = {
  fontFamily: "var(--font-heading)",
  fontSize: 16,
  fontWeight: 600,
  color: "var(--text-primary)",
  marginBottom: 20,
};

const LABEL: React.CSSProperties = {
  display: "block",
  fontFamily: "var(--font-body)",
  fontSize: 12,
  fontWeight: 500,
  color: "var(--text-muted)",
  marginBottom: 6,
};

const INPUT: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-input)",
  border: "1px solid var(--border-medium)",
  borderRadius: 8,
  padding: "9px 14px",
  fontFamily: "var(--font-body)",
  fontSize: 14,
  color: "var(--text-primary)",
  outline: "none",
  boxSizing: "border-box",
};

const GRID2: React.CSSProperties = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 };
const GRID3: React.CSSProperties = { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 };
const GRID4: React.CSSProperties = { display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16 };

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null;
  return <p style={{ color: "#e53e3e", fontFamily: "var(--font-body)", fontSize: 12, marginTop: 4 }}>{msg}</p>;
}

// ---- Zod schema for header --------------------------------------------------

const schema = z.object({
  po_date: z.string().min(1, "PO Date is required"),
  customer_no: z.string().optional().default(""),
  vendor: z.number({ required_error: "Vendor is required" }),
  buyer: z.number().nullable().optional(),
  internal_contact: z.number({ required_error: "Internal Contact is required" }),
  delivery_address: z.number({ required_error: "Delivery Address is required" }),
  bank: z.number().nullable().optional(),
  currency: z.number({ required_error: "Currency is required" }),
  payment_terms: z.number().nullable().optional(),
  country_of_origin: z.number().nullable().optional(),
  transaction_type: z.string().min(1, "Transaction Type is required"),
  time_of_delivery: z.string().optional().default(""),
  tc_template: z.number().nullable().optional(),
  tc_content: z.string().optional().default(""),
  line_item_remarks: z.string().optional().default(""),
  remarks: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

// ---- Line item row type (client-side, with computed fields) -----------------

type ItemRow = {
  _key: string;          // unique client-side key
  id?: number;           // set for existing items
  _deleted: boolean;

  description: string;
  item_code: string;
  hsn_code: string;
  manufacturer: string;
  uom: number | null;
  quantity: string;
  packaging_description: string;
  unit_price: string;
  igst_percent: string;
  cgst_percent: string;
  sgst_percent: string;
  sort_order: number;
};

let _keyCounter = 0;
function newKey() { return `row-${++_keyCounter}`; }

function blankRow(sort_order: number): ItemRow {
  return {
    _key: newKey(),
    _deleted: false,
    description: "",
    item_code: "",
    hsn_code: "",
    manufacturer: "",
    uom: null,
    quantity: "",
    packaging_description: "",
    unit_price: "",
    igst_percent: "",
    cgst_percent: "",
    sgst_percent: "",
    sort_order,
  };
}

function rowFromExisting(item: PurchaseOrderLineItem, sort_order: number): ItemRow {
  return {
    _key: newKey(),
    id: item.id,
    _deleted: false,
    description: item.description,
    item_code: item.item_code,
    hsn_code: item.hsn_code,
    manufacturer: item.manufacturer,
    uom: item.uom,
    quantity: item.quantity,
    packaging_description: item.packaging_description,
    unit_price: item.unit_price,
    igst_percent: item.igst_percent ?? "",
    cgst_percent: item.cgst_percent ?? "",
    sgst_percent: item.sgst_percent ?? "",
    sort_order,
  };
}

// Compute derived tax values for display — mirrors backend logic
function computeRow(row: ItemRow, txType: string) {
  const qty = parseFloat(row.quantity) || 0;
  const price = parseFloat(row.unit_price) || 0;
  const taxable = qty * price;

  if (txType === TRANSACTION_TYPES.IGST) {
    const pct = parseFloat(row.igst_percent) || 0;
    const amt = taxable * pct / 100;
    return { taxable, igst_amount: amt, cgst_amount: 0, sgst_amount: 0, total_tax: amt, total: taxable + amt };
  } else if (txType === TRANSACTION_TYPES.CGST_SGST) {
    const cpct = parseFloat(row.cgst_percent) || 0;
    const spct = parseFloat(row.sgst_percent) || 0;
    const camt = taxable * cpct / 100;
    const samt = taxable * spct / 100;
    return { taxable, igst_amount: 0, cgst_amount: camt, sgst_amount: samt, total_tax: camt + samt, total: taxable + camt + samt };
  } else {
    return { taxable, igst_amount: 0, cgst_amount: 0, sgst_amount: 0, total_tax: 0, total: taxable };
  }
}

function fmt2(n: number): string {
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatAddress(addr: OrgAddress): string {
  const parts = [addr.line1, addr.city, addr.state, addr.country_name].filter(Boolean);
  return parts.join(", ");
}

// ---- Page -------------------------------------------------------------------

export default function PurchaseOrderFormPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const queryClient = useQueryClient();

  // ---- Line items state
  const [items, setItems] = useState<ItemRow[]>([blankRow(0)]);

  // ---- Template selection state
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);

  // ---- Delivery addresses (loaded after vendor is selected)
  const [deliveryAddresses, setDeliveryAddresses] = useState<OrgAddress[]>([]);
  const [deliveryLoading, setDeliveryLoading] = useState(false);

  // ---- Contact phone display
  const [contactPhone, setContactPhone] = useState("");

  // ---- Header form
  const {
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      po_date: dayjs().format("YYYY-MM-DD"),
      transaction_type: TRANSACTION_TYPES.ZERO_RATED,
    },
  });

  const watchedVendor = watch("vendor");
  const watchedBuyer = watch("buyer");
  const watchedContact = watch("internal_contact");
  const watchedTxType = watch("transaction_type");

  // ---- Master data queries
  const { data: vendors = [] } = useQuery({
    queryKey: ["organisations", "VENDOR"],
    queryFn: () => listOrganisations("VENDOR"),
  });
  const { data: buyers = [] } = useQuery({
    queryKey: ["organisations", "BUYER"],
    queryFn: () => listOrganisations("BUYER"),
  });
  const { data: currencies = [] } = useQuery({
    queryKey: ["currencies"],
    queryFn: listCurrencies,
  });
  const { data: banks = [] } = useQuery({
    queryKey: ["banks"],
    queryFn: listBanks,
  });
  const { data: paymentTerms = [] } = useQuery({
    queryKey: ["payment-terms"],
    queryFn: listPaymentTerms,
  });
  const { data: countries = [] } = useQuery({
    queryKey: ["countries"],
    queryFn: listCountries,
  });
  const { data: uoms = [] } = useQuery({
    queryKey: ["uoms"],
    queryFn: listUOMs,
  });
  const { data: tcTemplates = [] } = useQuery({
    queryKey: ["tc-templates"],
    queryFn: listTCTemplates,
  });
  const { data: users = [] } = useQuery({
    queryKey: ["users"],
    queryFn: listUsers,
  });

  // ---- Load existing PO in edit mode
  const { data: existingPO } = useQuery({
    queryKey: ["purchase-orders", Number(id)],
    queryFn: () => getPurchaseOrder(Number(id)),
    enabled: isEdit,
  });

  // When existing PO loads, populate form and items
  useEffect(() => {
    if (!existingPO) return;
    reset({
      po_date: existingPO.po_date,
      customer_no: existingPO.customer_no,
      vendor: existingPO.vendor,
      buyer: existingPO.buyer,
      internal_contact: existingPO.internal_contact,
      delivery_address: existingPO.delivery_address,
      bank: existingPO.bank,
      currency: existingPO.currency,
      payment_terms: existingPO.payment_terms,
      country_of_origin: existingPO.country_of_origin,
      transaction_type: existingPO.transaction_type,
      time_of_delivery: existingPO.time_of_delivery,
      tc_template: existingPO.tc_template,
      tc_content: existingPO.tc_content,
      line_item_remarks: existingPO.line_item_remarks,
      remarks: existingPO.remarks,
    });
    if (existingPO.tc_template) setSelectedTemplateId(existingPO.tc_template);
    if (existingPO.line_items?.length) {
      setItems(existingPO.line_items.map((item, i) => rowFromExisting(item, i)));
    }
  }, [existingPO, reset]);

  // ---- Reload delivery addresses when buyer or vendor changes
  // When a buyer is selected, delivery addresses come from the buyer.
  // When no buyer is selected, they come from the vendor.
  useEffect(() => {
    const sourceOrgId = watchedBuyer ?? watchedVendor;
    if (!sourceOrgId) {
      setDeliveryAddresses([]);
      setValue("delivery_address", undefined as any);
      return;
    }
    setDeliveryLoading(true);
    getOrganisation(sourceOrgId)
      .then((org) => {
        const deliveries = (org.addresses ?? []).filter((a) => a.address_type === "DELIVERY");
        setDeliveryAddresses(deliveries);
        // Auto-select if exactly one delivery address
        if (deliveries.length === 1 && deliveries[0].id) {
          setValue("delivery_address", deliveries[0].id);
        } else {
          setValue("delivery_address", undefined as any);
        }
      })
      .catch(() => setDeliveryAddresses([]))
      .finally(() => setDeliveryLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchedBuyer, watchedVendor]);

  // ---- Update contact phone display when contact changes
  useEffect(() => {
    if (!watchedContact) { setContactPhone(""); return; }
    const u = users.find((u) => u.id === watchedContact);
    if (u?.phone_country_code && u?.phone_number) {
      setContactPhone(`${u.phone_country_code} ${u.phone_number}`);
    } else {
      setContactPhone("");
    }
  }, [watchedContact, users]);

  // ---- Auto-populate TC content when template is selected
  const { data: selectedTemplate } = useQuery({
    queryKey: ["tc-templates", selectedTemplateId],
    queryFn: () => getTCTemplate(selectedTemplateId!),
    enabled: selectedTemplateId !== null,
  });
  useEffect(() => {
    if (selectedTemplate) setValue("tc_content", selectedTemplate.body);
  }, [selectedTemplate, setValue]);

  // ---- Transaction type change with confirmation
  function handleTxTypeChange(newType: string) {
    const hasFilledTax = items.some(
      (r) => !r._deleted && (r.igst_percent || r.cgst_percent || r.sgst_percent)
    );
    if (hasFilledTax) {
      Modal.confirm({
        title: "Change Transaction Type?",
        content: "Changing the transaction type will clear all tax values on existing line items. Continue?",
        okText: "Yes, change",
        cancelText: "Cancel",
        onOk: () => {
          setValue("transaction_type", newType);
          setItems((prev) =>
            prev.map((r) => ({ ...r, igst_percent: "", cgst_percent: "", sgst_percent: "" }))
          );
        },
      });
    } else {
      setValue("transaction_type", newType);
      setItems((prev) =>
        prev.map((r) => ({ ...r, igst_percent: "", cgst_percent: "", sgst_percent: "" }))
      );
    }
  }

  // ---- Line item helpers
  function addItem() {
    setItems((prev) => [...prev, blankRow(prev.filter((r) => !r._deleted).length)]);
  }

  function removeItem(key: string) {
    setItems((prev) =>
      prev.map((r) => (r._key === key ? { ...r, _deleted: true } : r))
    );
  }

  function updateItem<K extends keyof ItemRow>(key: string, field: K, value: ItemRow[K]) {
    setItems((prev) => prev.map((r) => (r._key === key ? { ...r, [field]: value } : r)));
  }

  const activeItems = items.filter((r) => !r._deleted);
  const grandTotal = activeItems.reduce((sum, row) => {
    return sum + computeRow(row, watchedTxType).total;
  }, 0);

  // ---- Save: persist header + line items, then optionally submit
  const [isSaving, setIsSaving] = useState(false);

  async function doSave(values: FormValues, andSubmit = false) {
    setIsSaving(true);
    try {
      const payload = {
        ...values,
        buyer: values.buyer ?? null,
        bank: values.bank ?? null,
        payment_terms: values.payment_terms ?? null,
        country_of_origin: values.country_of_origin ?? null,
        tc_template: values.tc_template ?? null,
      };

      let poId: number;

      if (isEdit) {
        const updated = await updatePurchaseOrder(Number(id), payload);
        poId = updated.id;
      } else {
        const created = await createPurchaseOrder(payload);
        poId = created.id;
      }

      // Sync line items
      const deletedIds = items.filter((r) => r._deleted && r.id).map((r) => r.id!);
      await Promise.all(deletedIds.map((lid) => deleteLineItem(poId, lid)));

      for (const row of items.filter((r) => !r._deleted)) {
        const itemPayload = {
          description: row.description,
          item_code: row.item_code,
          hsn_code: row.hsn_code,
          manufacturer: row.manufacturer,
          uom: row.uom!,
          quantity: row.quantity || "0",
          packaging_description: row.packaging_description,
          unit_price: row.unit_price || "0",
          igst_percent: row.igst_percent || null,
          cgst_percent: row.cgst_percent || null,
          sgst_percent: row.sgst_percent || null,
          sort_order: row.sort_order,
        };
        if (row.id) {
          await updateLineItem(poId, row.id, itemPayload);
        } else {
          await createLineItem(poId, itemPayload);
        }
      }

      if (andSubmit) {
        await workflowPurchaseOrder(poId, "SUBMIT");
        message.success("Purchase Order submitted for approval.");
      } else {
        message.success(isEdit ? "Purchase Order saved." : "Purchase Order created.");
      }

      queryClient.invalidateQueries({ queryKey: ["purchase-orders"] });
      navigate(`/purchase-orders/${poId}`);
    } catch (err: unknown) {
      message.error(extractApiError(err, "Failed to save Purchase Order."), 8);
    } finally {
      setIsSaving(false);
    }
  }

  const inEditableState =
    !existingPO || existingPO.status === "DRAFT" || existingPO.status === "REWORK";

  return (
    <div>
      {/* Back */}
      <button
        onClick={() => navigate("/purchase-orders")}
        style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          background: "transparent", border: "none", cursor: "pointer",
          fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)",
          marginBottom: 20, padding: 0,
        }}
      >
        <ArrowLeft size={15} strokeWidth={1.5} /> Back to Purchase Orders
      </button>

      <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", marginBottom: 24 }}>
        {isEdit ? `Edit ${existingPO?.po_number ?? "Purchase Order"}` : "New Purchase Order"}
      </h1>

      <form onSubmit={handleSubmit((v) => doSave(v, false))}>

        {/* ── Section 1: Header ──────────────────────────────────────────── */}
        <div style={CARD}>
          <h2 style={SECTION_TITLE}>Purchase Order Header</h2>

          {/* Row 1: PO Number | PO Date | Transaction Type | Time of Delivery */}
          <div style={{ ...GRID4, marginBottom: 16 }}>
            <div>
              <label style={LABEL}>PO Number</label>
              <div style={{ ...INPUT, background: "var(--bg-base)", color: "var(--text-muted)", cursor: "default" }}>
                {existingPO?.po_number ?? "[Auto-generated]"}
              </div>
            </div>
            <div>
              <label style={LABEL}>PO Date <span style={{ color: "#e53e3e" }}>*</span></label>
              <Controller
                name="po_date"
                control={control}
                render={({ field }) => (
                  <DatePicker
                    value={field.value ? dayjs(field.value) : dayjs()}
                    onChange={(d) => field.onChange(d ? d.format("YYYY-MM-DD") : "")}
                    style={{ width: "100%" }}
                    disabled={!inEditableState}
                  />
                )}
              />
              <FieldError msg={errors.po_date?.message} />
            </div>
            <div>
              <label style={LABEL}>Transaction Type <span style={{ color: "#e53e3e" }}>*</span></label>
              <Controller
                name="transaction_type"
                control={control}
                render={({ field }) => (
                  <Select
                    value={field.value}
                    onChange={(val) => {
                      if (inEditableState) handleTxTypeChange(val);
                    }}
                    placeholder="Select transaction type…"
                    style={{ width: "100%" }}
                    disabled={!inEditableState}
                    options={Object.entries(TRANSACTION_TYPE_LABELS).map(([v, l]) => ({ value: v, label: l }))}
                  />
                )}
              />
              <FieldError msg={errors.transaction_type?.message} />
            </div>
            <div>
              <label style={LABEL}>Time of Delivery</label>
              <input
                {...register("time_of_delivery")}
                style={INPUT}
                placeholder="e.g. prompt / August 2025"
                disabled={!inEditableState}
              />
            </div>
          </div>

          {/* Row 2: Vendor | Buyer | Customer No | Internal Contact */}
          <div style={{ ...GRID4, marginBottom: 16 }}>
            <div>
              <label style={LABEL}>Vendor <span style={{ color: "#e53e3e" }}>*</span></label>
              <Controller
                name="vendor"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    showSearch
                    optionFilterProp="label"
                    placeholder="Select vendor…"
                    style={{ width: "100%" }}
                    disabled={!inEditableState}
                    options={vendors.map((v) => ({ value: v.id, label: v.name })).sort((a, b) => a.label.localeCompare(b.label))}
                    onChange={(val) => {
                      field.onChange(val);
                      setValue("delivery_address", undefined as any);
                    }}
                  />
                )}
              />
              <FieldError msg={errors.vendor?.message} />
            </div>
            <div>
              <label style={LABEL}>Buyer</label>
              <Controller
                name="buyer"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    showSearch
                    optionFilterProp="label"
                    placeholder="Select buyer (optional)"
                    style={{ width: "100%" }}
                    disabled={!inEditableState}
                    options={buyers.map((b) => ({ value: b.id, label: b.name })).sort((a, b) => a.label.localeCompare(b.label))}
                    onChange={(val) => {
                      field.onChange(val ?? null);
                      setValue("delivery_address", undefined as any);
                    }}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL}>Customer No.</label>
              <input
                {...register("customer_no")}
                style={INPUT}
                placeholder="Vendor's reference number"
                disabled={!inEditableState}
              />
            </div>
            <div>
              <label style={LABEL}>Internal Contact <span style={{ color: "#e53e3e" }}>*</span></label>
              <Controller
                name="internal_contact"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    showSearch
                    optionFilterProp="label"
                    placeholder="Select contact…"
                    style={{ width: "100%" }}
                    disabled={!inEditableState}
                    options={users
                      .filter((u) => u.is_active)
                      .map((u) => ({ value: u.id, label: `${u.full_name} (${u.role})` }))
                      .sort((a, b) => a.label.localeCompare(b.label))
                    }
                  />
                )}
              />
              <FieldError msg={errors.internal_contact?.message} />
              {contactPhone && (
                <p style={{ fontFamily: "var(--font-body)", fontSize: 12, color: "var(--text-muted)", marginTop: 6 }}>
                  📞 {contactPhone}
                </p>
              )}
            </div>
          </div>

          {/* Row 3: Delivery Address (full width) */}
          <div style={{ marginBottom: 16 }}>
            <label style={LABEL}>Delivery Address <span style={{ color: "#e53e3e" }}>*</span></label>
            <Controller
              name="delivery_address"
              control={control}
              render={({ field }) => (
                <Select
                  {...field}
                  loading={deliveryLoading}
                  placeholder={watchedBuyer ? "Select buyer delivery address…" : watchedVendor ? "Select delivery address…" : "Select a vendor first"}
                  style={{ width: "100%" }}
                  disabled={!inEditableState || (!watchedVendor && !watchedBuyer)}
                  options={deliveryAddresses.map((a) => ({
                    value: a.id!,
                    label: formatAddress(a),
                  }))}
                />
              )}
            />
            <FieldError msg={errors.delivery_address?.message} />
            {(watchedBuyer || watchedVendor) && !deliveryLoading && deliveryAddresses.length === 0 && (
              <p style={{ display: "flex", alignItems: "center", gap: 6, fontFamily: "var(--font-body)", fontSize: 12, color: "#d97706", marginTop: 6 }}>
                <AlertTriangle size={13} /> {watchedBuyer ? "This buyer has no delivery addresses." : "This vendor has no delivery addresses."} Add one in Organisation master.
              </p>
            )}
          </div>

          {/* Row 4: Bank | Currency | Payment Terms | Country of Origin */}
          <div style={{ ...GRID4 }}>
            <div>
              <label style={LABEL}>Bank</label>
              <Controller
                name="bank"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    showSearch
                    optionFilterProp="label"
                    placeholder="Select bank (optional)"
                    style={{ width: "100%" }}
                    disabled={!inEditableState}
                    options={banks.map((b) => ({
                      value: b.id,
                      label: `${b.bank_name} – ${b.beneficiary_name}`,
                    })).sort((a, b) => a.label.localeCompare(b.label))}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL}>Currency <span style={{ color: "#e53e3e" }}>*</span></label>
              <Controller
                name="currency"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    showSearch
                    optionFilterProp="label"
                    placeholder="Select currency…"
                    style={{ width: "100%" }}
                    disabled={!inEditableState}
                    options={currencies
                      .filter((c) => c.is_active)
                      .map((c) => ({ value: c.id, label: `${c.code} – ${c.name}` }))
                      .sort((a, b) => a.label.localeCompare(b.label))}
                  />
                )}
              />
              <FieldError msg={errors.currency?.message} />
            </div>
            <div>
              <label style={LABEL}>Payment Terms</label>
              <Controller
                name="payment_terms"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    showSearch
                    optionFilterProp="label"
                    placeholder="Select payment terms"
                    style={{ width: "100%" }}
                    disabled={!inEditableState}
                    options={paymentTerms.map((pt) => ({ value: pt.id, label: pt.name })).sort((a, b) => a.label.localeCompare(b.label))}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL}>Country of Origin</label>
              <Controller
                name="country_of_origin"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    showSearch
                    optionFilterProp="label"
                    placeholder="Select country"
                    style={{ width: "100%" }}
                    disabled={!inEditableState}
                    options={countries.map((c) => ({ value: c.id, label: c.name })).sort((a, b) => a.label.localeCompare(b.label))}
                  />
                )}
              />
            </div>
          </div>
        </div>

        {/* ── Section 2: Line Items ──────────────────────────────────────── */}
        <div style={CARD}>
          <h2 style={SECTION_TITLE}>Line Items</h2>
          <LineItemsTable
            items={activeItems}
            transactionType={watchedTxType}
            uoms={uoms}
            readonly={!inEditableState}
            onUpdateItem={updateItem}
            onRemoveItem={removeItem}
          />

          {/* Grand Total */}
          {activeItems.length > 0 && (
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 12 }}>
              <div
                style={{
                  background: "var(--bg-base)",
                  border: "1px solid var(--border-light)",
                  borderRadius: 8,
                  padding: "10px 20px",
                  display: "flex",
                  gap: 24,
                  alignItems: "center",
                }}
              >
                <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)" }}>Grand Total</span>
                <span style={{ fontFamily: "var(--font-heading)", fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>
                  {fmt2(grandTotal)}
                </span>
              </div>
            </div>
          )}

          {inEditableState && (
            <button
              type="button"
              onClick={addItem}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                background: "transparent",
                border: "1px dashed var(--border-medium)",
                borderRadius: 8,
                padding: "8px 16px",
                marginTop: 14,
                fontFamily: "var(--font-body)",
                fontSize: 13,
                color: "var(--text-secondary)",
                cursor: "pointer",
              }}
            >
              <Plus size={14} strokeWidth={2} /> Add Item
            </button>
          )}
        </div>

        {/* ── Line Item Remarks ─────────────────────────────────────────── */}
        <div style={CARD}>
          <h2 style={SECTION_TITLE}>Line Item Remarks</h2>
          <textarea
            {...register("line_item_remarks")}
            style={{ ...INPUT, resize: "vertical", minHeight: 80 }}
            placeholder="Any notes specific to the line items above…"
            disabled={!inEditableState}
          />
        </div>

        {/* ── Section 3: Terms & Conditions ─────────────────────────────── */}
        <div style={CARD}>
          <h2 style={SECTION_TITLE}>Terms &amp; Conditions</h2>
          <div style={{ marginBottom: 16 }}>
            <label style={LABEL}>T&amp;C Template</label>
            <Controller
              name="tc_template"
              control={control}
              render={({ field }) => (
                <Select
                  {...field}
                  allowClear
                  showSearch
                  optionFilterProp="label"
                  placeholder="Select template (optional)"
                  style={{ width: "100%" }}
                  disabled={!inEditableState}
                  onChange={(val) => {
                    field.onChange(val ?? null);
                    setSelectedTemplateId(val ?? null);
                    if (!val) setValue("tc_content", "");
                  }}
                  options={tcTemplates
                    .filter((t) => t.is_active)
                    .map((t) => ({ value: t.id, label: t.name }))
                    .sort((a, b) => a.label.localeCompare(b.label))}
                />
              )}
            />
          </div>
          {selectedTemplate && (
            <div
              style={{
                background: "var(--bg-base)",
                border: "1px solid var(--border-light)",
                borderRadius: 8,
                padding: "14px 16px",
                fontFamily: "var(--font-body)",
                fontSize: 13,
                color: "var(--text-secondary)",
                maxHeight: 200,
                overflowY: "auto",
              }}
              dangerouslySetInnerHTML={{ __html: selectedTemplate.body }}
            />
          )}
        </div>

        {/* ── Section 4: Remarks (Below Total) ─────────────────────────── */}
        <div style={CARD}>
          <h2 style={SECTION_TITLE}>Remarks (Below Total)</h2>
          <textarea
            {...register("remarks")}
            style={{ ...INPUT, resize: "vertical", minHeight: 100 }}
            placeholder="Any additional notes or instructions…"
            disabled={!inEditableState}
          />
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: 12, justifyContent: "flex-end", marginBottom: 32 }}>
          <button
            type="button"
            onClick={() => navigate("/purchase-orders")}
            style={{
              background: "transparent",
              color: "var(--text-secondary)",
              border: "1px solid var(--border-medium)",
              borderRadius: 8,
              padding: "9px 20px",
              fontFamily: "var(--font-body)",
              fontSize: 14,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Cancel
          </button>

          {inEditableState && (
            <>
              <button
                type="submit"
                disabled={isSaving}
                style={{
                  background: "var(--bg-surface)",
                  color: "var(--text-primary)",
                  border: "1px solid var(--border-medium)",
                  borderRadius: 8,
                  padding: "9px 20px",
                  fontFamily: "var(--font-body)",
                  fontSize: 14,
                  fontWeight: 500,
                  cursor: isSaving ? "not-allowed" : "pointer",
                  opacity: isSaving ? 0.7 : 1,
                }}
              >
                {isSaving ? "Saving…" : "Save as Draft"}
              </button>
              <button
                type="button"
                disabled={isSaving}
                onClick={handleSubmit((v) => doSave(v, true))}
                style={{
                  background: "var(--primary)",
                  color: "#fff",
                  border: "none",
                  borderRadius: 8,
                  padding: "9px 24px",
                  fontFamily: "var(--font-body)",
                  fontSize: 14,
                  fontWeight: 500,
                  cursor: isSaving ? "not-allowed" : "pointer",
                  opacity: isSaving ? 0.7 : 1,
                }}
              >
                {isSaving ? "Saving…" : "Submit for Approval"}
              </button>
            </>
          )}
        </div>
      </form>
    </div>
  );
}

// ---- Line Items Table -------------------------------------------------------

function LineItemsTable({
  items,
  transactionType,
  uoms,
  readonly,
  onUpdateItem,
  onRemoveItem,
}: {
  items: ItemRow[];
  transactionType: string;
  uoms: { id: number; name: string; abbreviation: string }[];
  readonly: boolean;
  onUpdateItem: <K extends keyof ItemRow>(key: string, field: K, value: ItemRow[K]) => void;
  onRemoveItem: (key: string) => void;
}) {
  if (items.length === 0) {
    return (
      <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: "8px 0 16px" }}>
        No line items yet. Click "Add Item" below.
      </p>
    );
  }

  const isIgst = transactionType === TRANSACTION_TYPES.IGST;
  const isCgstSgst = transactionType === TRANSACTION_TYPES.CGST_SGST;
  const isZeroRated = transactionType === TRANSACTION_TYPES.ZERO_RATED;

  return (
    <div style={{ overflowX: "auto" }}>
      {items.map((row, idx) => {
        const computed = computeRow(row, transactionType);
        return (
          <div
            key={row._key}
            style={{
              border: "1px solid var(--border-light)",
              borderRadius: 10,
              marginBottom: 12,
              overflow: "hidden",
            }}
          >
            {/* Top row: description + basic fields */}
            <div style={{ background: "var(--bg-base)", padding: "10px 14px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 600, color: "var(--text-muted)" }}>
                Item {idx + 1}
              </span>
              {!readonly && (
                <button
                  type="button"
                  onClick={() => onRemoveItem(row._key)}
                  style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 0 }}
                >
                  <Trash2 size={14} strokeWidth={1.5} />
                </button>
              )}
            </div>

            <div style={{ padding: "14px" }}>
              {/* Row 1: Description + Item Code + HSN + Manufacturer */}
              <div style={{ display: "grid", gridTemplateColumns: "3fr 1fr 1fr 1fr", gap: 10, marginBottom: 10 }}>
                <div>
                  <label style={LABEL}>Description <span style={{ color: "#e53e3e" }}>*</span></label>
                  <input
                    value={row.description}
                    onChange={(e) => onUpdateItem(row._key, "description", e.target.value)}
                    style={INPUT}
                    placeholder="Product / goods description"
                    disabled={readonly}
                  />
                </div>
                <div>
                  <label style={LABEL}>Item Code</label>
                  <input
                    value={row.item_code}
                    onChange={(e) => onUpdateItem(row._key, "item_code", e.target.value)}
                    style={INPUT}
                    placeholder="e.g. 3004"
                    disabled={readonly}
                  />
                </div>
                <div>
                  <label style={LABEL}>NCM / HSN</label>
                  <input
                    value={row.hsn_code}
                    onChange={(e) => onUpdateItem(row._key, "hsn_code", e.target.value)}
                    style={INPUT}
                    placeholder="e.g. 2815.11"
                    disabled={readonly}
                  />
                </div>
                <div>
                  <label style={LABEL}>Manufacturer</label>
                  <input
                    value={row.manufacturer}
                    onChange={(e) => onUpdateItem(row._key, "manufacturer", e.target.value)}
                    style={INPUT}
                    placeholder="Manufacturer name"
                    disabled={readonly}
                  />
                </div>
              </div>

              {/* Row 2: UOM + Quantity + Packaging + Unit Price */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 2fr 1fr", gap: 10, marginBottom: 10 }}>
                <div>
                  <label style={LABEL}>UOM <span style={{ color: "#e53e3e" }}>*</span></label>
                  <Select
                    value={row.uom ?? undefined}
                    onChange={(val) => onUpdateItem(row._key, "uom", val)}
                    placeholder="UOM"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    disabled={readonly}
                    options={uoms.map((u) => ({ value: u.id, label: `${u.name} (${u.abbreviation})` }))}
                  />
                </div>
                <div>
                  <label style={LABEL}>Quantity</label>
                  <input
                    type="number"
                    step="any"
                    value={row.quantity}
                    onChange={(e) => onUpdateItem(row._key, "quantity", e.target.value)}
                    style={INPUT}
                    placeholder="0"
                    disabled={readonly}
                  />
                </div>
                <div>
                  <label style={LABEL}>Packaging Description</label>
                  <input
                    value={row.packaging_description}
                    onChange={(e) => onUpdateItem(row._key, "packaging_description", e.target.value)}
                    style={INPUT}
                    placeholder="e.g. 4,320 25kg bags without pallets"
                    disabled={readonly}
                  />
                </div>
                <div>
                  <label style={LABEL}>Unit Price</label>
                  <input
                    type="number"
                    step="0.01"
                    value={row.unit_price}
                    onChange={(e) => onUpdateItem(row._key, "unit_price", e.target.value)}
                    style={INPUT}
                    placeholder="0.00"
                    disabled={readonly}
                  />
                </div>
              </div>

              {/* Row 3: Computed amounts + tax inputs */}
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
                {/* Taxable Amount */}
                <div style={{ minWidth: 120 }}>
                  <label style={LABEL}>Taxable Amt</label>
                  <div style={{ ...INPUT, background: "var(--bg-base)", color: "var(--text-primary)", fontWeight: 600 }}>
                    {fmt2(computed.taxable)}
                  </div>
                </div>

                {/* IGST fields */}
                {isIgst && (
                  <>
                    <div style={{ minWidth: 90 }}>
                      <label style={LABEL}>IGST %</label>
                      <input
                        type="number"
                        step="0.01"
                        value={row.igst_percent}
                        onChange={(e) => onUpdateItem(row._key, "igst_percent", e.target.value)}
                        style={INPUT}
                        placeholder="0.00"
                        disabled={readonly}
                      />
                    </div>
                    <div style={{ minWidth: 120 }}>
                      <label style={LABEL}>IGST Amt</label>
                      <div style={{ ...INPUT, background: "var(--bg-base)", color: "var(--text-secondary)" }}>
                        {fmt2(computed.igst_amount)}
                      </div>
                    </div>
                  </>
                )}

                {/* CGST + SGST fields */}
                {isCgstSgst && (
                  <>
                    <div style={{ minWidth: 90 }}>
                      <label style={LABEL}>CGST %</label>
                      <input
                        type="number"
                        step="0.01"
                        value={row.cgst_percent}
                        onChange={(e) => onUpdateItem(row._key, "cgst_percent", e.target.value)}
                        style={INPUT}
                        placeholder="0.00"
                        disabled={readonly}
                      />
                    </div>
                    <div style={{ minWidth: 120 }}>
                      <label style={LABEL}>CGST Amt</label>
                      <div style={{ ...INPUT, background: "var(--bg-base)", color: "var(--text-secondary)" }}>
                        {fmt2(computed.cgst_amount)}
                      </div>
                    </div>
                    <div style={{ minWidth: 90 }}>
                      <label style={LABEL}>SGST %</label>
                      <input
                        type="number"
                        step="0.01"
                        value={row.sgst_percent}
                        onChange={(e) => onUpdateItem(row._key, "sgst_percent", e.target.value)}
                        style={INPUT}
                        placeholder="0.00"
                        disabled={readonly}
                      />
                    </div>
                    <div style={{ minWidth: 120 }}>
                      <label style={LABEL}>SGST Amt</label>
                      <div style={{ ...INPUT, background: "var(--bg-base)", color: "var(--text-secondary)" }}>
                        {fmt2(computed.sgst_amount)}
                      </div>
                    </div>
                  </>
                )}

                {/* Total Tax */}
                {!isZeroRated && (
                  <div style={{ minWidth: 120 }}>
                    <label style={LABEL}>Total Tax</label>
                    <div style={{ ...INPUT, background: "var(--bg-base)", color: "var(--text-secondary)" }}>
                      {fmt2(computed.total_tax)}
                    </div>
                  </div>
                )}

                {/* Line Total */}
                <div style={{ minWidth: 130 }}>
                  <label style={LABEL}>Line Total</label>
                  <div style={{ ...INPUT, background: "var(--bg-base)", color: "var(--text-primary)", fontWeight: 700 }}>
                    {fmt2(computed.total)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
