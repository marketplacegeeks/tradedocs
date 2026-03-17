// Proforma Invoice detail page — FR-09.5 (line items), FR-09.7 (cost breakdown), FR-08 (workflow).
// Shows header, editable line items + charges (in DRAFT/REWORK), cost breakdown, workflow buttons, PDF download.

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { message, Modal, Tooltip, Drawer } from "antd";
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
} from "../../api/proformaInvoices";
import type { ProformaInvoiceLineItem, ProformaInvoiceCharge, AuditLogEntry } from "../../api/proformaInvoices";
import WorkflowActionButton from "../../components/common/WorkflowActionButton";
import { useAuth } from "../../store/AuthContext";
import {
  DOCUMENT_STATUS,
  DOCUMENT_STATUS_CHIP,
  DOCUMENT_STATUS_LABELS,
  INCOTERM_SELLER_FIELDS,
  COST_FIELD_LABELS,
} from "../../utils/constants";

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
  if (!v) return "$0.00";
  const n = parseFloat(v);
  return `$${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
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

  const { data: pi, isLoading } = useQuery({
    queryKey: ["proforma-invoice", piId],
    queryFn: () => getProformaInvoice(piId),
  });

  const { data: auditLogs = [] } = useQuery({
    queryKey: ["proforma-invoice", piId, "audit-log"],
    queryFn: () => getAuditLog(piId),
    enabled: auditDrawerOpen,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["proforma-invoice", piId] });
    queryClient.invalidateQueries({ queryKey: ["proforma-invoices"] });
  };

  // ---- Mutations -----------------------------------------------------------

  const addLineItemMutation = useMutation({
    mutationFn: (data: any) => createLineItem(piId, data),
    onSuccess: () => { invalidate(); setAddingLineItem(false); setLineItemForm(EMPTY_LINE_ITEM); },
    onError: (e: any) => message.error(e?.response?.data?.description?.[0] || "Failed to add line item."),
  });

  const updateLineItemMutation = useMutation({
    mutationFn: ({ lid, data }: { lid: number; data: any }) => updateLineItem(piId, lid, data),
    onSuccess: () => { invalidate(); setEditingLineItem(null); },
    onError: (e: any) => message.error("Failed to update line item."),
  });

  const deleteLineItemMutation = useMutation({
    mutationFn: (lid: number) => deleteLineItem(piId, lid),
    onSuccess: invalidate,
    onError: () => message.error("Failed to delete line item."),
  });

  const addChargeMutation = useMutation({
    mutationFn: (data: any) => createCharge(piId, data),
    onSuccess: () => { invalidate(); setAddingCharge(false); setChargeForm({ description: "", amount_usd: "" }); },
    onError: () => message.error("Failed to add charge."),
  });

  const deleteChargeMutation = useMutation({
    mutationFn: (cid: number) => deleteCharge(piId, cid),
    onSuccess: invalidate,
    onError: () => message.error("Failed to delete charge."),
  });

  const updateCostFieldsMutation = useMutation({
    mutationFn: (data: any) => updateProformaInvoice(piId, data),
    onSuccess: () => { invalidate(); message.success("Cost breakdown saved."); },
    onError: () => message.error("Failed to save cost breakdown."),
  });

  const uploadSignedCopyMutation = useMutation({
    mutationFn: (file: File) => uploadSignedCopy(piId, file),
    onSuccess: () => { invalidate(); message.success("Signed copy uploaded."); },
    onError: (e: any) => {
      const detail = e?.response?.data?.file?.[0] || e?.response?.data?.detail || "Upload failed.";
      message.error(detail);
    },
  });

  if (isLoading || !pi) {
    return (
      <div style={{ padding: 48, textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-body)" }}>
        Loading…
      </div>
    );
  }

  const isEditable = pi.status === DOCUMENT_STATUS.DRAFT || pi.status === DOCUMENT_STATUS.REWORK;
  const isCreator = pi.created_by === user?.id;
  const canEdit = isEditable && (isCreator || user?.role === "COMPANY_ADMIN");

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
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
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
                    {(["hsn_code", "item_code", "description", "quantity", "uom", "rate_usd"] as const).map((f) => (
                      <td key={f} style={TD}>
                        <input
                          style={INPUT}
                          value={(lineItemForm as any)[f]}
                          onChange={(e) => setLineItemForm((prev) => ({ ...prev, [f]: e.target.value }))}
                          placeholder={f.replace(/_/g, " ")}
                        />
                      </td>
                    ))}
                    <td style={TD}>—</td>
                    <td style={TD}>
                      <button
                        onClick={() => updateLineItemMutation.mutate({ lid: item.id, data: lineItemForm })}
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
                    <td style={{ ...TD, textAlign: "right" }}>{parseFloat(item.quantity).toLocaleString(undefined, { minimumFractionDigits: 3 })}</td>
                    <td style={TD}>{(item.uom as any)?.abbreviation ?? "—"}</td>
                    <td style={{ ...TD, textAlign: "right" }}>{formatMoney(item.rate_usd)}</td>
                    <td style={{ ...TD, textAlign: "right", fontWeight: 600 }}>{formatMoney(item.amount_usd)}</td>
                    {canEdit && (
                      <td style={TD}>
                        <div style={{ display: "flex", gap: 4 }}>
                          <button
                            onClick={() => { setEditingLineItem(item); setLineItemForm({ description: item.description, quantity: item.quantity, rate_usd: item.rate_usd, hsn_code: item.hsn_code, item_code: item.item_code, uom: String(item.uom ?? "") }); }}
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
                  {(["hsn_code", "item_code", "description", "quantity", "uom", "rate_usd"] as const).map((f) => (
                    <td key={f} style={TD}>
                      <input
                        style={INPUT}
                        value={(lineItemForm as any)[f]}
                        onChange={(e) => setLineItemForm((prev) => ({ ...prev, [f]: e.target.value }))}
                        placeholder={f.replace(/_/g, " ")}
                      />
                    </td>
                  ))}
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
                <td colSpan={canEdit ? 7 : 6} style={{ ...TD, textAlign: "right", fontWeight: 600, fontSize: 13 }}>Total Amount (USD)</td>
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
    const showCostBreakdown = incotermsCode && incotermsCode !== "EXW" && sellerFields.size > 0;

    return (
      <div style={{ ...CARD, maxWidth: 480, marginLeft: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>Total Amount (USD)</span>
          <span style={{ fontFamily: "var(--font-heading)", fontSize: 13, fontWeight: 600 }}>{formatMoney(pi.line_items_total)}</span>
        </div>
        {pi.charges.map((c) => (
          <div key={c.id} style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>{c.description}</span>
            <span style={{ fontFamily: "var(--font-body)", fontSize: 13 }}>{formatMoney(c.amount_usd)}</span>
          </div>
        ))}

        <div style={{ borderTop: "1px solid var(--border-light)", paddingTop: 8, marginTop: 4, display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
          <span style={{ fontFamily: "var(--font-heading)", fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>Grand Total Amount</span>
          <span style={{ fontFamily: "var(--font-heading)", fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>{formatMoney(pi.grand_total)}</span>
        </div>

        {showCostBreakdown && (
          <>
            <div style={{ background: "var(--bg-base)", borderRadius: 8, padding: "12px 14px", marginBottom: 10 }}>
              <p style={{ fontFamily: "var(--font-body)", fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 10 }}>
                Cost Breakdown ({incotermsCode})
              </p>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>FOB Value</span>
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
                      onChange={(e) => setCostFields((p) => ({ ...p, [field]: e.target.value }))}
                      onBlur={() => updateCostFieldsMutation.mutate({ [field]: costFields[field] || null })}
                      placeholder="0.00"
                    />
                  ) : (
                    <span style={{ fontFamily: "var(--font-body)", fontSize: 13 }}>{formatMoney((pi as any)[field])}</span>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        <div style={{ borderTop: "2px solid var(--border-medium)", paddingTop: 10, display: "flex", justifyContent: "space-between" }}>
          <span style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>Invoice Total Value</span>
          <span style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 700, color: "var(--primary)" }}>{formatMoney(pi.invoice_total)}</span>
        </div>
      </div>
    );
  }

  // ---- Audit log drawer ----------------------------------------------------

  function renderAuditLog() {
    return (
      <Drawer
        title="Audit Log"
        open={auditDrawerOpen}
        onClose={() => setAuditDrawerOpen(false)}
        width={400}
      >
        {auditLogs.length === 0 ? (
          <p style={{ color: "var(--text-muted)", fontFamily: "var(--font-body)", fontSize: 13 }}>No activity yet.</p>
        ) : (
          auditLogs.map((log) => (
            <div
              key={log.id}
              style={{
                padding: "12px 0",
                borderBottom: "1px solid var(--border-light)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span className={DOCUMENT_STATUS_CHIP[log.to_status] ?? "chip-blue"}>
                  {DOCUMENT_STATUS_LABELS[log.action] ?? log.action}
                </span>
                <span style={{ fontFamily: "var(--font-body)", fontSize: 11, color: "var(--text-muted)" }}>
                  {new Date(log.performed_at).toLocaleString()}
                </span>
              </div>
              <p style={{ fontFamily: "var(--font-body)", fontSize: 12, color: "var(--text-secondary)", margin: "4px 0 0" }}>
                by {log.performed_by_name}
                {log.comment && <> · "{log.comment}"</>}
              </p>
            </div>
          ))
        )}
      </Drawer>
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

      {/* Header bar */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 12, marginBottom: 24 }}>
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
            onClick={() => downloadPiPdf(piId, `${pi.pi_number}.pdf`)}
            style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              background: "var(--pastel-green)", color: "var(--pastel-green-text)",
              border: "none", borderRadius: 8, padding: "8px 14px",
              fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, cursor: "pointer",
            }}
          >
            <Download size={14} strokeWidth={1.5} /> Download PDF
          </button>
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
          <LabelValue label="Incoterms" value={pi.incoterms_code ?? "—"} />
          <LabelValue label="Payment Terms" value={pi.payment_terms_name ?? undefined} />
          <LabelValue label="Port of Loading" value={pi.port_of_loading_name ?? undefined} />
          <LabelValue label="Port of Discharge" value={pi.port_of_discharge_name ?? undefined} />
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

      {renderAuditLog()}
    </div>
  );
}
