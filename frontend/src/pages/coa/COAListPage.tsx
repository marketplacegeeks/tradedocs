// Certificate of Analysis list page.
// Shows all COAs with status tabs, search, and a link to each detail page.

import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, FlaskConical, Search } from "lucide-react";

import { listCOAs } from "../../api/coa";
import type { COA } from "../../api/coa";
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

const tdStyle: React.CSSProperties = {
  padding: "14px 16px",
  borderBottom: "1px solid var(--border-light)",
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-secondary)",
};

// ---- Page ------------------------------------------------------------------

export default function COAListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [activeStatus, setActiveStatus] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const canCreate =
    user?.role === ROLES.MAKER ||
    user?.role === ROLES.COMPANY_ADMIN ||
    user?.role === ROLES.SUPER_ADMIN;

  // Fetch all COAs — filtering by status when a tab is active
  const queryParams = activeStatus ? { status: activeStatus } : undefined;
  const { data, isLoading } = useQuery({
    queryKey: ["coas", activeStatus],
    queryFn: () => listCOAs(queryParams).then((r) => r.data),
  });

  const coas: COA[] = data ?? [];

  // Client-side search by COA number or batch number
  const displayed = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return coas;
    return coas.filter(
      (c) =>
        c.coa_number.toLowerCase().includes(q) ||
        c.batch_number.toLowerCase().includes(q) ||
        c.product_name.toLowerCase().includes(q) ||
        c.customer_name.toLowerCase().includes(q)
    );
  }, [coas, searchQuery]);

  function handleStatusChange(key: string) {
    setActiveStatus(key);
    setSearchQuery("");
  }

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
            Certificate of Analysis
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            {coas.length} certificate{coas.length !== 1 ? "s" : ""}
            {activeStatus ? ` · ${DOCUMENT_STATUS_LABELS[activeStatus] ?? activeStatus}` : ""}
          </p>
        </div>
        {canCreate && (
          <button
            onClick={() => navigate("/coas/new")}
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
            New COA
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
              onClick={() => handleStatusChange(tab.key)}
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

      {/* Search bar */}
      <div style={{ marginBottom: 12, position: "relative", maxWidth: 400 }}>
        <Search
          size={15}
          strokeWidth={1.8}
          style={{
            position: "absolute",
            left: 11,
            top: "50%",
            transform: "translateY(-50%)",
            color: "var(--text-muted)",
            pointerEvents: "none",
          }}
        />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by COA number, batch number, product…"
          style={{
            width: "100%",
            background: "var(--bg-surface)",
            border: "1px solid var(--border-medium)",
            borderRadius: 8,
            padding: "8px 12px 8px 34px",
            fontFamily: "var(--font-body)",
            fontSize: 13,
            color: "var(--text-primary)",
            outline: "none",
            boxSizing: "border-box",
          }}
        />
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
          <table
            style={{ width: "100%", borderCollapse: "collapse", minWidth: 750 }}
            aria-label="Certificate of Analysis"
          >
            <thead>
              <tr style={{ background: "var(--bg-base)" }}>
                {["COA Number", "Product", "Customer", "Batch Number", "Date of Manufacture", "Status", ""].map(
                  (label) => (
                    <th
                      key={label}
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
                      {label}
                    </th>
                  )
                )}
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
              ) : displayed.length === 0 ? (
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
                        <FlaskConical size={22} color="var(--pastel-blue-text)" strokeWidth={1.5} />
                      </div>
                      <p
                        style={{
                          fontFamily: "var(--font-heading)",
                          fontSize: 15,
                          fontWeight: 600,
                          color: "var(--text-primary)",
                          margin: 0,
                        }}
                      >
                        No Certificates of Analysis
                      </p>
                      <p
                        style={{
                          fontFamily: "var(--font-body)",
                          fontSize: 13,
                          color: "var(--text-muted)",
                          margin: 0,
                        }}
                      >
                        {searchQuery
                          ? "No COAs match your search."
                          : canCreate
                          ? "Create your first COA to get started."
                          : "No COAs match the current filter."}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                displayed.map((coa) => (
                  <COARow
                    key={coa.id}
                    coa={coa}
                    canEdit={
                      (coa.status === DOCUMENT_STATUS.DRAFT ||
                        coa.status === DOCUMENT_STATUS.REWORK) &&
                      (user?.role === ROLES.MAKER ||
                        user?.role === ROLES.COMPANY_ADMIN ||
                        user?.role === ROLES.SUPER_ADMIN)
                    }
                    onView={() => navigate(`/coas/${coa.id}`)}
                    onEdit={() => navigate(`/coas/${coa.id}/edit`)}
                  />
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

function COARow({
  coa,
  canEdit,
  onView,
  onEdit,
}: {
  coa: COA;
  canEdit: boolean;
  onView: () => void;
  onEdit: () => void;
}) {
  return (
    <tr
      onClick={onView}
      style={{ cursor: "pointer", transition: "background 0.12s ease" }}
      onMouseEnter={(e) =>
        ((e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)")
      }
      onMouseLeave={(e) =>
        ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")
      }
    >
      <td style={tdStyle}>
        <span
          style={{
            fontFamily: "var(--font-heading)",
            fontWeight: 600,
            fontSize: 13,
            color: "var(--text-primary)",
          }}
        >
          {coa.coa_number}
        </span>
      </td>
      <td style={tdStyle}>
        {coa.product_name} — {coa.grade}
      </td>
      <td style={tdStyle}>{coa.customer_name}</td>
      <td style={tdStyle}>{coa.batch_number}</td>
      <td style={tdStyle}>{coa.date_of_manufacture}</td>
      <td style={tdStyle}>
        <span className={DOCUMENT_STATUS_CHIP[coa.status] ?? "chip-blue"}>
          {DOCUMENT_STATUS_LABELS[coa.status] ?? coa.status}
        </span>
      </td>
      <td style={{ ...tdStyle, textAlign: "right" }}>
        <div
          style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}
          onClick={(e) => e.stopPropagation()}
        >
          {canEdit && (
            <button
              onClick={onEdit}
              style={{
                padding: "4px 10px",
                background: "transparent",
                border: "1px solid var(--border-medium)",
                borderRadius: 6,
                fontFamily: "var(--font-body)",
                fontSize: 12,
                color: "var(--text-secondary)",
                cursor: "pointer",
              }}
            >
              Edit
            </button>
          )}
          <span style={{ color: "var(--primary)", fontFamily: "var(--font-body)", fontSize: 13 }}>
            View →
          </span>
        </div>
      </td>
    </tr>
  );
}
