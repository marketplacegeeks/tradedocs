// Proforma Invoice list page — status-tab filtering, design system table.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, FileText, Download } from "lucide-react";

import { listProformaInvoices } from "../../api/proformaInvoices";
import type { ProformaInvoice } from "../../api/proformaInvoices";
import { useAuth } from "../../store/AuthContext";
import {
  ROLES,
  DOCUMENT_STATUS,
  DOCUMENT_STATUS_LABELS,
  DOCUMENT_STATUS_CHIP,
} from "../../utils/constants";

// ---- Status tabs -----------------------------------------------------------

const STATUS_TABS = [
  { key: "", label: "All" },
  { key: DOCUMENT_STATUS.DRAFT, label: "Draft" },
  { key: DOCUMENT_STATUS.PENDING_APPROVAL, label: "Pending Approval" },
  { key: DOCUMENT_STATUS.APPROVED, label: "Approved" },
  { key: DOCUMENT_STATUS.REWORK, label: "Rework" },
  { key: DOCUMENT_STATUS.PERMANENTLY_REJECTED, label: "Permanently Rejected" },
];

// ---- Page ------------------------------------------------------------------

export default function ProformaInvoiceListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeStatus, setActiveStatus] = useState("");

  const canCreate = user?.role === ROLES.MAKER || user?.role === ROLES.COMPANY_ADMIN;

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ["proforma-invoices", activeStatus],
    queryFn: () => listProformaInvoices(activeStatus ? { status: activeStatus } : {}),
  });

  return (
    <div>
      {/* Page header */}
      <div
        className="page-header"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 24,
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: 22,
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: 4,
            }}
          >
            Proforma Invoices
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            {invoices.length} invoice{invoices.length !== 1 ? "s" : ""}
            {activeStatus ? ` · ${DOCUMENT_STATUS_LABELS[activeStatus] ?? activeStatus}` : ""}
          </p>
        </div>
        {canCreate && (
          <button
            onClick={() => navigate("/proforma-invoices/new")}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              background: "var(--primary)",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "9px 18px",
              fontFamily: "var(--font-body)",
              fontSize: 14,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            <Plus size={16} strokeWidth={2} />
            New Proforma Invoice
          </button>
        )}
      </div>

      {/* Status tabs */}
      <div
        style={{
          display: "flex",
          gap: 4,
          marginBottom: 16,
          borderBottom: "1px solid var(--border-light)",
          overflowX: "auto",
        }}
      >
        {STATUS_TABS.map((tab) => {
          const isActive = tab.key === activeStatus;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveStatus(tab.key)}
              style={{
                padding: "9px 16px",
                border: "none",
                borderBottom: isActive ? "2px solid var(--primary)" : "2px solid transparent",
                background: "transparent",
                fontFamily: "var(--font-body)",
                fontSize: 13,
                fontWeight: isActive ? 600 : 400,
                color: isActive ? "var(--primary)" : "var(--text-secondary)",
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "all 0.15s ease",
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div
        style={{
          background: "var(--bg-surface)",
          borderRadius: 14,
          border: "1px solid var(--border-light)",
          boxShadow: "var(--shadow-card)",
          overflow: "hidden",
        }}
      >
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
            <thead>
              <tr style={{ background: "var(--bg-base)" }}>
                {["PI Number", "Date", "Exporter", "Consignee", "Status", "Created By", ""].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "12px 16px",
                      textAlign: "left",
                      fontFamily: "var(--font-body)",
                      fontSize: 11,
                      fontWeight: 600,
                      color: "var(--text-muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                      borderBottom: "1px solid var(--border-light)",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td
                    colSpan={7}
                    style={{
                      padding: "48px 16px",
                      textAlign: "center",
                      fontFamily: "var(--font-body)",
                      fontSize: 14,
                      color: "var(--text-muted)",
                    }}
                  >
                    Loading…
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        padding: "48px 16px",
                        gap: 12,
                      }}
                    >
                      <div
                        style={{
                          width: 48,
                          height: 48,
                          borderRadius: 12,
                          background: "var(--pastel-blue)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        <FileText size={22} color="var(--pastel-blue-text)" strokeWidth={1.5} />
                      </div>
                      <p style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                        No Proforma Invoices
                      </p>
                      <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                        {canCreate ? "Create your first invoice to get started." : "No invoices match the current filter."}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                invoices.map((pi) => (
                  <PIRow key={pi.id} pi={pi} onClick={() => navigate(`/proforma-invoices/${pi.id}`)} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ---- Table row -------------------------------------------------------------

function PIRow({ pi, onClick }: { pi: ProformaInvoice; onClick: () => void }) {
  return (
    <tr
      onClick={onClick}
      style={{ cursor: "pointer", transition: "background 0.12s ease" }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)")}
      onMouseLeave={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")}
    >
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: 13, color: "var(--text-primary)" }}>
          {pi.pi_number}
        </span>
      </td>
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {pi.pi_date}
        </span>
      </td>
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {pi.exporter_name}
        </span>
      </td>
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {pi.consignee_name}
        </span>
      </td>
      <td style={tdStyle}>
        <span className={DOCUMENT_STATUS_CHIP[pi.status] ?? "chip-blue"}>
          {DOCUMENT_STATUS_LABELS[pi.status] ?? pi.status}
        </span>
      </td>
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {pi.created_by_name}
        </span>
      </td>
      <td style={{ ...tdStyle, textAlign: "right" }}>
        <span style={{ color: "var(--primary)", fontFamily: "var(--font-body)", fontSize: 13 }}>
          View →
        </span>
      </td>
    </tr>
  );
}

const tdStyle: React.CSSProperties = {
  padding: "14px 16px",
  borderBottom: "1px solid var(--border-light)",
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-secondary)",
};
