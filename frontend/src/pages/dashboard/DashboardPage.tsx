// Dashboard — post-login landing page.
// Shows real document counts and the 10 most recent workflow actions.

import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { FileText, Package, ShoppingBag, Clock } from "lucide-react";

import { useAuth } from "../../store/AuthContext";
import { getDashboardData } from "../../api/dashboard";
import {
  DOCUMENT_STATUS_CHIP,
  DOCUMENT_STATUS_LABELS,
} from "../../utils/constants";

// ---- Helpers ---------------------------------------------------------------

/** Format an ISO timestamp as a relative label: "2 hours ago", "3 days ago" etc. */
function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

/** Human-readable document type label. */
function docTypeLabel(type: string): string {
  const map: Record<string, string> = {
    proforma_invoice: "Proforma Invoice",
    packing_list: "Packing List",
    commercial_invoice: "Commercial Invoice",
    purchase_order: "Purchase Order",
  };
  return map[type] ?? type.replace(/_/g, " ");
}

// ---- Stat Card -------------------------------------------------------------

interface StatCardProps {
  label: string;
  value: number | undefined;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
  loading: boolean;
}

function StatCard({ label, value, icon: Icon, iconBg, iconColor, loading }: StatCardProps) {
  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-light)",
        borderRadius: 14,
        padding: "20px 24px",
        boxShadow: "var(--shadow-card)",
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: iconBg,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 16,
        }}
      >
        <Icon size={20} strokeWidth={1.5} color={iconColor} />
      </div>

      <div
        style={{
          fontFamily: "var(--font-heading)",
          fontSize: 32,
          fontWeight: 700,
          color: "var(--text-primary)",
          lineHeight: 1,
          marginBottom: 6,
        }}
      >
        {loading ? (
          <span style={{ display: "inline-block", width: 48, height: 32, borderRadius: 6, background: "var(--bg-hover)", verticalAlign: "middle" }} />
        ) : (
          value ?? 0
        )}
      </div>

      <div
        style={{
          fontFamily: "var(--font-body)",
          fontSize: 14,
          fontWeight: 500,
          color: "var(--text-primary)",
        }}
      >
        {label}
      </div>
    </div>
  );
}

// ---- Page ------------------------------------------------------------------

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboardData,
    // Refresh every 60 seconds so counts stay fresh without manual reload
    refetchInterval: 60_000,
  });

  const counts = data?.counts;
  const activity = data?.recent_activity ?? [];

  const KPI_CARDS = [
    {
      label: "Proforma Invoices",
      value: counts?.proforma_invoices,
      icon: FileText,
      iconBg: "var(--pastel-blue)",
      iconColor: "var(--pastel-blue-text)",
    },
    {
      label: "Packing Lists",
      value: counts?.packing_lists,
      icon: Package,
      iconBg: "var(--pastel-green)",
      iconColor: "var(--pastel-green-text)",
    },
    {
      label: "Purchase Orders",
      value: counts?.purchase_orders,
      icon: ShoppingBag,
      iconBg: "var(--pastel-purple)",
      iconColor: "var(--pastel-purple-text)",
    },
    {
      label: "Pending Approvals",
      value: counts?.pending_approvals,
      icon: Clock,
      iconBg: "var(--pastel-yellow)",
      iconColor: "var(--pastel-yellow-text)",
    },
  ];

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 28 }}>
        <h1
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: 22,
            fontWeight: 700,
            color: "var(--text-primary)",
            marginBottom: 4,
          }}
        >
          Welcome back{user?.firstName ? `, ${user.firstName}` : ""}
        </h1>
        <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
          Here's an overview of your trade documents.
        </p>
      </div>

      {/* KPI grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 16,
          marginBottom: 28,
        }}
        className="stats-grid"
      >
        {KPI_CARDS.map((card, i) => (
          <div key={card.label} className="card-animate" style={{ animationDelay: `${i * 0.05 + 0.05}s` }}>
            <StatCard {...card} loading={isLoading} />
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border-light)",
          borderRadius: 14,
          padding: "20px 24px",
          boxShadow: "var(--shadow-card)",
        }}
      >
        <h3
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: 16,
            fontWeight: 600,
            color: "var(--text-primary)",
            marginBottom: 16,
          }}
        >
          Recent Activity
        </h3>

        {isLoading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                style={{
                  height: 52,
                  borderRadius: 8,
                  background: "var(--bg-hover)",
                  opacity: 1 - i * 0.18,
                }}
              />
            ))}
          </div>
        )}

        {!isLoading && activity.length === 0 && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 0", gap: 12 }}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 14,
                background: "var(--pastel-blue)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Clock size={22} strokeWidth={1.5} color="var(--pastel-blue-text)" />
            </div>
            <p style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
              No recent activity
            </p>
            <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
              Document activity will appear here once documents are created.
            </p>
          </div>
        )}

        {!isLoading && activity.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column" }}>
            {activity.map((entry, idx) => (
              <div
                key={entry.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  padding: "12px 0",
                  borderBottom: idx < activity.length - 1 ? "1px solid var(--border-light)" : "none",
                }}
              >
                {/* Status chip / action badge */}
                <span
                  className={DOCUMENT_STATUS_CHIP[entry.to_status] ?? "chip-blue"}
                  style={{ flexShrink: 0, minWidth: 110, textAlign: "center" }}
                >
                  {DOCUMENT_STATUS_LABELS[entry.to_status] ?? entry.to_status}
                </span>

                {/* Document link + action description */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <button
                    onClick={() => navigate(`${entry.url_prefix}/${entry.document_id}`)}
                    style={{
                      background: "none",
                      border: "none",
                      padding: 0,
                      cursor: "pointer",
                      fontFamily: "var(--font-body)",
                      fontSize: 13,
                      fontWeight: 600,
                      color: "var(--primary)",
                      textDecoration: "none",
                    }}
                  >
                    {entry.document_number}
                  </button>
                  <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
                    {" "}· {docTypeLabel(entry.document_type)} {entry.action_label.toLowerCase()} by{" "}
                    <strong style={{ fontWeight: 500, color: "var(--text-primary)" }}>{entry.performed_by_name}</strong>
                  </span>
                </div>

                {/* Timestamp */}
                <span
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 12,
                    color: "var(--text-muted)",
                    flexShrink: 0,
                    whiteSpace: "nowrap",
                  }}
                >
                  {timeAgo(entry.performed_at)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
