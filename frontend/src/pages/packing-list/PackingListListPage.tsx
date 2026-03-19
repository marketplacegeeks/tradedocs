// Packing List list page — FR-14M.
// Shows all PL+CI documents in a table; Maker/Admin can create new ones.

import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Select } from "antd";
import { Plus, FileText } from "lucide-react";
import { useState } from "react";

import { listPackingLists } from "../../api/packingLists";
import { useAuth } from "../../store/AuthContext";
import {
  DOCUMENT_STATUS,
  DOCUMENT_STATUS_CHIP,
  DOCUMENT_STATUS_LABELS,
  ROLES,
} from "../../utils/constants";

// ---- Styles -----------------------------------------------------------------

const PAGE: React.CSSProperties = {
  padding: 32,
  background: "var(--bg-base)",
  minHeight: "100vh",
};

const HEADER_ROW: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  marginBottom: 24,
};

const PAGE_TITLE: React.CSSProperties = {
  fontFamily: "var(--font-heading)",
  fontSize: 22,
  fontWeight: 700,
  color: "var(--text-primary)",
  margin: 0,
};

const CARD: React.CSSProperties = {
  background: "var(--bg-surface)",
  borderRadius: 14,
  border: "1px solid var(--border-light)",
  boxShadow: "var(--shadow-card)",
  overflow: "hidden",
};

const TH: React.CSSProperties = {
  padding: "12px 16px",
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
  padding: "14px 16px",
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-secondary)",
  borderBottom: "1px solid var(--border-light)",
};

const BTN_PRIMARY: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "9px 18px",
  borderRadius: 8,
  border: "none",
  background: "var(--primary)",
  color: "#fff",
  fontFamily: "var(--font-body)",
  fontSize: 13,
  fontWeight: 500,
  cursor: "pointer",
};

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
      padding: "3px 10px",
      borderRadius: 999,
      fontFamily: "var(--font-body)",
      fontSize: 11,
      fontWeight: 600,
      display: "inline-block",
    }}>
      {label}
    </span>
  );
}

// ---- Page -------------------------------------------------------------------

export default function PackingListListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  const canCreate = user?.role === ROLES.MAKER || user?.role === ROLES.COMPANY_ADMIN;

  const { data: packingLists = [], isLoading } = useQuery({
    queryKey: ["packing-lists", statusFilter],
    queryFn: () => listPackingLists(statusFilter ? { status: statusFilter } : undefined),
  });

  return (
    <div style={PAGE}>
      <div style={HEADER_ROW}>
        <h1 style={PAGE_TITLE}>Packing List</h1>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Select
            allowClear
            placeholder="Filter by status"
            style={{ width: 200 }}
            value={statusFilter}
            onChange={setStatusFilter}
            options={Object.entries(DOCUMENT_STATUS_LABELS).map(([k, v]) => ({
              value: k,
              label: v,
            }))}
          />
          {canCreate && (
            <button style={BTN_PRIMARY} onClick={() => navigate("/packing-lists/new")}>
              <Plus size={14} strokeWidth={2} />
              New Packing List
            </button>
          )}
        </div>
      </div>

      <div style={CARD}>
        {isLoading ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-body)" }}>
            Loading…
          </div>
        ) : packingLists.length === 0 ? (
          <div style={{ padding: 64, textAlign: "center" }}>
            <FileText size={40} color="var(--text-muted)" style={{ marginBottom: 12 }} />
            <p style={{ fontFamily: "var(--font-body)", color: "var(--text-muted)", fontSize: 14 }}>
              No packing lists found.
            </p>
            {canCreate && (
              <button style={{ ...BTN_PRIMARY, marginTop: 12 }} onClick={() => navigate("/packing-lists/new")}>
                <Plus size={14} strokeWidth={2} />
                Create your first Packing List
              </button>
            )}
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={TH}>PL Number</th>
                <th style={TH}>CI Number</th>
                <th style={TH}>PI Number</th>
                <th style={TH}>Consignee</th>
                <th style={TH}>PL Date</th>
                <th style={TH}>Status</th>
              </tr>
            </thead>
            <tbody>
              {packingLists.map((pl) => (
                <tr
                  key={pl.id}
                  style={{ cursor: "pointer" }}
                  onClick={() => navigate(`/packing-lists/${pl.id}`)}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-hover)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <td style={{ ...TD, fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-heading)" }}>
                    {pl.pl_number}
                  </td>
                  <td style={{ ...TD, color: "var(--text-secondary)" }}>{pl.ci_number ?? "—"}</td>
                  <td style={TD}>{pl.pi_number_display ?? "—"}</td>
                  <td style={TD}>{pl.consignee_name ?? "—"}</td>
                  <td style={TD}>{pl.pl_date}</td>
                  <td style={TD}>
                    <StatusChip status={pl.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
