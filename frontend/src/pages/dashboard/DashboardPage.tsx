// Dashboard placeholder — post-login landing page.
// KPI stat cards with staggered fade-up animation.
// Will be populated with real counts in a future sprint.

import { FileText, Package, DollarSign, Clock } from "lucide-react";
import { useAuth } from "../../store/AuthContext";

// ---- KPI card data --------------------------------------------------------

const KPI_CARDS = [
  {
    label: "Proforma Invoices",
    value: "—",
    sub: "Coming soon",
    icon: FileText,
    iconBg: "var(--pastel-blue)",
    iconColor: "var(--pastel-blue-text)",
  },
  {
    label: "Packing Lists",
    value: "—",
    sub: "Coming soon",
    icon: Package,
    iconBg: "var(--pastel-green)",
    iconColor: "var(--pastel-green-text)",
  },
  {
    label: "Commercial Invoices",
    value: "—",
    sub: "Coming soon",
    icon: DollarSign,
    iconBg: "var(--pastel-purple)",
    iconColor: "var(--pastel-purple-text)",
  },
  {
    label: "Pending Approvals",
    value: "—",
    sub: "Coming soon",
    icon: Clock,
    iconBg: "var(--pastel-yellow)",
    iconColor: "var(--pastel-yellow-text)",
  },
];

// ---- Stat Card component --------------------------------------------------

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  iconBg,
  iconColor,
}: typeof KPI_CARDS[0]) {
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
      {/* Icon */}
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

      {/* Value */}
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
        {value}
      </div>

      {/* Label */}
      <div
        style={{
          fontFamily: "var(--font-body)",
          fontSize: 14,
          fontWeight: 500,
          color: "var(--text-primary)",
          marginBottom: 4,
        }}
      >
        {label}
      </div>

      {/* Sub */}
      <div
        style={{
          fontFamily: "var(--font-body)",
          fontSize: 12,
          color: "var(--text-muted)",
        }}
      >
        {sub}
      </div>
    </div>
  );
}

// ---- Page -----------------------------------------------------------------

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div>
      {/* Page header */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          marginBottom: 28,
          flexWrap: "wrap",
          gap: 12,
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
            Welcome back{user?.firstName ? `, ${user.firstName}` : ""}
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            Here's an overview of your trade documents.
          </p>
        </div>
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
            <StatCard {...card} />
          </div>
        ))}
      </div>

      {/* Placeholder activity area */}
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
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            padding: "40px 0",
            gap: 12,
          }}
        >
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
          <p
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: 15,
              fontWeight: 600,
              color: "var(--text-primary)",
              margin: 0,
            }}
          >
            No recent activity
          </p>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: 13,
              color: "var(--text-muted)",
              margin: 0,
            }}
          >
            Document activity will appear here once documents are created.
          </p>
        </div>
      </div>
    </div>
  );
}
