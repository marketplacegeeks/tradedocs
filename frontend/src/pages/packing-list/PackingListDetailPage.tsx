// Packing List detail page — FR-14M.14.
// Tabbed layout: Document Header | Containers & Items | Final Rates | Bank & Payment
// Plus workflow action buttons, audit trail drawer.

// Convert a USD amount to words, e.g. 1234.56 → "One Thousand Two Hundred Thirty-Four US Dollars and Fifty-Six Cents Only"
function amountToWords(amount: number): string {
  const ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen",
    "Eighteen", "Nineteen"];
  const tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];

  function toWords(n: number): string {
    if (n === 0) return "";
    if (n < 20) return ones[n];
    if (n < 100) return tens[Math.floor(n / 10)] + (n % 10 ? "-" + ones[n % 10] : "");
    if (n < 1000) return ones[Math.floor(n / 100)] + " Hundred" + (n % 100 ? " " + toWords(n % 100) : "");
    if (n < 1_000_000) return toWords(Math.floor(n / 1000)) + " Thousand" + (n % 1000 ? " " + toWords(n % 1000) : "");
    return toWords(Math.floor(n / 1_000_000)) + " Million" + (n % 1_000_000 ? " " + toWords(n % 1_000_000) : "");
  }

  const rounded = Math.round(amount * 100) / 100;
  const dollars = Math.floor(rounded);
  const cents = Math.round((rounded - dollars) * 100);
  const dollarWords = dollars === 0 ? "Zero" : toWords(dollars);
  const centsText = cents > 0 ? ` and ${toWords(cents)} Cents` : "";
  return `${dollarWords} US Dollars${centsText} Only`;
}

// Strip trailing zeros: 12.000 → "12", 12.500 → "12.5", 12.55 → "12.55"
function fmtQty(v: string | number | null | undefined) {
  if (v === null || v === undefined || v === "") return "—";
  const n = parseFloat(String(v));
  // Show decimals only if not a whole number
  if (Number.isInteger(n)) {
    return n.toLocaleString("en-US", { maximumFractionDigits: 0 });
  }
  return n.toLocaleString("en-US", { maximumFractionDigits: 3 });
}

// Format weight values (show decimals only if present)
function fmtWeight(v: string | number | null | undefined) {
  if (v === null || v === undefined || v === "") return "—";
  const n = parseFloat(String(v));
  // Show decimals only if not a whole number
  if (Number.isInteger(n)) {
    return n.toLocaleString("en-US", { maximumFractionDigits: 0 });
  }
  return n.toLocaleString("en-US", { maximumFractionDigits: 1 });
}
// Like fmtQty but max 2 decimal places (for money without $ sign)
function fmtNum(v: string | number | null | undefined) {
  if (v === null || v === undefined || v === "") return "0";
  const n = parseFloat(String(v));
  return n.toLocaleString("en-US", { maximumFractionDigits: 2 });
}
function fmtMoney(v: string | number | null | undefined) {
  if (v === null || v === undefined || v === "") return "$0";
  const n = parseFloat(String(v));
  return `$${n.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { message, Modal, Input } from "antd";
import AuditLogDrawer from "../../components/AuditLogDrawer";
import { ArrowLeft, Edit2, Clock, Trash2, FileDown, Upload, Paperclip } from "lucide-react";

import {
  getPackingList,
  deletePackingList,
  packingListWorkflow,
  getPlAuditLog,
  getCommercialInvoice,
  updateCILineItem,
  downloadPackingListPDF,
  uploadPlSignedCopy,
  uploadCiSignedCopy,
  hardDeletePackingList,
} from "../../api/packingLists";
import type { PackingList, CILineItem } from "../../api/packingLists";
import WorkflowActionButton from "../../components/common/WorkflowActionButton";
import { useAuth } from "../../store/AuthContext";
import { extractApiError } from "../../utils/apiErrors";
import {
  DOCUMENT_STATUS,
  DOCUMENT_STATUS_CHIP,
  DOCUMENT_STATUS_LABELS,
  ROLES,
} from "../../utils/constants";

// ---- Shared style tokens ----------------------------------------------------

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
  marginTop: 0,
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

const TH: React.CSSProperties = {
  padding: "10px 14px",
  fontFamily: "var(--font-body)",
  fontSize: 11,
  fontWeight: 600,
  color: "var(--text-muted)",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  background: "var(--bg-base)",
  borderBottom: "1px solid var(--border-light)",
  textAlign: "left" as const,
};

const TD: React.CSSProperties = {
  padding: "12px 14px",
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-secondary)",
  borderBottom: "1px solid var(--border-light)",
};

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <span style={LABEL}>{label}</span>
      <span style={VALUE}>{value || "—"}</span>
    </div>
  );
}

function StatusChip({ status }: { status: string }) {
  const cls = DOCUMENT_STATUS_CHIP[status] ?? "chip-blue";
  const label = DOCUMENT_STATUS_LABELS[status] ?? status;
  const chipStyles: Record<string, React.CSSProperties> = {
    "chip-blue": { background: "var(--pastel-blue)", color: "var(--pastel-blue-text)" },
    "chip-yellow": { background: "var(--pastel-yellow)", color: "var(--pastel-yellow-text)" },
    "chip-green": { background: "var(--pastel-green)", color: "var(--pastel-green-text)" },
    "chip-orange": { background: "var(--pastel-orange)", color: "var(--pastel-orange-text)" },
    "chip-pink": { background: "var(--pastel-pink)", color: "var(--pastel-pink-text)" },
  };
  return (
    <span style={{
      ...chipStyles[cls],
      padding: "3px 12px",
      borderRadius: 999,
      fontFamily: "var(--font-body)",
      fontSize: 12,
      fontWeight: 600,
    }}>
      {label}
    </span>
  );
}

// ---- Tab: Document Header ---------------------------------------------------

function HeaderTab({ pl }: { pl: PackingList }) {
  return (
    <>
      <div style={CARD}>
        <p style={SECTION_TITLE}>Document Numbers & Dates</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
          <Field label="PL Number" value={pl.pl_number} />
          <Field label="PL Date" value={pl.pl_date} />
          <Field label="CI Number" value={pl.ci_number} />
          <Field label="CI Date" value={pl.ci_date} />
          <Field label="Proforma Invoice" value={pl.pi_number_display} />
        </div>
      </div>

      <div style={CARD}>
        <p style={SECTION_TITLE}>Parties</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
          <Field label="Exporter" value={pl.exporter_name} />
          <Field label="Consignee" value={pl.consignee_name} />
          <Field label="Buyer" value={pl.buyer_name} />
          <Field label="Notify Party" value={pl.notify_party_name} />
        </div>
      </div>

      <div style={CARD}>
        <p style={SECTION_TITLE}>Order References</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
          {pl.po_number && <Field label="PO Number" value={`${pl.po_number}${pl.po_date ? ` / ${pl.po_date}` : ""}`} />}
          {pl.lc_number && <Field label="LC Number" value={`${pl.lc_number}${pl.lc_date ? ` / ${pl.lc_date}` : ""}`} />}
          {pl.bl_number && <Field label="BL Number" value={`${pl.bl_number}${pl.bl_date ? ` / ${pl.bl_date}` : ""}`} />}
          {pl.so_number && <Field label="SO Number" value={`${pl.so_number}${pl.so_date ? ` / ${pl.so_date}` : ""}`} />}
          {pl.other_references && <Field label="Other References" value={pl.other_references} />}
        </div>
        {pl.additional_description && (
          <Field label="Additional Description" value={pl.additional_description} />
        )}
      </div>

      <div style={CARD}>
        <p style={SECTION_TITLE}>Shipping & Logistics</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
          <Field label="Pre-Carriage By" value={pl.pre_carriage_by_name} />
          <Field label="Place of Receipt" value={pl.place_of_receipt_name} />
          <Field label="Place of Receipt by Pre-Carrier" value={pl.place_of_receipt_by_pre_carrier_name} />
          <Field label="Vessel / Flight No" value={pl.vessel_flight_no} />
          <Field label="Port of Loading" value={pl.port_of_loading_name} />
          <Field label="Port of Discharge" value={pl.port_of_discharge_name} />
          <Field label="Final Destination" value={pl.final_destination_name} />
          <Field label="Country of Origin" value={pl.country_of_origin_name} />
          <Field label="Country of Final Destination" value={pl.country_of_final_destination_name} />
          <Field label="Incoterms" value={pl.incoterms_display} />
          <Field label="Payment Terms" value={pl.payment_terms_display} />
        </div>
      </div>
    </>
  );
}

// ---- Tab: Containers & Items ------------------------------------------------

function ContainersTab({ pl }: { pl: PackingList }) {
  if (!pl.containers || pl.containers.length === 0) {
    return (
      <div style={CARD}>
        <p style={{ fontFamily: "var(--font-body)", color: "var(--text-muted)", fontSize: 14 }}>
          No containers added yet.
        </p>
      </div>
    );
  }

  return (
    <>
      {pl.containers.map((container, idx) => (
        <div key={container.id} style={{ ...CARD, marginBottom: 20 }}>
          <p style={SECTION_TITLE}>
            Container {idx + 1}: {container.container_ref || "—"}
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 16 }}>
            <Field label="Container Ref" value={container.container_ref} />
            <Field label="Marks & Numbers" value={container.marks_numbers} />
            <Field label="Seal Number" value={container.seal_number} />
            <Field label="Tare Weight" value={`${container.tare_weight} kg`} />
            <Field label="Gross Weight" value={`${container.gross_weight} kg`} />
          </div>

          {container.items.length > 0 && (
            <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 8 }}>
              <thead>
                <tr>
                  <th style={TH}>Item Code</th>
                  <th style={TH}>HSN</th>
                  <th style={TH}>Description</th>
                  <th style={TH}>Batch No.</th>
                  <th style={TH}>Quantity of Items</th>
                  <th style={TH}>Type of Package</th>
                  <th style={TH}>Material Unit</th>
                  <th style={TH}>Net Weight Per Item</th>
                  <th style={TH}>Weight per empty package</th>
                  <th style={TH}>Net Material Wt</th>
                  <th style={TH}>Gross Weight</th>
                </tr>
              </thead>
              <tbody>
                {container.items.map((item) => (
                  <tr key={item.id}>
                    <td style={{ ...TD, fontWeight: 600, color: "var(--text-primary)" }}>{item.item_code}</td>
                    <td style={TD}>{item.hsn_code || "—"}</td>
                    <td style={TD}>{item.description}</td>
                    <td style={TD}>{item.batch_details || "—"}</td>
                    <td style={TD}>{fmtQty(item.no_of_packages)}</td>
                    <td style={TD}>{item.type_of_package_name || "—"}</td>
                    <td style={TD}>{item.uom_abbr ?? "—"}</td>
                    <td style={TD}>{fmtQty(item.qty_per_package)}</td>
                    <td style={TD}>{fmtQty(item.weight_per_unit_packaging)}</td>
                    <td style={TD}>{fmtQty(item.net_material_weight)}</td>
                    <td style={TD}>{fmtQty(item.item_gross_weight)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </>
  );
}

// ---- Tab: Final Rates -------------------------------------------------------

function FinalRatesTab({ pl, ciId }: { pl: PackingList; ciId: number | null }) {
  const queryClient = useQueryClient();

  const { data: ci } = useQuery({
    queryKey: ["commercial-invoice", ciId],
    queryFn: () => getCommercialInvoice(ciId!),
    enabled: ciId != null,
  });

  const isEditable =
    pl.status === DOCUMENT_STATUS.DRAFT || pl.status === DOCUMENT_STATUS.REWORK;

  const [editingRate, setEditingRate] = useState<{ id: number; value: string } | null>(null);
  const [editingPkg, setEditingPkg] = useState<{ id: number; value: string } | null>(null);

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { rate?: string; packages_kind?: string } }) =>
      updateCILineItem(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commercial-invoice", ciId] });
      message.success("Updated.");
    },
    onError: (err: unknown) => message.error(extractApiError(err, "Failed to update.")),
  });

  if (!ci) {
    return (
      <div style={CARD}>
        <p style={{ fontFamily: "var(--font-body)", color: "var(--text-muted)" }}>
          No commercial invoice found.
        </p>
      </div>
    );
  }

  // Get the currency code from the CI (defaults to "USD" if not available)
  const currencyCode = ci.currency_display?.code ?? "USD";

  return (
    <>
      <div style={CARD}>
        <p style={SECTION_TITLE}>Final Rates — Aggregated by Item Code + UOM</p>
        {ci.line_items.length === 0 ? (
          <p style={{ fontFamily: "var(--font-body)", color: "var(--text-muted)", fontSize: 14 }}>
            No items yet. Add containers and items first.
          </p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={TH}>Item Code</th>
                <th style={TH}>Description</th>
                <th style={TH}>HSN</th>
                <th style={TH}>No. & Kind of Pkgs</th>
                <th style={TH}>Total Qty</th>
                <th style={TH}>UOM</th>
                <th style={TH}>Rate ({currencyCode})</th>
                <th style={TH}>Amount ({currencyCode})</th>
              </tr>
            </thead>
            <tbody>
              {ci.line_items.map((li) => (
                <tr key={li.id}>
                  <td style={{ ...TD, fontWeight: 600, color: "var(--text-primary)" }}>{li.item_code}</td>
                  <td style={TD}>{li.description}</td>
                  <td style={TD}>{li.hsn_code || "—"}</td>
                  <td style={{ ...TD, background: isEditable ? "var(--pastel-yellow)" : "inherit" }}>
                    {/* packages_kind is editable per FR-14M.10 */}
                    {isEditable && editingPkg?.id === li.id ? (
                      <input
                        autoFocus
                        style={{ background: "var(--bg-input)", border: "1px solid var(--border-medium)", borderRadius: 6, padding: "4px 8px", fontSize: 13, width: "100%", fontFamily: "var(--font-body)" }}
                        value={editingPkg.value}
                        onChange={(e) => setEditingPkg({ id: li.id, value: e.target.value })}
                        onBlur={() => {
                          if (editingPkg.value !== li.packages_kind) {
                            updateMutation.mutate({ id: li.id, data: { packages_kind: editingPkg.value } });
                          }
                          setEditingPkg(null);
                        }}
                        onKeyDown={(e) => e.key === "Escape" && setEditingPkg(null)}
                      />
                    ) : (
                      <span
                        style={{ cursor: isEditable ? "pointer" : "default" }}
                        title={isEditable ? "Click to edit" : undefined}
                        onClick={() => isEditable && setEditingPkg({ id: li.id, value: li.packages_kind })}
                      >
                        {li.packages_kind || "—"}
                      </span>
                    )}
                  </td>
                  <td style={TD}>{fmtQty(li.total_quantity)}</td>
                  <td style={TD}>{li.uom_abbr ?? "—"}</td>
                  <td style={TD}>
                    {isEditable && editingRate?.id === li.id ? (
                      <>
                        <input
                          autoFocus
                          type="number"
                          step="0.01"
                          style={{ background: "var(--bg-input)", border: "1px solid var(--border-medium)", borderRadius: 6, padding: "4px 8px", fontSize: 13, width: 100, fontFamily: "var(--font-body)" }}
                          value={editingRate.value}
                          onChange={(e) => setEditingRate({ id: li.id, value: e.target.value })}
                          onBlur={() => {
                            if (editingRate.value !== li.rate) {
                              updateMutation.mutate({ id: li.id, data: { rate: editingRate.value } });
                            }
                            setEditingRate(null);
                          }}
                          onKeyDown={(e) => e.key === "Escape" && setEditingRate(null)}
                        />
                        {li.uom_abbr && (
                          <div style={{ fontFamily: "var(--font-body)", fontSize: 11, color: "var(--text-muted)", marginTop: 3 }}>
                            {currencyCode} per {li.uom_abbr}
                          </div>
                        )}
                      </>
                    ) : (
                      <span
                        style={{ cursor: isEditable ? "pointer" : "default", color: isEditable ? "var(--primary)" : "inherit" }}
                        title={isEditable ? "Click to edit rate" : undefined}
                        onClick={() => isEditable && setEditingRate({ id: li.id, value: li.rate })}
                      >
                        {fmtNum(li.rate)}
                        {li.uom_abbr && (
                          <span style={{ fontFamily: "var(--font-body)", fontSize: 11, color: "var(--text-muted)", marginLeft: 4 }}>
                            / {li.uom_abbr}
                          </span>
                        )}
                      </span>
                    )}
                  </td>
                  <td style={{ ...TD, fontWeight: 600 }}>{currencyCode} {fmtNum(li.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div style={CARD}>
        {(() => {
          const incotermCode = pl.incoterms_display?.split("–")[0]?.trim() ?? null;
          const itemTotal = ci.line_items.reduce((sum, li) => sum + (parseFloat(li.amount as any) || 0), 0);
          const freightAmt = parseFloat(ci.freight as any) || 0;
          const insuranceAmt = parseFloat(ci.insurance as any) || 0;
          // Invoice Total = line item amounts only (freight/insurance are reference figures on the CI PDF)
          const invoiceTotal = itemTotal;
          const fmt = (n: number) => n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

          return (
            <>
              <div style={{ background: "var(--bg-base)", borderRadius: 8, padding: "12px 14px", marginBottom: 10 }}>
                <p style={{ fontFamily: "var(--font-body)", fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10, marginTop: 0 }}>
                  Cost Breakdown{incotermCode ? ` (${incotermCode})` : ""}
                </p>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>Invoice Value (Line Items)</span>
                  <span style={{ fontFamily: "var(--font-body)", fontSize: 13 }}>{currencyCode} {fmt(itemTotal)}</span>
                </div>
                {ci.freight && (
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>Freight ({currencyCode})</span>
                    <span style={{ fontFamily: "var(--font-body)", fontSize: 13 }}>{currencyCode} {fmt(freightAmt)}</span>
                  </div>
                )}
                {ci.insurance && (
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>Insurance ({currencyCode})</span>
                    <span style={{ fontFamily: "var(--font-body)", fontSize: 13 }}>{currencyCode} {fmt(insuranceAmt)}</span>
                  </div>
                )}
              </div>

              <div style={{ borderTop: "2px solid var(--border-medium)", paddingTop: 10, marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>Invoice Total (Amount Payable)</span>
                <span style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 700, color: "var(--primary)" }}>{currencyCode} {fmt(invoiceTotal)}</span>
              </div>

              <div style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)", marginBottom: ci.lc_details ? 16 : 0 }}>
                <strong>Amount in Words:</strong> {amountToWords(invoiceTotal)}
              </div>

              {ci.lc_details && (
                <div style={{ marginTop: 16, borderTop: "1px solid var(--border-light)", paddingTop: 12 }}>
                  <span style={LABEL}>L/C Details</span>
                  <span style={VALUE}>{ci.lc_details}</span>
                </div>
              )}
            </>
          );
        })()}
      </div>
    </>
  );
}

// ---- Tab: Bank & Payment ----------------------------------------------------

function BankTab({ pl }: { pl: PackingList }) {
  const { data: ci } = useQuery({
    queryKey: ["commercial-invoice", pl.ci_id],
    queryFn: () => getCommercialInvoice(pl.ci_id!),
    enabled: pl.ci_id != null,
  });

  if (!ci || !ci.bank_details) {
    return (
      <div style={CARD}>
        <p style={{ fontFamily: "var(--font-body)", color: "var(--text-muted)", fontSize: 14 }}>
          No bank selected. Edit the document to add bank details.
        </p>
      </div>
    );
  }

  const b = ci.bank_details;
  return (
    <div style={CARD}>
      <p style={SECTION_TITLE}>Bank Details</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        <Field label="Beneficiary Name" value={b.beneficiary_name} />
        <Field label="Bank Name" value={b.bank_name} />
        <Field label="Branch Name" value={b.branch_name} />
        <Field label="Branch Address" value={b.branch_address} />
        <Field label="Account Number" value={b.account_number} />
        <Field label="IFSC / Routing Number" value={b.routing_number} />
        <Field label="SWIFT Code" value={b.swift_code} />
        <Field label="IBAN" value={b.iban} />
      </div>
      {b.intermediary_bank_name && (
        <>
          <div style={{ borderTop: "1px solid var(--border-light)", margin: "16px 0" }} />
          <p style={SECTION_TITLE}>Intermediary Institution (for {b.intermediary_currency})</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
            <Field label="Intermediary Bank" value={b.intermediary_bank_name} />
            <Field label="Account Number" value={b.intermediary_account_number} />
            <Field label="SWIFT Code" value={b.intermediary_swift_code} />
          </div>
        </>
      )}
    </div>
  );
}

// ---- Main Page --------------------------------------------------------------

const TABS = ["Document Header", "Containers & Items", "Final Rates", "Bank & Payment"] as const;
type Tab = typeof TABS[number];

export default function PackingListDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<Tab>("Document Header");
  const [auditOpen, setAuditOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  const { data: pl, isLoading } = useQuery({
    queryKey: ["packing-list", Number(id)],
    queryFn: () => getPackingList(Number(id)),
    enabled: !!id,
  });

  const { data: auditLog = [] } = useQuery({
    queryKey: ["pl-audit", Number(id)],
    queryFn: () => getPlAuditLog(Number(id)),
    enabled: auditOpen && !!id,
  });

  // Fetch CI to read signed_copy_url (FR-08.4). Only needed when Approved.
  const { data: ciData } = useQuery({
    queryKey: ["commercial-invoice", pl?.ci_id],
    queryFn: () => getCommercialInvoice(pl!.ci_id!),
    enabled: !!pl?.ci_id && pl?.status === DOCUMENT_STATUS.APPROVED,
  });

  const deleteMutation = useMutation({
    mutationFn: () => deletePackingList(Number(id)),
    onSuccess: () => {
      message.success("Packing List deleted.");
      navigate("/packing-lists");
    },
    onError: (err: unknown) => message.error(extractApiError(err, "Could not delete this document.")),
  });

  const hardDeleteMutation = useMutation({
    mutationFn: () => hardDeletePackingList(Number(id)),
    onSuccess: () => {
      message.success("Packing List permanently deleted.");
      navigate("/packing-lists");
    },
    onError: (err: unknown) => message.error(extractApiError(err, "Delete failed. Please try again.")),
  });

  function confirmHardDelete() {
    Modal.confirm({
      title: "Permanently delete this Packing List?",
      content: "This action cannot be undone. The PL, its linked Commercial Invoice, and all containers/items will be removed from the database.",
      okText: "Delete permanently",
      okButtonProps: { danger: true },
      cancelText: "Cancel",
      onOk: () => hardDeleteMutation.mutate(),
    });
  }

  const uploadPlSignedCopyMutation = useMutation({
    mutationFn: (file: File) => uploadPlSignedCopy(Number(id), file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["packing-list", id] });
      message.success("PL signed copy uploaded.");
    },
    onError: (err: unknown) => message.error(extractApiError(err, "Upload failed.")),
  });

  const uploadCiSignedCopyMutation = useMutation({
    mutationFn: (file: File) => uploadCiSignedCopy(pl?.ci_id as number, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["commercial-invoice", pl?.ci_id] });
      message.success("CI signed copy uploaded.");
    },
    onError: (err: unknown) => message.error(extractApiError(err, "Upload failed.")),
  });

  if (isLoading || !pl) {
    return (
      <div style={{ padding: 32, fontFamily: "var(--font-body)", color: "var(--text-muted)" }}>
        Loading…
      </div>
    );
  }

  const isEditable = pl.status === DOCUMENT_STATUS.DRAFT || pl.status === DOCUMENT_STATUS.REWORK;
  const isDraft = pl.status === DOCUMENT_STATUS.DRAFT;
  const isCreator = user?.id === pl.created_by;
  const isAdmin = user?.role === ROLES.COMPANY_ADMIN || user?.role === ROLES.SUPER_ADMIN;
  // Any Maker can edit or delete any editable PL — not just the creator.
  const canEdit = isEditable && (user?.role === ROLES.MAKER || isCreator || isAdmin);
  const canDelete = isDraft && (user?.role === ROLES.MAKER || isCreator || isAdmin);
  const isApproved = pl.status === DOCUMENT_STATUS.APPROVED;
  // FR-08.3: PDF available to all roles in all states (DRAFT watermark shown on non-Approved).
  const canDownloadPDF = true;

  return (
    <div style={{ padding: 32, background: "var(--bg-base)", minHeight: "100vh" }}>
      {/* Page header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <button
            onClick={() => navigate("/packing-lists")}
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4, fontFamily: "var(--font-body)", fontSize: 13, padding: 0, marginBottom: 8 }}
          >
            <ArrowLeft size={14} /> Back
          </button>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
              {pl.pl_number}
            </h1>
            {pl.ci_number && (
              <span style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-secondary)" }}>
                + {pl.ci_number}
              </span>
            )}
            <StatusChip status={pl.status} />
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <button
            onClick={() => setAuditOpen(true)}
            style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "8px 14px", borderRadius: 8, border: "1px solid var(--border-medium)", background: "var(--bg-surface)", cursor: "pointer", fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}
          >
            <Clock size={14} /> Audit Trail
          </button>

          {canEdit && (
            <button
              onClick={() => {
                // Map active detail tab → wizard step number
                const stepMap: Record<string, number> = {
                  "Document Header": 1,
                  "Containers & Items": 3,
                  "Final Rates": 4,
                  "Bank & Payment": 1,
                };
                const step = stepMap[activeTab] ?? 1;
                navigate(`/packing-lists/${pl.id}/edit?step=${step}`);
              }}
              style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "8px 14px", borderRadius: 8, border: "1px solid var(--border-medium)", background: "var(--bg-surface)", cursor: "pointer", fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}
            >
              <Edit2 size={14} /> Edit
            </button>
          )}

          {canDelete && (
            <button
              onClick={() => setDeleteModalOpen(true)}
              style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "8px 14px", borderRadius: 8, border: "none", background: "var(--pastel-pink)", cursor: "pointer", fontFamily: "var(--font-body)", fontSize: 13, color: "var(--pastel-pink-text)" }}
            >
              <Trash2 size={14} /> Delete
            </button>
          )}

          {canDownloadPDF && (
            <button
              onClick={() =>
                downloadPackingListPDF(pl.id, `${pl.pl_number}.pdf`).catch(() =>
                  message.error("Could not download PDF.")
                )
              }
              style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "8px 14px", borderRadius: 8, border: "none", background: "var(--primary)", cursor: "pointer", fontFamily: "var(--font-body)", fontSize: 13, color: "#fff" }}
            >
              <FileDown size={14} /> Download PDF
            </button>
          )}

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
          <WorkflowActionButton
            documentId={pl.id}
            documentStatus={pl.status}
            userRole={user?.role ?? ""}
            documentType="packing_list"
            onSuccess={(newStatus) => {
              queryClient.setQueryData<PackingList>(["packing-list", pl.id], (old) =>
                old ? { ...old, status: newStatus } : old
              );
            }}
            onAction={(action, comment) => packingListWorkflow(pl.id, action, comment)}
          />
        </div>
      </div>

      {/* Last rework comment */}
      {pl.status === DOCUMENT_STATUS.REWORK && (
        <div style={{ ...CARD, background: "var(--pastel-yellow)", borderColor: "var(--pastel-yellow-text)", marginBottom: 20 }}>
          <p style={{ margin: 0, fontFamily: "var(--font-body)", fontSize: 13, color: "var(--pastel-yellow-text)" }}>
            This document was sent for rework. Check the Audit Trail for comments.
          </p>
        </div>
      )}

      {/* Tab navigation */}
      <div style={{ display: "flex", gap: 0, marginBottom: 20, borderBottom: "2px solid var(--border-light)" }}>
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: "10px 20px",
              background: "none",
              border: "none",
              borderBottom: activeTab === tab ? "2px solid var(--primary)" : "2px solid transparent",
              marginBottom: -2,
              cursor: "pointer",
              fontFamily: "var(--font-body)",
              fontSize: 14,
              fontWeight: activeTab === tab ? 600 : 400,
              color: activeTab === tab ? "var(--primary)" : "var(--text-secondary)",
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "Document Header" && <HeaderTab pl={pl} />}
      {activeTab === "Containers & Items" && <ContainersTab pl={pl} />}
      {activeTab === "Final Rates" && <FinalRatesTab pl={pl} ciId={pl.ci_id} />}
      {activeTab === "Bank & Payment" && <BankTab pl={pl} />}

      {/* Signed copy upload (FR-08.4) — visible only when Approved */}
      {isApproved && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginTop: 4 }}>
          {/* PL signed copy */}
          <div style={CARD}>
            <h2 style={SECTION_TITLE}>Packing List — Signed Copy</h2>
            <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", marginBottom: 14 }}>
              Upload a scanned signed copy of the approved Packing List (PDF, JPG, or PNG — max 3 MB).
            </p>
            {pl.signed_copy_url && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--pastel-green)", borderRadius: 8, padding: "10px 14px", marginBottom: 14 }}>
                <Paperclip size={14} strokeWidth={1.5} color="var(--pastel-green-text)" />
                <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--pastel-green-text)", flex: 1 }}>Signed copy uploaded</span>
                <a href={pl.signed_copy_url} target="_blank" rel="noreferrer" style={{ fontFamily: "var(--font-body)", fontSize: 12, color: "var(--pastel-green-text)", fontWeight: 600 }}>View / Download</a>
              </div>
            )}
            <label style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "var(--bg-input)", border: "1px dashed var(--border-medium)", borderRadius: 8, padding: "8px 16px", fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)", cursor: uploadPlSignedCopyMutation.isPending ? "not-allowed" : "pointer", opacity: uploadPlSignedCopyMutation.isPending ? 0.6 : 1 }}>
              <Upload size={14} strokeWidth={1.5} />
              {uploadPlSignedCopyMutation.isPending ? "Uploading…" : pl.signed_copy_url ? "Replace signed copy" : "Upload signed copy"}
              <input type="file" accept=".pdf,.jpg,.jpeg,.png" style={{ display: "none" }} disabled={uploadPlSignedCopyMutation.isPending} onChange={(e) => { const file = e.target.files?.[0]; if (file) uploadPlSignedCopyMutation.mutate(file); e.target.value = ""; }} />
            </label>
          </div>

          {/* CI signed copy */}
          {pl.ci_id && (
            <div style={CARD}>
              <h2 style={SECTION_TITLE}>Commercial Invoice — Signed Copy</h2>
              <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", marginBottom: 14 }}>
                Upload a scanned signed copy of the approved Commercial Invoice (PDF, JPG, or PNG — max 3 MB).
              </p>
              {pl.ci_status === DOCUMENT_STATUS.APPROVED && ciData?.signed_copy_url && (
                <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--pastel-green)", borderRadius: 8, padding: "10px 14px", marginBottom: 14 }}>
                  <Paperclip size={14} strokeWidth={1.5} color="var(--pastel-green-text)" />
                  <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--pastel-green-text)", flex: 1 }}>Signed copy uploaded</span>
                  <a href={ciData.signed_copy_url} target="_blank" rel="noreferrer" style={{ fontFamily: "var(--font-body)", fontSize: 12, color: "var(--pastel-green-text)", fontWeight: 600 }}>View / Download</a>
                </div>
              )}
              <label style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "var(--bg-input)", border: "1px dashed var(--border-medium)", borderRadius: 8, padding: "8px 16px", fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)", cursor: uploadCiSignedCopyMutation.isPending ? "not-allowed" : "pointer", opacity: uploadCiSignedCopyMutation.isPending ? 0.6 : 1 }}>
                <Upload size={14} strokeWidth={1.5} />
                {uploadCiSignedCopyMutation.isPending ? "Uploading…" : ciData?.signed_copy_url ? "Replace signed copy" : "Upload signed copy"}
                <input type="file" accept=".pdf,.jpg,.jpeg,.png" style={{ display: "none" }} disabled={uploadCiSignedCopyMutation.isPending} onChange={(e) => { const file = e.target.files?.[0]; if (file) uploadCiSignedCopyMutation.mutate(file); e.target.value = ""; }} />
              </label>
            </div>
          )}
        </div>
      )}

      <AuditLogDrawer
        open={auditOpen}
        onClose={() => setAuditOpen(false)}
        entries={auditLog}
      />

      {/* Delete confirmation modal */}
      <Modal
        title="Delete Packing List"
        open={deleteModalOpen}
        onOk={() => {
          setDeleteModalOpen(false);
          deleteMutation.mutate();
        }}
        onCancel={() => setDeleteModalOpen(false)}
        okText="Delete"
        okButtonProps={{ danger: true }}
      >
        <p style={{ fontFamily: "var(--font-body)", fontSize: 14 }}>
          Are you sure you want to delete <strong>{pl.pl_number}</strong> and its linked Commercial Invoice <strong>{pl.ci_number}</strong>?
          This cannot be undone.
        </p>
      </Modal>
    </div>
  );
}
