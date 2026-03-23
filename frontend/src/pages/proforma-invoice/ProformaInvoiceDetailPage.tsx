// Proforma Invoice detail page — FR-09.5 (line items), FR-09.7 (cost breakdown), FR-08 (workflow).
// Shows header, editable line items + charges (in DRAFT/REWORK), cost breakdown, workflow buttons, PDF download.

import { useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { message, Modal, Tooltip } from "antd";
import AuditLogDrawer from "../../components/AuditLogDrawer";
import { ArrowLeft, Download, FileText, Plus, Trash2, Edit2, Clock, Upload, Paperclip } from "lucide-react";

import {
  getProformaInvoice,
  updateProformaInvoice,
  createLineItem,
  updateLineItem,
  deleteLineItem,
  createCharge,
  updateCharge,
  deleteCharge,
  triggerWorkflowAction,
  downloadPiPdf,
  getAuditLog,
  uploadSignedCopy,
  hardDeleteProformaInvoice,
} from "../../api/proformaInvoices";
import { listUOMs, listIncoterms, listPaymentTerms } from "../../api/referenceData";
import type { UOM, Incoterm, PaymentTerm } from "../../api/referenceData";
import type { ProformaInvoiceLineItem, ProformaInvoiceCharge, AuditLogEntry } from "../../api/proformaInvoices";
import WorkflowActionButton from "../../components/common/WorkflowActionButton";
import { useAuth } from "../../store/AuthContext";
import {
  DOCUMENT_STATUS,
  DOCUMENT_STATUS_CHIP,
  DOCUMENT_STATUS_LABELS,
  INCOTERM_SELLER_FIELDS,
  COST_FIELD_LABELS,
  ROLES,
} from "../../utils/constants";
import { extractApiError } from "../../utils/apiErrors";

// ---- Styles ----------------------------------------------------------------

const CARD: React.CSSProperties = {
  background: "var(--bg-surface)",
  borderRadius: 14,
  border: "1px solid var(--border-light)",
  boxShadow: "var(--shadow-card)",
  padding: "20px 24px",
  marginBottom: 20,
};

const SECTION_TITLE: React.CSSProperties = {
  fontFamily: "var(--font-heading)",
  fontSize: 15,
  fontWeight: 600,
  color: "var(--text-primary)",
  marginBottom: 16,
};

const LABEL: React.CSSProperties = {
  fontFamily: "var(--font-body)",
  fontSize: 11,
  fontWeight: 500,
  color: "var(--text-muted)",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  marginBottom: 4,
  display: "block",
};

const VALUE: React.CSSProperties = {
  fontFamily: "var(--font-body)",
  fontSize: 14,
  color: "var(--text-primary)",
};

const TD: React.CSSProperties = {
  padding: "12px 14px",
  borderBottom: "1px solid var(--border-light)",
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-secondary)",
};

const INPUT: React.CSSProperties = {
  background: "var(--bg-input)",
  border: "1px solid var(--border-medium)",
  borderRadius: 6,
  padding: "6px 10px",
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-primary)",
  outline: "none",
  width: "100%",
};

// ---- Helpers ---------------------------------------------------------------

function LabelValue({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <span style={LABEL}>{label}</span>
      <span style={VALUE}>{value || "—"}</span>
    </div>
  );
}

function formatMoney(v: string | null | undefined) {
  if (!v) return "$0";
  const n = parseFloat(v);
  // Strip trailing zeros: $12.00 → $12, $12.50 → $12.5, $12.55 → $12.55
  return `$${n.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

// ---- Line item form (inline) -----------------------------------------------

interface LineItemFormData {
  description: string;
  quantity: string;
  rate_usd: string;
  hsn_code: string;
  item_code: string;
  uom: string;
}

const EMPTY_LINE_ITEM: LineItemFormData = {
  description: "", quantity: "", rate_usd: "",
  hsn_code: "", item_code: "", uom: "",
};

// ---- Main page -------------------------------------------------------------

export default function ProformaInvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const piId = parseInt(id!, 10);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const [auditDrawerOpen, setAuditDrawerOpen] = useState(false);
  const [addingLineItem, setAddingLineItem] = useState(false);
  const [editingLineItem, setEditingLineItem] = useState<ProformaInvoiceLineItem | null>(null);
  const [lineItemForm, setLineItemForm] = useState<LineItemFormData>(EMPTY_LINE_ITEM);
  const [addingCharge, setAddingCharge] = useState(false);
  const [chargeForm, setChargeForm] = useState({ description: "", amount_usd: "" });

  // Cost breakdown fields for Incoterm (FR-09.7)
  const [costFields, setCostFields] = useState<Record<string, string>>({
    freight: "", insurance_amount: "", import_duty: "", destination_charges: "",
  });
  // Debounce timer ref — cost fields save 600ms after the user stops typing
  const costSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { data: pi, isLoading } = useQuery({
    queryKey: ["proforma-invoice", piId],
    queryFn: () => getProformaInvoice(piId),
  });

  const { data: auditLogs = [] } = useQuery({
    queryKey: ["proforma-invoice", piId, "audit-log"],
    queryFn: () => getAuditLog(piId),
    enabled: auditDrawerOpen,
  });

  const { data: uoms = [] } = useQuery<UOM[]>({
    queryKey: ["uoms"],
    queryFn: listUOMs,
  });

  const { data: incoterms = [] } = useQuery<Incoterm[]>({
    queryKey: ["incoterms"],
    queryFn: listIncoterms,
  });

  const { data: paymentTerms = [] } = useQuery<PaymentTerm[]>({
    queryKey: ["payment-terms"],
    queryFn: listPaymentTerms,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["proforma-invoice", piId] });
    queryClient.invalidateQueries({ queryKey: ["proforma-invoices"] });
  };

  // ---- Mutations -----------------------------------------------------------

  const addLineItemMutation = useMutation({
    mutationFn: (data: any) => createLineItem(piId, data),
    onSuccess: () => { invalidate(); setAddingLineItem(false); setLineItemForm(EMPTY_LINE_ITEM); },
    onError: (err: unknown) => message.error(extractApiError(err, "Failed to add line item.")),
  });

  const updateLineItemMutation = useMutation({
    mutationFn: ({ lid, data }: { lid: number; data: any }) => updateLineItem(piId, lid, data),
    onSuccess: () => { invalidate(); setEditingLineItem(null); },
    onError: (err: unknown) => message.error(extractApiError(err, "Failed to update line item.")),
  });

  const deleteLineItemMutation = useMutation({
    mutationFn: (lid: number) => deleteLineItem(piId, lid),
    onSuccess: invalidate,
    onError: (err: unknown) => message.error(extractApiError(err, "Failed to delete line item.")),
  });

  const addChargeMutation = useMutation({
    mutationFn: (data: any) => createCharge(piId, data),
    onSuccess: () => { invalidate(); setAddingCharge(false); setChargeForm({ description: "", amount_usd: "" }); },
    onError: (err: unknown) => message.error(extractApiError(err, "Failed to add charge.")),
  });

  const deleteChargeMutation = useMutation({
    mutationFn: (cid: number) => deleteCharge(piId, cid),
    onSuccess: invalidate,
    onError: (err: unknown) => message.error(extractApiError(err, "Failed to delete charge.")),
  });

  const updateCostFieldsMutation = useMutation({
    mutationFn: (data: any) => updateProformaInvoice(piId, data),
    onSuccess: () => { invalidate(); message.success("Saved."); },
    onError: (err: unknown) => message.error(extractApiError(err, "Failed to save.")),
  });

  const uploadSignedCopyMutation = useMutation({
    mutationFn: (file: File) => uploadSignedCopy(piId, file),
    onSuccess: () => { invalidate(); message.success("Signed copy uploaded."); },
    onError: (err: unknown) => message.error(extractApiError(err, "Upload failed.")),
  });

  const hardDeleteMutation = useMutation({
    mutationFn: () => hardDeleteProformaInvoice(piId),
    onSuccess: () => {
      message.success("Proforma Invoice permanently deleted.");
      navigate("/proforma-invoices");
    },
    onError: (err: unknown) => message.error(extractApiError(err, "Delete failed. Please try again.")),
  });

  function confirmHardDelete() {
    Modal.confirm({
      title: "Permanently delete this Proforma Invoice?",
      content: "This action cannot be undone. The PI and all its line items will be removed from the database.",
      okText: "Delete permanently",
      okButtonProps: { danger: true },
      cancelText: "Cancel",
      onOk: () => hardDeleteMutation.mutate(),
    });
  }

  if (isLoading || !pi) {
    return (
      <div style={{ padding: 48, textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-body)" }}>
        Loading…
      </div>
    );
  }

  const isEditable = pi.status === DOCUMENT_STATUS.DRAFT || pi.status === DOCUMENT_STATUS.REWORK;
  const isCreator = pi.created_by === user?.id;
  // Any Maker can edit any editable PI — not just the creator (FR-PO permission change).
  const canEdit = isEditable && (user?.role === ROLES.MAKER || isCreator || user?.role === ROLES.COMPANY_ADMIN || user?.role === ROLES.SUPER_ADMIN);

  const incotermsCode = pi.incoterms_code ?? "";
  const sellerFields = INCOTERM_SELLER_FIELDS[incotermsCode] ?? new Set<string>();

  // Initialise cost fields from server data
  function initCostFields() {
    setCostFields({
      freight: pi.freight ?? "",
      insurance_amount: pi.insurance_amount ?? "",
      import_duty: pi.import_duty ?? "",
      destination_charges: pi.destination_charges ?? "",
    });
  }

  // ---- Render: Line Items table -------------------------------------------

  function renderLineItems() {
    return (
      <div style={CARD}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <h2 style={SECTION_TITLE}>Line Items</h2>
          {canEdit && !addingLineItem && (
            <button
              onClick={() => { setAddingLineItem(true); setLineItemForm(EMPTY_LINE_ITEM); }}
              style={{
                display: "inline-flex", alignItems: "center", gap: 6,
                background: "var(--pastel-blue)", color: "var(--pastel-blue-text)",
                border: "none", borderRadius: 8, padding: "7px 14px",
                fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, cursor: "pointer",
              }}
            >
              <Plus size={14} strokeWidth={2} /> Add Line Item
            </button>
          )}
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700, tableLayout: "fixed" }}>
            <colgroup>
              <col style={{ width: 40 }} />   {/* # */}
              <col style={{ width: 100 }} />  {/* HSN Code */}
              <col style={{ width: 110 }} />  {/* Item Code */}
              <col />                          {/* Description — takes remaining space */}
              <col style={{ width: 115 }} />  {/* Qty */}
              <col style={{ width: 90 }} />   {/* UOM */}
              <col style={{ width: 135 }} />  {/* Rate (USD) */}
              <col style={{ width: 145 }} />  {/* Amount (USD) */}
              {canEdit && <col style={{ width: 72 }} />}  {/* Actions */}
            </colgroup>
            <thead>
              <tr style={{ background: "var(--bg-base)" }}>
                {["#", "HSN Code", "Item Code", "Description", "Qty", "UOM", "Rate (USD)", "Amount (USD)", canEdit ? "" : null]
                  .filter(Boolean)
                  .map((h) => (
                    <th key={h} style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em" }}>
                      {h}
                    </th>
                  ))}
              </tr>
            </thead>
            <tbody>
              {pi.line_items.map((item, idx) => (
                editingLineItem?.id === item.id ? (
                  <tr key={item.id} style={{ background: "var(--primary-light)" }}>
                    <td style={TD}>{idx + 1}</td>
                    {(["hsn_code", "item_code", "description", "quantity"] as const).map((f) => (
                      <td key={f} style={TD}>
                        <input
                          style={INPUT}
                          value={(lineItemForm as any)[f]}
                          onChange={(e) => setLineItemForm((prev) => ({ ...prev, [f]: e.target.value }))}
                          placeholder={f.replace(/_/g, " ")}
                        />
                      </td>
                    ))}
                    <td style={TD}>
                      <select
                        style={INPUT}
                        value={lineItemForm.uom}
                        onChange={(e) => setLineItemForm((prev) => ({ ...prev, uom: e.target.value }))}
                      >
                        <option value="">— UOM —</option>
                        {uoms.map((u) => (
                          <option key={u.id} value={String(u.id)}>{u.abbreviation}</option>
                        ))}
                      </select>
                    </td>
                    <td style={TD}>
                      <input
                        style={INPUT}
                        value={lineItemForm.rate_usd}
                        onChange={(e) => setLineItemForm((prev) => ({ ...prev, rate_usd: e.target.value }))}
                        placeholder="rate usd"
                      />
                    </td>
                    <td style={TD}>—</td>
                    <td style={TD}>
                      <button
                        onClick={() => updateLineItemMutation.mutate({
                          lid: item.id,
                          data: { ...lineItemForm, uom: lineItemForm.uom ? parseInt(lineItemForm.uom) : null },
                        })}
                        style={{ background: "var(--primary)", color: "#fff", border: "none", borderRadius: 6, padding: "5px 12px", cursor: "pointer", fontSize: 12 }}
                      >Save</button>
                      <button
                        onClick={() => setEditingLineItem(null)}
                        style={{ background: "transparent", color: "var(--text-muted)", border: "none", cursor: "pointer", fontSize: 12, marginLeft: 6 }}
                      >Cancel</button>
                    </td>
                  </tr>
                ) : (
                  <tr key={item.id}>
                    <td style={TD}>{idx + 1}</td>
                    <td style={TD}>{item.hsn_code || "—"}</td>
                    <td style={TD}>{item.item_code || "—"}</td>
                    <td style={TD}>{item.description}</td>
                    <td style={{ ...TD, textAlign: "right" }}>{parseFloat(item.quantity).toLocaleString("en-US", { maximumFractionDigits: 3 })}</td>
                    <td style={TD}>{uoms.find(u => u.id === (item.uom as any))?.abbreviation ?? "—"}</td>
                    <td style={{ ...TD, textAlign: "right" }}>{formatMoney(item.rate_usd)}</td>
                    <td style={{ ...TD, textAlign: "right", fontWeight: 600 }}>{formatMoney(item.amount_usd)}</td>
                    {canEdit && (
                      <td style={TD}>
                        <div style={{ display: "flex", gap: 4 }}>
                          <button
                            onClick={() => { setEditingLineItem(item); setLineItemForm({ description: item.description, quantity: item.quantity, rate_usd: item.rate_usd, hsn_code: item.hsn_code, item_code: item.item_code, uom: String((item.uom as any)?.id ?? item.uom ?? "") }); }}
                            style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 4 }}
                          >
                            <Edit2 size={14} strokeWidth={1.5} />
                          </button>
                          <button
                            onClick={() => Modal.confirm({ title: "Delete this line item?", onOk: () => deleteLineItemMutation.mutate(item.id) })}
                            style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--pastel-pink-text)", padding: 4 }}
                          >
                            <Trash2 size={14} strokeWidth={1.5} />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                )
              ))}

              {/* Add row */}
              {addingLineItem && (
                <tr style={{ background: "var(--primary-light)" }}>
                  <td style={TD}>—</td>
                  {(["hsn_code", "item_code", "description", "quantity"] as const).map((f) => (
                    <td key={f} style={TD}>
                      <input
                        style={INPUT}
                        value={(lineItemForm as any)[f]}
                        onChange={(e) => setLineItemForm((prev) => ({ ...prev, [f]: e.target.value }))}
                        placeholder={f.replace(/_/g, " ")}
                      />
                    </td>
                  ))}
                  <td style={TD}>
                    <select
                      style={INPUT}
                      value={lineItemForm.uom}
                      onChange={(e) => setLineItemForm((prev) => ({ ...prev, uom: e.target.value }))}
                    >
                      <option value="">— UOM —</option>
                      {uoms.map((u) => (
                        <option key={u.id} value={String(u.id)}>{u.abbreviation}</option>
                      ))}
                    </select>
                  </td>
                  <td style={TD}>
                    <input
                      style={INPUT}
                      value={lineItemForm.rate_usd}
                      onChange={(e) => setLineItemForm((prev) => ({ ...prev, rate_usd: e.target.value }))}
                      placeholder="rate usd"
                    />
                  </td>
                  <td style={TD}>—</td>
                  <td style={TD}>
                    <button
                      onClick={() => addLineItemMutation.mutate({ ...lineItemForm, uom: lineItemForm.uom ? parseInt(lineItemForm.uom) : null })}
                      style={{ background: "var(--primary)", color: "#fff", border: "none", borderRadius: 6, padding: "5px 12px", cursor: "pointer", fontSize: 12 }}
                    >Add</button>
                    <button
                      onClick={() => setAddingLineItem(false)}
                      style={{ background: "transparent", color: "var(--text-muted)", border: "none", cursor: "pointer", fontSize: 12, marginLeft: 6 }}
                    >Cancel</button>
                  </td>
                </tr>
              )}

              {/* Totals row */}
              <tr style={{ background: "var(--bg-base)" }}>
                <td colSpan={canEdit ? 7 : 6} style={{ ...TD, textAlign: "right", fontWeight: 600, fontSize: 13 }}>Item Total</td>
                <td style={{ ...TD, textAlign: "right", fontWeight: 700, fontSize: 14, color: "var(--text-primary)" }}>
                  {formatMoney(pi.line_items_total)}
                </td>
                {canEdit && <td style={TD} />}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // ---- Render: Charges table -----------------------------------------------

  function renderCharges() {
    return (
      <>
        {/* Additional charges */}
        {(pi.charges.length > 0 || addingCharge || canEdit) && (
          <div style={{ background: "var(--bg-base)", borderRadius: 8, border: "1px solid var(--border-light)", overflow: "hidden", marginBottom: 4 }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <tbody>
                {pi.charges.map((charge) => (
                  <tr key={charge.id}>
                    <td style={{ ...TD, width: "70%" }}>{charge.description}</td>
                    <td style={{ ...TD, textAlign: "right", fontWeight: 600 }}>{formatMoney(charge.amount_usd)}</td>
                    {canEdit && (
                      <td style={{ ...TD, width: 40 }}>
                        <button
                          onClick={() => Modal.confirm({ title: "Delete this charge?", onOk: () => deleteChargeMutation.mutate(charge.id) })}
                          style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--pastel-pink-text)", padding: 2 }}
                        >
                          <Trash2 size={13} strokeWidth={1.5} />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
                {addingCharge && (
                  <tr style={{ background: "var(--primary-light)" }}>
                    <td style={TD}>
                      <input style={INPUT} value={chargeForm.description} onChange={(e) => setChargeForm((p) => ({ ...p, description: e.target.value }))} placeholder="Charge description" />
                    </td>
                    <td style={TD}>
                      <input style={{ ...INPUT, textAlign: "right" }} value={chargeForm.amount_usd} onChange={(e) => setChargeForm((p) => ({ ...p, amount_usd: e.target.value }))} placeholder="0.00" />
                    </td>
                    <td style={TD}>
                      <button
                        onClick={() => addChargeMutation.mutate(chargeForm)}
                        style={{ background: "var(--primary)", color: "#fff", border: "none", borderRadius: 6, padding: "5px 10px", cursor: "pointer", fontSize: 12 }}
                      >Add</button>
                      <button onClick={() => setAddingCharge(false)} style={{ background: "transparent", border: "none", cursor: "pointer", fontSize: 12, marginLeft: 4, color: "var(--text-muted)" }}>Cancel</button>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
        {canEdit && !addingCharge && (
          <button
            onClick={() => { setAddingCharge(true); setChargeForm({ description: "", amount_usd: "" }); }}
            style={{
              display: "inline-flex", alignItems: "center", gap: 4,
              background: "transparent", border: "1px dashed var(--border-medium)",
              borderRadius: 6, padding: "5px 12px",
              fontFamily: "var(--font-body)", fontSize: 12, color: "var(--text-muted)", cursor: "pointer", marginBottom: 4,
            }}
          >
            <Plus size={12} strokeWidth={2} /> Add Charge
          </button>
        )}
      </>
    );
  }

  // ---- Render: Totals + Cost breakdown (FR-09.7) ---------------------------

  function renderTotals() {
    // Show Cost Breakdown for any incoterm except EXW (EXW has no FOB concept).
    // FCA/FOB: sellerFields is empty so only the FOB Value row is shown, no cost input rows.
    const showCostBreakdown = !!incotermsCode && incotermsCode !== "EXW";

    // Invoice Total shown for any selected incoterm (including EXW where it equals FOB Value).
    // When no incoterm is set, Grand Total Amount is shown instead.
    const showInvoiceTotal = !!incotermsCode;

    return (
      <div style={{ ...CARD }}>
        {/* Item Total + charges breakdown only when there are charges and no Cost Breakdown section (EXW or no incoterm) */}
        {pi.charges.length > 0 && !showCostBreakdown && (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>Item Total</span>
              <span style={{ fontFamily: "var(--font-heading)", fontSize: 13, fontWeight: 600 }}>{formatMoney(pi.line_items_total)}</span>
            </div>
            {pi.charges.map((c) => (
              <div key={c.id} style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>{c.description}</span>
                <span style={{ fontFamily: "var(--font-body)", fontSize: 13 }}>{formatMoney(c.amount_usd)}</span>
              </div>
            ))}
          </>
        )}

        {/* Grand Total Amount only shown when no incoterm is set; Invoice Total replaces it otherwise */}
        {!incotermsCode && (
          <div style={{ borderTop: pi.charges.length > 0 ? "1px solid var(--border-light)" : "none", paddingTop: pi.charges.length > 0 ? 8 : 0, marginTop: pi.charges.length > 0 ? 4 : 0, display: "flex", justifyContent: "space-between" }}>
            <span style={{ fontFamily: "var(--font-heading)", fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>Grand Total Amount</span>
            <span style={{ fontFamily: "var(--font-heading)", fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>{formatMoney(pi.grand_total)}</span>
          </div>
        )}

        {showCostBreakdown && (
          <div style={{ background: "var(--bg-base)", borderRadius: 8, padding: "12px 14px", marginBottom: 10 }}>
            <p style={{ fontFamily: "var(--font-body)", fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 10 }}>
              Cost Breakdown ({incotermsCode})
            </p>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>FOB Value (Item Cost+Additional Charges)</span>
              <span style={{ fontFamily: "var(--font-body)", fontSize: 13 }}>{formatMoney(pi.grand_total)}</span>
            </div>
            {Array.from(sellerFields).map((field) => (
              <div key={field} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
                  {COST_FIELD_LABELS[field]}
                  {field === "insurance_amount" && incotermsCode === "CIP" && (
                    <Tooltip title="CIP requires all-risk (Institute Cargo Clauses A) coverage.">
                      <span style={{ marginLeft: 4, color: "var(--primary)", fontSize: 11, cursor: "help" }}>ℹ</span>
                    </Tooltip>
                  )}
                </span>
                {canEdit ? (
                  <input
                    style={{ ...INPUT, width: 120, textAlign: "right" }}
                    value={costFields[field] ?? (pi as any)[field] ?? ""}
                    onChange={(e) => {
                      const val = e.target.value;
                      setCostFields((p) => ({ ...p, [field]: val }));
                      // Debounce: save 600ms after the user stops typing
                      if (costSaveTimer.current) clearTimeout(costSaveTimer.current);
                      costSaveTimer.current = setTimeout(() => {
                        updateCostFieldsMutation.mutate({ [field]: val || null });
                      }, 600);
                    }}
                    placeholder="0.00"
                  />
                ) : (
                  <span style={{ fontFamily: "var(--font-body)", fontSize: 13 }}>{formatMoney((pi as any)[field])}</span>
                )}
              </div>
            ))}
          </div>
        )}

        {showInvoiceTotal && (
          <div style={{ borderTop: "2px solid var(--border-medium)", paddingTop: 10, display: "flex", justifyContent: "space-between" }}>
            <span style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>Invoice Total (Amount Payable)</span>
            <span style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 700, color: "var(--primary)" }}>{formatMoney(pi.invoice_total)}</span>
          </div>
        )}
      </div>
    );
  }

  // ---- Render: Signed copy (FR-08.4) — visible only when Approved ----------

  function renderSignedCopy() {
    if (pi.status !== DOCUMENT_STATUS.APPROVED) return null;

    return (
      <div style={CARD}>
        <h2 style={SECTION_TITLE}>Signed Copy</h2>
        <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", marginBottom: 14 }}>
          Upload a scanned signed copy of the approved invoice (PDF, JPG, or PNG — max 3 MB).
        </p>

        {/* Show existing upload if present */}
        {pi.signed_copy_url && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8,
            background: "var(--pastel-green)", borderRadius: 8,
            padding: "10px 14px", marginBottom: 14,
          }}>
            <Paperclip size={14} strokeWidth={1.5} color="var(--pastel-green-text)" />
            <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--pastel-green-text)", flex: 1 }}>
              Signed copy uploaded
            </span>
            <a
              href={pi.signed_copy_url}
              target="_blank"
              rel="noreferrer"
              style={{ fontFamily: "var(--font-body)", fontSize: 12, color: "var(--pastel-green-text)", fontWeight: 600 }}
            >
              View / Download
            </a>
          </div>
        )}

        {/* Upload button — replaces any existing file */}
        <label style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          background: "var(--bg-input)", border: "1px dashed var(--border-medium)",
          borderRadius: 8, padding: "8px 16px",
          fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)",
          cursor: uploadSignedCopyMutation.isPending ? "not-allowed" : "pointer",
          opacity: uploadSignedCopyMutation.isPending ? 0.6 : 1,
        }}>
          <Upload size={14} strokeWidth={1.5} />
          {uploadSignedCopyMutation.isPending ? "Uploading…" : pi.signed_copy_url ? "Replace signed copy" : "Upload signed copy"}
          <input
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            style={{ display: "none" }}
            disabled={uploadSignedCopyMutation.isPending}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) uploadSignedCopyMutation.mutate(file);
              // Reset input so the same file can be re-selected if needed
              e.target.value = "";
            }}
          />
        </label>
      </div>
    );
  }

  // ---- Main render ---------------------------------------------------------

  return (
    <div>
      {/* Back */}
      <button
        onClick={() => navigate("/proforma-invoices")}
        style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          background: "transparent", border: "none", cursor: "pointer",
          fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)",
          marginBottom: 20, padding: 0,
        }}
      >
        <ArrowLeft size={15} strokeWidth={1.5} /> Back to Proforma Invoices
      </button>

      {/* Header bar — sticky so PI number and actions stay visible while scrolling */}
      <div style={{ position: "sticky", top: 0, zIndex: 10, background: "var(--bg-base)", paddingBottom: 16, marginBottom: 8, display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
              {pi.pi_number}
            </h1>
            <span className={DOCUMENT_STATUS_CHIP[pi.status] ?? "chip-blue"}>
              {DOCUMENT_STATUS_LABELS[pi.status] ?? pi.status}
            </span>
          </div>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
            Created by {pi.created_by_name} · {pi.pi_date}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          {canEdit && (
            <button
              onClick={() => navigate(`/proforma-invoices/${piId}/edit`)}
              style={{
                display: "inline-flex", alignItems: "center", gap: 6,
                background: "var(--pastel-blue)", color: "var(--pastel-blue-text)",
                border: "none", borderRadius: 8, padding: "8px 14px",
                fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, cursor: "pointer",
              }}
            >
              <Edit2 size={14} strokeWidth={1.5} /> Edit Header
            </button>
          )}
          <button
            onClick={() => setAuditDrawerOpen(true)}
            style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              background: "transparent", border: "1px solid var(--border-medium)",
              borderRadius: 8, padding: "8px 14px",
              fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)", cursor: "pointer",
            }}
          >
            <Clock size={14} strokeWidth={1.5} /> History
          </button>
          <button
            onClick={() => {
              const today = new Date();
              const dd = String(today.getDate()).padStart(2, "0");
              const mm = String(today.getMonth() + 1).padStart(2, "0");
              const yyyy = today.getFullYear();
              const dateStr = `${dd}${mm}${yyyy}`;
              const consigneeName = (pi.consignee_name ?? "").replace(/[^a-zA-Z0-9]/g, "");
              const isDraft = pi.status !== DOCUMENT_STATUS.APPROVED;
              const filename = isDraft
                ? `${dateStr}_Draft_ProformaInvoice_${consigneeName}.pdf`
                : `${dateStr}_ProformaInvoice_${consigneeName}.pdf`;
              downloadPiPdf(piId, filename).catch(() =>
                message.error("PDF download failed. Please try again.")
              );
            }}
            style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              background: "var(--pastel-green)", color: "var(--pastel-green-text)",
              border: "none", borderRadius: 8, padding: "8px 14px",
              fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, cursor: "pointer",
            }}
          >
            <Download size={14} strokeWidth={1.5} /> Download PDF
          </button>
          {user?.role === ROLES.SUPER_ADMIN && (
            <button
              onClick={confirmHardDelete}
              style={{
                display: "inline-flex", alignItems: "center", gap: 6,
                background: "var(--pastel-pink)", color: "var(--pastel-pink-text)",
                border: "none", borderRadius: 8, padding: "8px 14px",
                fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, cursor: "pointer",
              }}
            >
              <Trash2 size={14} strokeWidth={1.5} /> Delete
            </button>
          )}
          {user && (
            <WorkflowActionButton
              documentId={piId}
              documentStatus={pi.status}
              userRole={user.role}
              documentType="proforma_invoice"
              onSuccess={(newStatus) => {
                invalidate();
              }}
              onAction={(action, comment) => triggerWorkflowAction(piId, action, comment)}
            />
          )}
        </div>
      </div>

      {/* Header details */}
      <div style={CARD}>
        <h2 style={SECTION_TITLE}>Invoice Details</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
          <LabelValue label="Exporter" value={pi.exporter_name} />
          <LabelValue label="Consignee" value={pi.consignee_name} />
          <LabelValue label="Buyer" value={pi.buyer_name ?? undefined} />
          <LabelValue label="Invoice Date" value={pi.pi_date} />
          <LabelValue label="Buyer Order No" value={pi.buyer_order_no} />
          <LabelValue label="Buyer Order Date" value={pi.buyer_order_date ?? undefined} />
          <div>
            <span style={LABEL}>Incoterms</span>
            {canEdit ? (
              <select
                style={{ ...INPUT, marginTop: 4 }}
                value={pi.incoterms ?? ""}
                onChange={(e) => {
                  const id = e.target.value ? Number(e.target.value) : null;
                  updateCostFieldsMutation.mutate({ incoterms: id });
                }}
              >
                <option value="">— Select —</option>
                {incoterms.filter(i => i.is_active).map((i) => (
                  <option key={i.id} value={i.id}>{i.code} — {i.full_name}</option>
                ))}
              </select>
            ) : (
              <span style={VALUE}>{pi.incoterms_code ?? "—"}</span>
            )}
          </div>
          <div>
            <span style={LABEL}>Payment Terms</span>
            {canEdit ? (
              <select
                style={{ ...INPUT, marginTop: 4 }}
                value={pi.payment_terms ?? ""}
                onChange={(e) => {
                  const id = e.target.value ? Number(e.target.value) : null;
                  updateCostFieldsMutation.mutate({ payment_terms: id });
                }}
              >
                <option value="">— Select —</option>
                {paymentTerms.filter(p => p.is_active).map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            ) : (
              <span style={VALUE}>{pi.payment_terms_name ?? "—"}</span>
            )}
          </div>
          <LabelValue label="Port of Loading" value={pi.port_of_loading_name ?? undefined} />
          <LabelValue label="Port of Discharge" value={pi.port_of_discharge_name ?? undefined} />
          <LabelValue label="Place of Receipt" value={pi.place_of_receipt_name ?? undefined} />
          <LabelValue label="Place of Receipt by Pre-Carrier" value={pi.place_of_receipt_by_pre_carrier_name ?? undefined} />
        </div>
        {pi.other_references && (
          <div style={{ marginTop: 16 }}>
            <span style={LABEL}>Other References</span>
            <span style={VALUE}>{pi.other_references}</span>
          </div>
        )}
      </div>

      {/* Line items */}
      {renderLineItems()}

      {/* Additional charges + Totals */}
      <div style={CARD}>
        <h2 style={SECTION_TITLE}>Additional Charges</h2>
        {renderCharges()}
      </div>

      {renderTotals()}

      {/* Signed copy upload (FR-08.4) */}
      {renderSignedCopy()}

      {/* T&C */}
      {pi.tc_content && (
        <div style={CARD}>
          <h2 style={SECTION_TITLE}>Terms &amp; Conditions</h2>
          <div
            style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}
            dangerouslySetInnerHTML={{ __html: pi.tc_content }}
          />
        </div>
      )}

      <AuditLogDrawer
        open={auditDrawerOpen}
        onClose={() => setAuditDrawerOpen(false)}
        entries={auditLogs}
        title="Audit Log"
      />
    </div>
  );
}
