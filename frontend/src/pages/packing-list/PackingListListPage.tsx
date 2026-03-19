// Packing List + Commercial Invoice list page — FR-14M.
// Status tabs on top (same pattern as ProformaInvoiceListPage).

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, Package } from "lucide-react";

import { listPackingLists } from "../../api/packingLists";
import type { PackingList } from "../../api/packingLists";
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

export default function PackingListListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeStatus, setActiveStatus] = useState("");

  const canCreate = user?.role === ROLES.MAKER || user?.role === ROLES.COMPANY_ADMIN;

  const { data: packingLists = [], isLoading } = useQuery({
    queryKey: ["packing-lists", activeStatus],
    queryFn: () => listPackingLists(activeStatus ? { status: activeStatus } : undefined),
  });

  return (
    <div>
      {/* Page header */}
      <div
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
            Packing List &amp; Commercial Invoice
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            {packingLists.length} document{packingLists.length !== 1 ? "s" : ""}
            {activeStatus ? ` · ${DOCUMENT_STATUS_LABELS[activeStatus] ?? activeStatus}` : ""}
          </p>
        </div>
        {canCreate && (
          <button
            onClick={() => navigate("/packing-lists/new")}
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
            New Packing List & Commercial Invoice
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
                {["PL Number", "CI Number", "PI Number", "Consignee", "PL Date", "Status", "Created By", ""].map((h) => (
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
                    colSpan={8}
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
              ) : packingLists.length === 0 ? (
                <tr>
                  <td colSpan={8}>
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
                        <Package size={22} color="var(--pastel-blue-text)" strokeWidth={1.5} />
                      </div>
                      <p style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                        No Packing Lists
                      </p>
                      <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                        {canCreate ? "Create your first PL + CI to get started." : "No documents match the current filter."}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                packingLists.map((pl) => (
                  <PLRow key={pl.id} pl={pl} onClick={() => navigate(`/packing-lists/${pl.id}`)} />
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

function PLRow({ pl, onClick }: { pl: PackingList; onClick: () => void }) {
  return (
    <tr
      onClick={onClick}
      style={{ cursor: "pointer", transition: "background 0.12s ease" }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)")}
      onMouseLeave={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")}
    >
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: 13, color: "var(--text-primary)" }}>
          {pl.pl_number}
        </span>
      </td>
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {pl.ci_number ?? "—"}
        </span>
      </td>
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {pl.pi_number_display ?? "—"}
        </span>
      </td>
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {pl.consignee_name ?? "—"}
        </span>
      </td>
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {pl.pl_date}
        </span>
      </td>
      <td style={tdStyle}>
        <span className={DOCUMENT_STATUS_CHIP[pl.status] ?? "chip-blue"}>
          {DOCUMENT_STATUS_LABELS[pl.status] ?? pl.status}
        </span>
      </td>
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {pl.created_by_name}
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
