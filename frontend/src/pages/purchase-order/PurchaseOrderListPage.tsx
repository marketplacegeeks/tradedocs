// Purchase Order list page (FR-PO-14).
// All authenticated roles see all POs.
// Supports status filter tabs, PO number search, vendor filter, and date range.

import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Select } from "antd";
import { Plus, ShoppingBag, Search, ArrowUp, ArrowDown, ArrowUpDown } from "lucide-react";

import { listPurchaseOrders } from "../../api/purchaseOrders";
import type { PurchaseOrder } from "../../api/purchaseOrders";
import { listOrganisations } from "../../api/organisations";
import { useAuth } from "../../store/AuthContext";
import {
  ROLES,
  DOCUMENT_STATUS,
  DOCUMENT_STATUS_LABELS,
  DOCUMENT_STATUS_CHIP,
  TRANSACTION_TYPE_LABELS,
} from "../../utils/constants";

// ---- Status tabs ------------------------------------------------------------

const STATUS_TABS = [
  { key: "", label: "All" },
  { key: DOCUMENT_STATUS.DRAFT, label: "Draft" },
  { key: DOCUMENT_STATUS.PENDING_APPROVAL, label: "Pending Approval" },
  { key: DOCUMENT_STATUS.APPROVED, label: "Approved" },
  { key: DOCUMENT_STATUS.REWORK, label: "Rework" },
  { key: DOCUMENT_STATUS.PERMANENTLY_REJECTED, label: "Permanently Rejected" },
];

// ---- Sortable columns -------------------------------------------------------

type SortKey = "po_number" | "po_date" | "vendor_name" | "total" | "status" | "created_by_name";

const COLUMNS: { label: string; key: SortKey | null }[] = [
  { label: "PO Number",   key: "po_number" },
  { label: "PO Date",     key: "po_date" },
  { label: "Vendor",      key: "vendor_name" },
  { label: "Currency",    key: null },
  { label: "Total",       key: "total" },
  { label: "Status",      key: "status" },
  { label: "",            key: null },
];

function getSortValue(po: PurchaseOrder, key: SortKey): string | number {
  switch (key) {
    case "po_number":      return po.po_number ?? "";
    case "po_date":        return po.po_date ?? "";
    case "vendor_name":    return po.vendor_name ?? "";
    case "total":          return parseFloat(po.total ?? "0");
    case "status":         return po.status ?? "";
    case "created_by_name": return po.created_by_name ?? "";
  }
}

// ---- Helpers ----------------------------------------------------------------

function formatDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function formatTotal(value: string | undefined): string {
  if (!value) return "0.00";
  return parseFloat(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ---- Page -------------------------------------------------------------------

export default function PurchaseOrderListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [activeStatus, setActiveStatus] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [vendorFilter, setVendorFilter] = useState<number | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("po_date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  // All roles see all POs — no created_by filter applied
  const apiFilters = useMemo(() => {
    const f: Record<string, unknown> = {};
    if (activeStatus) f.status = activeStatus;
    if (vendorFilter) f.vendor = vendorFilter;
    return f;
  }, [activeStatus, vendorFilter]);

  const { data: orders = [], isLoading } = useQuery({
    queryKey: ["purchase-orders", apiFilters],
    queryFn: () => listPurchaseOrders(apiFilters),
  });

  // Vendor dropdown options (VENDOR-tagged orgs only)
  const { data: vendors = [] } = useQuery({
    queryKey: ["organisations", "VENDOR"],
    queryFn: () => listOrganisations("VENDOR"),
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

    let list = orders;

    // Search by PO number
    if (q) {
      list = list.filter((po) => po.po_number.toLowerCase().includes(q));
    }

    // Date range filter (client-side)
    if (dateFrom) {
      list = list.filter((po) => po.po_date >= dateFrom);
    }
    if (dateTo) {
      list = list.filter((po) => po.po_date <= dateTo);
    }

    // Sort
    return [...list].sort((a, b) => {
      const av = getSortValue(a, sortKey);
      const bv = getSortValue(b, sortKey);
      const cmp =
        typeof av === "number" && typeof bv === "number"
          ? av - bv
          : String(av).localeCompare(String(bv));
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [orders, searchQuery, dateFrom, dateTo, sortKey, sortDir]);

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
            Purchase Orders
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            {displayed.length} of {orders.length} order{orders.length !== 1 ? "s" : ""}
            {activeStatus ? ` · ${DOCUMENT_STATUS_LABELS[activeStatus] ?? activeStatus}` : ""}
          </p>
        </div>
        <button
          onClick={() => navigate("/purchase-orders/new")}
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
          New Purchase Order
        </button>
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

      {/* Filters row */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 10,
          marginBottom: 16,
          alignItems: "center",
        }}
      >
        {/* PO number search */}
        <div style={{ position: "relative", flex: "1 1 220px", maxWidth: 280 }}>
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
            placeholder="Search by PO number…"
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

        {/* Vendor filter */}
        <Select
          allowClear
          placeholder="All vendors"
          value={vendorFilter ?? undefined}
          onChange={(v) => setVendorFilter(v ?? null)}
          style={{ width: 200, fontFamily: "var(--font-body)", fontSize: 13 }}
          options={vendors.map((v) => ({ value: v.id, label: v.name }))}
        />

        {/* Date from */}
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-medium)",
            borderRadius: 8,
            padding: "7px 10px",
            fontFamily: "var(--font-body)",
            fontSize: 13,
            color: "var(--text-primary)",
            outline: "none",
          }}
        />
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)" }}>to</span>
        {/* Date to */}
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-medium)",
            borderRadius: 8,
            padding: "7px 10px",
            fontFamily: "var(--font-body)",
            fontSize: 13,
            color: "var(--text-primary)",
            outline: "none",
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
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 750 }}>
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
                    colSpan={7}
                    style={{ padding: "48px 16px", textAlign: "center", fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}
                  >
                    Loading…
                  </td>
                </tr>
              ) : displayed.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "48px 16px", gap: 12 }}>
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
                        <ShoppingBag size={22} color="var(--pastel-blue-text)" strokeWidth={1.5} />
                      </div>
                      <p style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                        No Purchase Orders
                      </p>
                      <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                        {searchQuery
                          ? "No orders match your search."
                          : "Create your first purchase order to get started."}
                      </p>
                      <button
                        onClick={() => navigate("/purchase-orders/new")}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: 6,
                          background: "var(--primary)",
                          color: "#fff",
                          border: "none",
                          borderRadius: 8,
                          padding: "8px 16px",
                          fontFamily: "var(--font-body)",
                          fontSize: 13,
                          fontWeight: 500,
                          cursor: "pointer",
                        }}
                      >
                        <Plus size={14} strokeWidth={2} />
                        New Purchase Order
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                displayed.map((po) => (
                  <PORow
                    key={po.id}
                    po={po}
                    currentUserId={user?.id}
                    currentUserRole={user?.role}
                    onView={() => navigate(`/purchase-orders/${po.id}`)}
                    onEdit={() => navigate(`/purchase-orders/${po.id}/edit`)}
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

// ---- Table row --------------------------------------------------------------

function PORow({
  po,
  currentUserId,
  currentUserRole,
  onView,
  onEdit,
}: {
  po: PurchaseOrder;
  currentUserId: number | undefined;
  currentUserRole: string | undefined;
  onView: () => void;
  onEdit: () => void;
}) {
  const isOwner = po.created_by === currentUserId;
  const isEditable =
    (po.status === DOCUMENT_STATUS.DRAFT || po.status === DOCUMENT_STATUS.REWORK) &&
    (isOwner || currentUserRole === ROLES.COMPANY_ADMIN || currentUserRole === ROLES.SUPER_ADMIN);

  return (
    <tr
      style={{ transition: "background 0.12s ease", cursor: "default" }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)")}
      onMouseLeave={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")}
    >
      {/* PO Number */}
      <td style={tdStyle}>
        <button
          onClick={onView}
          style={{
            background: "none",
            border: "none",
            padding: 0,
            fontFamily: "var(--font-heading)",
            fontWeight: 600,
            fontSize: 13,
            color: "var(--primary)",
            cursor: "pointer",
          }}
        >
          {po.po_number}
        </button>
      </td>

      {/* PO Date */}
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {formatDate(po.po_date)}
        </span>
      </td>

      {/* Vendor */}
      <td style={tdStyle}>
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
          {po.vendor_name}
        </span>
      </td>

      {/* Currency */}
      <td style={tdStyle}>
        <span
          style={{
            display: "inline-block",
            background: "var(--pastel-blue)",
            color: "var(--pastel-blue-text)",
            borderRadius: 6,
            padding: "2px 8px",
            fontFamily: "var(--font-body)",
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: "0.02em",
          }}
        >
          {po.currency_code}
        </span>
      </td>

      {/* Total */}
      <td style={{ ...tdStyle, fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: 13, color: "var(--text-primary)" }}>
        {formatTotal(po.total)}
      </td>

      {/* Status */}
      <td style={tdStyle}>
        <span className={DOCUMENT_STATUS_CHIP[po.status] ?? "chip-blue"}>
          {DOCUMENT_STATUS_LABELS[po.status] ?? po.status}
        </span>
      </td>

      {/* Actions */}
      <td style={{ ...tdStyle, textAlign: "right" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          <button
            onClick={onView}
            style={{
              background: "none",
              border: "none",
              padding: 0,
              fontFamily: "var(--font-body)",
              fontSize: 13,
              color: "var(--primary)",
              cursor: "pointer",
            }}
          >
            View
          </button>
          {isEditable && (
            <button
              onClick={onEdit}
              style={{
                background: "none",
                border: "none",
                padding: 0,
                fontFamily: "var(--font-body)",
                fontSize: 13,
                color: "var(--text-muted)",
                cursor: "pointer",
              }}
            >
              Edit
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}

const tdStyle: React.CSSProperties = {
  padding: "14px 16px",
  borderBottom: "1px solid var(--border-light)",
};
