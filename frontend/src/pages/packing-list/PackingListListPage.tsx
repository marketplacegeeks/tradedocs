// Packing List + Commercial Invoice list page — status-tab filtering, search, sortable columns.

import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, Package, Search, ArrowUp, ArrowDown, ArrowUpDown } from "lucide-react";

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

// Columns that can be sorted and the field they map to on a PackingList
type SortKey = "pl_number" | "pl_date" | "ci_number" | "pi_number" | "consignee" | "status" | "created_by";

const COLUMNS: { label: string; key: SortKey | null }[] = [
  { label: "PL Number",   key: "pl_number" },
  { label: "CI Number",   key: "ci_number" },
  { label: "PI Number",   key: "pi_number" },
  { label: "Consignee",   key: "consignee" },
  { label: "PL Date",     key: "pl_date" },
  { label: "Status",      key: "status" },
  { label: "Created By",  key: "created_by" },
  { label: "",            key: null },
];

function getSortValue(pl: PackingList, key: SortKey): string {
  switch (key) {
    case "pl_number":  return pl.pl_number ?? "";
    case "pl_date":    return pl.pl_date ?? "";
    case "ci_number":  return pl.ci_number ?? "";
    case "pi_number":  return pl.pi_number_display ?? "";
    case "consignee":  return pl.consignee_name ?? "";
    case "status":     return pl.status ?? "";
    case "created_by": return pl.created_by_name ?? "";
  }
}

// ---- Page ------------------------------------------------------------------

export default function PackingListListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [activeStatus, setActiveStatus] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("pl_date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const canCreate = user?.role === ROLES.MAKER || user?.role === ROLES.COMPANY_ADMIN || user?.role === ROLES.SUPER_ADMIN;

  const { data: packingLists = [], isLoading } = useQuery({
    queryKey: ["packing-lists", activeStatus],
    queryFn: () => listPackingLists(activeStatus ? { status: activeStatus } : undefined),
  });

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  const displayed = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const filtered = q
      ? packingLists.filter((pl) =>
          (pl.pl_number ?? "").toLowerCase().includes(q) ||
          (pl.ci_number ?? "").toLowerCase().includes(q) ||
          (pl.pi_number_display ?? "").toLowerCase().includes(q) ||
          (pl.consignee_name ?? "").toLowerCase().includes(q) ||
          (pl.created_by_name ?? "").toLowerCase().includes(q) ||
          DOCUMENT_STATUS_LABELS[pl.status]?.toLowerCase().includes(q)
        )
      : packingLists;

    return [...filtered].sort((a, b) => {
      const cmp = getSortValue(a, sortKey).localeCompare(getSortValue(b, sortKey));
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [packingLists, searchQuery, sortKey, sortDir]);

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
            {displayed.length} of {packingLists.length} document{packingLists.length !== 1 ? "s" : ""}
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

      {/* Search bar */}
      <div style={{ marginBottom: 12, position: "relative", maxWidth: 360 }}>
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
          placeholder="Search by PL number, CI number, consignee…"
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
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 800 }}>
            <thead>
              <tr style={{ background: "var(--bg-base)" }}>
                {COLUMNS.map((col) => (
                  <th
                    key={col.label}
                    onClick={col.key ? () => handleSort(col.key!) : undefined}
                    style={{
                      padding: "12px 16px",
                      textAlign: "left",
                      fontFamily: "var(--font-body)",
                      fontSize: 11,
                      fontWeight: 600,
                      color: col.key && sortKey === col.key ? "var(--primary)" : "var(--text-muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                      borderBottom: "1px solid var(--border-light)",
                      whiteSpace: "nowrap",
                      cursor: col.key ? "pointer" : "default",
                      userSelect: "none",
                    }}
                  >
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                      {col.label}
                      {col.key && (
                        sortKey === col.key ? (
                          sortDir === "asc"
                            ? <ArrowUp size={11} strokeWidth={2.5} />
                            : <ArrowDown size={11} strokeWidth={2.5} />
                        ) : (
                          <ArrowUpDown size={11} strokeWidth={1.8} style={{ opacity: 0.35 }} />
                        )
                      )}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td
                    colSpan={8}
                    style={{ padding: "48px 16px", textAlign: "center", fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}
                  >
                    Loading…
                  </td>
                </tr>
              ) : displayed.length === 0 ? (
                <tr>
                  <td colSpan={8}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "48px 16px", gap: 12 }}>
                      <div style={{ width: 48, height: 48, borderRadius: 12, background: "var(--pastel-blue)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <Package size={22} color="var(--pastel-blue-text)" strokeWidth={1.5} />
                      </div>
                      <p style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                        No Packing Lists
                      </p>
                      <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                        {searchQuery ? "No documents match your search." : canCreate ? "Create your first PL + CI to get started." : "No documents match the current filter."}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                displayed.map((pl) => (
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
