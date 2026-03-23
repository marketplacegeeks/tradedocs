// Reports landing page (R-02 through R-07).
// Checker and Company Admin only — enforced by the route in App.tsx.
// One unified filter card at the top; each report portals its filter fields into it.

import { useState } from "react";
import { Select } from "antd";
import { BarChart2, Filter } from "lucide-react";

import R02ProformaInvoiceRegister from "./R02ProformaInvoiceRegister";
import R03ShipmentRegister from "./R03ShipmentRegister";
import R04CommoditySalesReport from "./R04CommoditySalesReport";
import R05ConsigneeBusinessSummary from "./R05ConsigneeBusinessSummary";
import R06PurchaseOrderRegister from "./R06PurchaseOrderRegister";

export const REPORTS = [
  { value: "R-02", label: "Proforma Invoice Register" },
  { value: "R-03", label: "Shipment Register" },
  { value: "R-04", label: "Commodity Sales Report" },
  { value: "R-05", label: "Consignee-wise Business Summary" },
  { value: "R-06", label: "Purchase Order Register" },
];

const IMPLEMENTED = new Set(["R-02", "R-03", "R-04", "R-05", "R-06"]);

const labelStyle: React.CSSProperties = {
  fontFamily: "var(--font-body)",
  fontSize: 12,
  fontWeight: 500,
  color: "var(--text-secondary)",
  marginBottom: 4,
};

export default function ReportsPage() {
  const [selectedReport, setSelectedReport] = useState<string | undefined>(undefined);

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <h1
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: 22,
            fontWeight: 700,
            color: "var(--text-primary)",
            marginBottom: 4,
          }}
        >
          Reports
        </h1>
        <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
          Select a report to view and export data.
        </p>
      </div>

      {/* ── Unified filter card ─────────────────────────────────────────────── */}
      <div
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border-light)",
          borderRadius: 14,
          padding: "20px 24px",
          boxShadow: "var(--shadow-card)",
          marginBottom: 20,
        }}
      >
        {/* Header */}
        <div
          style={{
            fontFamily: "var(--font-body)",
            fontSize: 13,
            fontWeight: 600,
            color: "var(--text-secondary)",
            marginBottom: 14,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <Filter size={14} strokeWidth={1.5} />
          Filters
        </div>

        {/* Filter grid — report selector always shown; active report portals its fields here */}
        <div
          id="report-filter-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
            gap: "12px 16px",
          }}
        >
          <div>
            <div style={labelStyle}>Report</div>
            <Select
              placeholder="Choose a report…"
              style={{ width: "100%" }}
              value={selectedReport}
              onChange={setSelectedReport}
              options={REPORTS}
            />
          </div>
          {/* Each active report component portals its filter fields into this grid */}
        </div>

        {/* Apply / Reset buttons are portaled here by each active report */}
        <div id="report-filter-buttons" />
      </div>

      {/* ── Report tables (each renders null when not active) ───────────────── */}
      <R02ProformaInvoiceRegister selectedReport={selectedReport} />
      <R03ShipmentRegister selectedReport={selectedReport} />
      <R04CommoditySalesReport selectedReport={selectedReport} />
      <R05ConsigneeBusinessSummary selectedReport={selectedReport} />
      <R06PurchaseOrderRegister selectedReport={selectedReport} />

      {/* Coming soon placeholder */}
      {selectedReport && !IMPLEMENTED.has(selectedReport) && (
        <div
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-light)",
            borderRadius: 14,
            padding: "24px",
            boxShadow: "var(--shadow-card)",
          }}
        >
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: 14,
              color: "var(--text-muted)",
              margin: 0,
              textAlign: "center",
              padding: "40px 0",
            }}
          >
            {REPORTS.find((r) => r.value === selectedReport)?.label} — coming soon.
          </p>
        </div>
      )}

      {/* Empty state when no report selected */}
      {!selectedReport && (
        <div
          style={{
            marginTop: 40,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            padding: "60px 0",
            gap: 12,
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              background: "var(--pastel-blue)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <BarChart2 size={26} strokeWidth={1.5} color="var(--pastel-blue-text)" />
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
            No report selected
          </p>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: 13,
              color: "var(--text-muted)",
              margin: 0,
            }}
          >
            Pick a report from the dropdown above to get started.
          </p>
        </div>
      )}
    </div>
  );
}
