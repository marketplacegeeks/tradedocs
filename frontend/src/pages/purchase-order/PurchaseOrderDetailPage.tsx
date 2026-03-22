// Purchase Order detail page — FR-PO-16.
// Read-only view with workflow action buttons, audit log drawer, and PDF download.

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { message } from "antd";
import { ArrowLeft, Download, Clock, Edit2 } from "lucide-react";

import {
  getPurchaseOrder,
  workflowPurchaseOrder,
  getPurchaseOrderAuditLog,
  downloadPurchaseOrderPdf,
} from "../../api/purchaseOrders";
import WorkflowActionButton from "../../components/common/WorkflowActionButton";
import AuditLogDrawer from "../../components/AuditLogDrawer";
import { useAuth } from "../../store/AuthContext";
import {
  DOCUMENT_STATUS,
  DOCUMENT_STATUS_CHIP,
  DOCUMENT_STATUS_LABELS,
  TRANSACTION_TYPE_LABELS,
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
  padding: "10px 14px",
  borderBottom: "1px solid var(--border-light)",
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-secondary)",
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

function fmtMoney(v: string | null | undefined, currencyCode?: string) {
  if (!v) return "0.00";
  const n = parseFloat(v);
  const formatted = n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return currencyCode ? `${currencyCode} ${formatted}` : formatted;
}

function fmtQty(v: string | null | undefined) {
  if (!v) return "0";
  const n = parseFloat(v);
  return n.toLocaleString("en-US", { maximumFractionDigits: 6 });
}

// ---- Main page -------------------------------------------------------------

export default function PurchaseOrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const poId = parseInt(id!, 10);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const [auditDrawerOpen, setAuditDrawerOpen] = useState(false);

  const { data: po, isLoading } = useQuery({
    queryKey: ["purchase-order", poId],
    queryFn: () => getPurchaseOrder(poId),
  });

  const { data: auditLogs = [] } = useQuery({
    queryKey: ["purchase-order", poId, "audit-log"],
    queryFn: () => getPurchaseOrderAuditLog(poId),
    enabled: auditDrawerOpen,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["purchase-order", poId] });
    queryClient.invalidateQueries({ queryKey: ["purchase-orders"] });
  };

  if (isLoading || !po) {
    return (
      <div style={{ padding: 48, textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-body)" }}>
        Loading…
      </div>
    );
  }

  const isEditable = po.status === DOCUMENT_STATUS.DRAFT || po.status === DOCUMENT_STATUS.REWORK;
  const isCreator = po.created_by === user?.id;
  const canEdit = isEditable && (isCreator || user?.role === "COMPANY_ADMIN");

  const txType = po.transaction_type;
  const showIGST = txType === "IGST";
  const showCGST = txType === "CGST_SGST";

  // Grand total is sum of all line item totals
  const grandTotal = po.line_items.reduce((sum, item) => sum + parseFloat(item.total || "0"), 0);

  // ---- Line items table ----------------------------------------------------

  function renderLineItems() {
    const currCode = po.currency_code;

    return (
      <div style={CARD}>
        <h2 style={SECTION_TITLE}>Line Items</h2>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
            <thead>
              <tr style={{ background: "var(--bg-base)" }}>
                <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", width: 36 }}>#</th>
                <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em" }}>Description</th>
                <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em" }}>Item Code</th>
                <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em" }}>HSN</th>
                <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", textAlign: "right" }}>Qty</th>
                <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", textAlign: "right" }}>Unit Price</th>
                <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", textAlign: "right" }}>Taxable Amt</th>
                {showIGST && (
                  <>
                    <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", textAlign: "right" }}>IGST %</th>
                    <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", textAlign: "right" }}>IGST Amt</th>
                  </>
                )}
                {showCGST && (
                  <>
                    <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", textAlign: "right" }}>CGST %</th>
                    <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", textAlign: "right" }}>CGST Amt</th>
                    <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", textAlign: "right" }}>SGST %</th>
                    <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", textAlign: "right" }}>SGST Amt</th>
                  </>
                )}
                <th style={{ ...TD, fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.04em", textAlign: "right" }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {po.line_items.map((item, idx) => (
                <tr key={item.id}>
                  <td style={TD}>{idx + 1}</td>
                  <td style={TD}>{item.description}</td>
                  <td style={TD}>{item.item_code || "—"}</td>
                  <td style={TD}>{item.hsn_code || "—"}</td>
                  <td style={{ ...TD, textAlign: "right" }}>{fmtQty(item.quantity)}</td>
                  <td style={{ ...TD, textAlign: "right" }}>{fmtMoney(item.unit_price, currCode)}</td>
                  <td style={{ ...TD, textAlign: "right" }}>{fmtMoney(item.taxable_amount, currCode)}</td>
                  {showIGST && (
                    <>
                      <td style={{ ...TD, textAlign: "right" }}>{item.igst_percent ? `${item.igst_percent}%` : "—"}</td>
                      <td style={{ ...TD, textAlign: "right" }}>{item.igst_amount ? fmtMoney(item.igst_amount, currCode) : "—"}</td>
                    </>
                  )}
                  {showCGST && (
                    <>
                      <td style={{ ...TD, textAlign: "right" }}>{item.cgst_percent ? `${item.cgst_percent}%` : "—"}</td>
                      <td style={{ ...TD, textAlign: "right" }}>{item.cgst_amount ? fmtMoney(item.cgst_amount, currCode) : "—"}</td>
                      <td style={{ ...TD, textAlign: "right" }}>{item.sgst_percent ? `${item.sgst_percent}%` : "—"}</td>
                      <td style={{ ...TD, textAlign: "right" }}>{item.sgst_amount ? fmtMoney(item.sgst_amount, currCode) : "—"}</td>
                    </>
                  )}
                  <td style={{ ...TD, textAlign: "right", fontWeight: 600, color: "var(--text-primary)" }}>
                    {fmtMoney(item.total, currCode)}
                  </td>
                </tr>
              ))}

              {po.line_items.length === 0 && (
                <tr>
                  <td colSpan={showIGST ? 9 : showCGST ? 11 : 7} style={{ ...TD, textAlign: "center", color: "var(--text-muted)", padding: "24px 14px" }}>
                    No line items yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Grand total */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 14, paddingTop: 12, borderTop: "2px solid var(--border-medium)" }}>
          <div style={{ textAlign: "right" }}>
            <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", marginRight: 24 }}>Grand Total</span>
            <span style={{ fontFamily: "var(--font-heading)", fontSize: 18, fontWeight: 700, color: "var(--primary)" }}>
              {po.currency_code} {grandTotal.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // ---- Main render ---------------------------------------------------------

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

      {/* Sticky header bar */}
      <div style={{
        position: "sticky", top: 0, zIndex: 10,
        background: "var(--bg-base)", paddingBottom: 16, marginBottom: 8,
        display: "flex", alignItems: "flex-start", justifyContent: "space-between",
        flexWrap: "wrap", gap: 12,
      }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
              {po.po_number}
            </h1>
            <span className={DOCUMENT_STATUS_CHIP[po.status] ?? "chip-blue"}>
              {DOCUMENT_STATUS_LABELS[po.status] ?? po.status}
            </span>
          </div>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
            Created by {po.created_by_name} · {po.po_date}
          </p>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          {canEdit && (
            <button
              onClick={() => navigate(`/purchase-orders/${poId}/edit`)}
              style={{
                display: "inline-flex", alignItems: "center", gap: 6,
                background: "var(--pastel-blue)", color: "var(--pastel-blue-text)",
                border: "none", borderRadius: 8, padding: "8px 14px",
                fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, cursor: "pointer",
              }}
            >
              <Edit2 size={14} strokeWidth={1.5} /> Edit
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
              const vendorSlug = (po.vendor_name ?? "").replace(/[^a-zA-Z0-9]/g, "");
              const isDraft = po.status !== DOCUMENT_STATUS.APPROVED;
              const filename = isDraft
                ? `${dateStr}_Draft_PurchaseOrder_${vendorSlug}.pdf`
                : `${dateStr}_PurchaseOrder_${vendorSlug}.pdf`;
              downloadPurchaseOrderPdf(poId, filename).catch(() =>
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

          {user && (
            <WorkflowActionButton
              documentId={poId}
              documentStatus={po.status}
              userRole={user.role}
              documentType="purchase_order"
              onSuccess={() => invalidate()}
              onAction={(action, comment) => workflowPurchaseOrder(poId, action, comment)}
            />
          )}
        </div>
      </div>

      {/* Vendor + Delivery Address */}
      <div style={CARD}>
        <h2 style={SECTION_TITLE}>Vendor &amp; Delivery</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 20 }}>
          <LabelValue label="Vendor" value={po.vendor_name} />
          {po.buyer_name && <LabelValue label="Buyer" value={po.buyer_name} />}
          <LabelValue label="Delivery Address" value={po.delivery_address_detail} />
          <LabelValue label="Customer No" value={po.customer_no} />
          <LabelValue label="Internal Contact" value={po.internal_contact_name} />
          {po.internal_contact_phone && (
            <LabelValue label="Contact Phone" value={po.internal_contact_phone} />
          )}
        </div>
      </div>

      {/* Document details */}
      <div style={CARD}>
        <h2 style={SECTION_TITLE}>Document Details</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
          <LabelValue label="Currency" value={po.currency_code} />
          <LabelValue label="Bank" value={po.bank_name} />
          <LabelValue label="Payment Terms" value={po.payment_terms_name} />
          <LabelValue label="Country of Origin" value={po.country_of_origin_name} />
          <LabelValue label="Time of Delivery" value={po.time_of_delivery} />
          <div>
            <span style={LABEL}>Transaction Type</span>
            <span style={VALUE}>{TRANSACTION_TYPE_LABELS[po.transaction_type as keyof typeof TRANSACTION_TYPE_LABELS] ?? po.transaction_type}</span>
          </div>
        </div>
      </div>

      {/* Line items */}
      {renderLineItems()}

      {/* T&C */}
      {po.tc_content && (
        <div style={CARD}>
          <h2 style={SECTION_TITLE}>Terms &amp; Conditions</h2>
          <div
            style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}
            dangerouslySetInnerHTML={{ __html: po.tc_content }}
          />
        </div>
      )}

      {/* Remarks */}
      {po.remarks && (
        <div style={CARD}>
          <h2 style={SECTION_TITLE}>Remarks</h2>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)", margin: 0, lineHeight: 1.6 }}>
            {po.remarks}
          </p>
        </div>
      )}

      <AuditLogDrawer
        open={auditDrawerOpen}
        onClose={() => setAuditDrawerOpen(false)}
        entries={auditLogs as any}
        title="Purchase Order Audit Log"
      />
    </div>
  );
}
