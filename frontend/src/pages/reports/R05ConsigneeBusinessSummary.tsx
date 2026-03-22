// R-05 — Consignee-wise Business Summary
// One aggregated row per consignee showing PI/CI counts and revenue totals.
// Columns and filters inferred from reports.md §R-05 description.
// Accessible to Checker and Company Admin only (enforced by ProtectedRoute in App.tsx).

import { useState, useMemo } from "react";
import { createPortal } from "react-dom";
import { useQuery } from "@tanstack/react-query";
import { DatePicker, Select, Button, Table } from "antd";
import { Download } from "lucide-react";
import dayjs from "dayjs";

import { getConsigneeBusinessSummary } from "../../api/reports";
import type { ConsigneeSummaryRow } from "../../api/reports";
import { listOrganisations } from "../../api/organisations";
import {
  DOCUMENT_STATUS,
  DOCUMENT_STATUS_LABELS,
} from "../../utils/constants";

const { RangePicker } = DatePicker;

// ---- Props ------------------------------------------------------------------

interface Props {
  selectedReport: string | undefined;
}

// ---- Filter state -----------------------------------------------------------

interface Filters {
  dateFrom: string;
  dateTo: string;
  doc_type: string;
  status: string;
  consignee: string;
}

const EMPTY_FILTERS: Filters = {
  dateFrom: "",
  dateTo: "",
  doc_type: "",
  status: "",
  consignee: "",
};

// ---- Static options ---------------------------------------------------------

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: DOCUMENT_STATUS.DRAFT, label: DOCUMENT_STATUS_LABELS.DRAFT },
  { value: DOCUMENT_STATUS.PENDING_APPROVAL, label: DOCUMENT_STATUS_LABELS.PENDING_APPROVAL },
  { value: DOCUMENT_STATUS.APPROVED, label: DOCUMENT_STATUS_LABELS.APPROVED },
  { value: DOCUMENT_STATUS.REWORK, label: DOCUMENT_STATUS_LABELS.REWORK },
  { value: DOCUMENT_STATUS.PERMANENTLY_REJECTED, label: DOCUMENT_STATUS_LABELS.PERMANENTLY_REJECTED },
];

const DOC_TYPE_OPTIONS = [
  { value: "", label: "PI + CI (All)" },
  { value: "PI", label: "Proforma Invoice (PI)" },
  { value: "CI", label: "Commercial Invoice (CI)" },
];

// ---- CSV export -------------------------------------------------------------

function exportToCsv(rows: ConsigneeSummaryRow[]) {
  const today = dayjs().format("DDMMYYYY");
  const filename = `${today}_ConsigneeBusinessSummary.csv`;

  const headers = [
    "Consignee",
    "PI Count",
    "CI Count",
    "Total PI Value (USD)",
    "Total CI Value (USD)",
    "Combined Total (USD)",
    "Latest Document Date",
  ];

  const escape = (val: string | number | null | undefined) => {
    if (val == null) return "";
    const str = String(val);
    if (str.includes(",") || str.includes("\n") || str.includes('"')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const csvLines = [
    headers.join(","),
    ...rows.map((row) =>
      [
        row.consignee_name,
        row.pi_count,
        row.ci_count,
        row.total_pi_value,
        row.total_ci_value,
        row.total_value,
        row.latest_doc_date,
      ]
        .map(escape)
        .join(",")
    ),
  ];

  const blob = new Blob([csvLines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// ---- Formatter helpers ------------------------------------------------------

function fmtUSD(val: string) {
  return parseFloat(val).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

// ---- Main component ---------------------------------------------------------

export default function R05ConsigneeBusinessSummary({ selectedReport }: Props) {
  const [staged, setStaged] = useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS);

  const enabled = selectedReport === "R-05";

  // ---- Master data
  const { data: consignees = [] } = useQuery({
    queryKey: ["organisations", "CONSIGNEE"],
    queryFn: () => listOrganisations("CONSIGNEE"),
    enabled,
  });

  // ---- Build API params
  const queryParams = useMemo(
    () => ({
      doc_type:    applied.doc_type || undefined,
      date_after:  applied.dateFrom || undefined,
      date_before: applied.dateTo   || undefined,
      status:      applied.status   || undefined,
      consignee:   applied.consignee || undefined,
    }),
    [applied]
  );

  const { data: rows = [], isFetching } = useQuery({
    queryKey: ["consignee-business-summary", queryParams],
    queryFn:  () => getConsigneeBusinessSummary(queryParams),
    enabled,
  });

  // ---- Grand total footer values
  const grandTotalPI = useMemo(
    () => rows.reduce((s, r) => s + parseFloat(r.total_pi_value || "0"), 0),
    [rows]
  );
  const grandTotalCI = useMemo(
    () => rows.reduce((s, r) => s + parseFloat(r.total_ci_value || "0"), 0),
    [rows]
  );
  const grandTotal = useMemo(
    () => rows.reduce((s, r) => s + parseFloat(r.total_value || "0"), 0),
    [rows]
  );

  // ---- Table columns
  const columns = [
    {
      title: "Consignee",
      dataIndex: "consignee_name",
      key: "consignee_name",
      fixed: "left" as const,
      width: 220,
      ellipsis: true,
      sorter: (a: ConsigneeSummaryRow, b: ConsigneeSummaryRow) =>
        a.consignee_name.localeCompare(b.consignee_name),
      render: (val: string) => (
        <span style={{ fontWeight: 600, fontSize: 13 }}>{val}</span>
      ),
    },
    {
      title: "PI Count",
      dataIndex: "pi_count",
      key: "pi_count",
      width: 100,
      align: "right" as const,
      sorter: (a: ConsigneeSummaryRow, b: ConsigneeSummaryRow) =>
        a.pi_count - b.pi_count,
      render: (val: number) => (
        <span
          style={{
            display: "inline-block",
            background: "var(--pastel-blue)",
            color: "var(--pastel-blue-text)",
            borderRadius: 12,
            padding: "1px 10px",
            fontSize: 12,
            fontWeight: 600,
            minWidth: 32,
            textAlign: "center",
          }}
        >
          {val}
        </span>
      ),
    },
    {
      title: "CI Count",
      dataIndex: "ci_count",
      key: "ci_count",
      width: 100,
      align: "right" as const,
      sorter: (a: ConsigneeSummaryRow, b: ConsigneeSummaryRow) =>
        a.ci_count - b.ci_count,
      render: (val: number) => (
        <span
          style={{
            display: "inline-block",
            background: "var(--pastel-green)",
            color: "var(--pastel-green-text)",
            borderRadius: 12,
            padding: "1px 10px",
            fontSize: 12,
            fontWeight: 600,
            minWidth: 32,
            textAlign: "center",
          }}
        >
          {val}
        </span>
      ),
    },
    {
      title: "Total PI Value (USD)",
      dataIndex: "total_pi_value",
      key: "total_pi_value",
      width: 175,
      align: "right" as const,
      sorter: (a: ConsigneeSummaryRow, b: ConsigneeSummaryRow) =>
        parseFloat(a.total_pi_value) - parseFloat(b.total_pi_value),
      render: (val: string) => fmtUSD(val),
    },
    {
      title: "Total CI Value (USD)",
      dataIndex: "total_ci_value",
      key: "total_ci_value",
      width: 175,
      align: "right" as const,
      sorter: (a: ConsigneeSummaryRow, b: ConsigneeSummaryRow) =>
        parseFloat(a.total_ci_value) - parseFloat(b.total_ci_value),
      render: (val: string) => fmtUSD(val),
    },
    {
      title: "Combined Total (USD)",
      dataIndex: "total_value",
      key: "total_value",
      width: 185,
      align: "right" as const,
      sorter: (a: ConsigneeSummaryRow, b: ConsigneeSummaryRow) =>
        parseFloat(a.total_value) - parseFloat(b.total_value),
      render: (val: string) => (
        <span style={{ fontWeight: 700, fontSize: 13 }}>{fmtUSD(val)}</span>
      ),
    },
    {
      title: "Latest Document",
      dataIndex: "latest_doc_date",
      key: "latest_doc_date",
      width: 140,
      sorter: (a: ConsigneeSummaryRow, b: ConsigneeSummaryRow) =>
        (a.latest_doc_date ?? "").localeCompare(b.latest_doc_date ?? ""),
      render: (val: string | null) =>
        val ? dayjs(val).format("DD MMM YYYY") : "—",
    },
  ];

  if (!enabled) return null;

  const filterGrid = document.getElementById("report-filter-grid");
  const filterButtons = document.getElementById("report-filter-buttons");

  return (
    <>
      {filterGrid && createPortal(
        <>
          <div style={{ gridColumn: "span 2" }}>
            <div style={labelStyle}>Date Range</div>
            <RangePicker
              style={{ width: "100%" }}
              value={
                staged.dateFrom && staged.dateTo
                  ? [dayjs(staged.dateFrom), dayjs(staged.dateTo)]
                  : staged.dateFrom ? [dayjs(staged.dateFrom), null] : null
              }
              onChange={(dates) => setStaged((prev) => ({
                ...prev,
                dateFrom: dates?.[0] ? dates[0].format("YYYY-MM-DD") : "",
                dateTo:   dates?.[1] ? dates[1].format("YYYY-MM-DD") : "",
              }))}
            />
          </div>
          <div>
            <div style={labelStyle}>Document Type</div>
            <Select style={{ width: "100%" }} options={DOC_TYPE_OPTIONS} value={staged.doc_type}
              onChange={(val) => setStaged((prev) => ({ ...prev, doc_type: val ?? "" }))} />
          </div>
          <div>
            <div style={labelStyle}>Status</div>
            <Select style={{ width: "100%" }} options={STATUS_OPTIONS} value={staged.status || ""}
              onChange={(val) => setStaged((prev) => ({ ...prev, status: val }))} />
          </div>
          <div>
            <div style={labelStyle}>Consignee</div>
            <Select style={{ width: "100%" }} placeholder="All consignees" allowClear
              value={staged.consignee || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, consignee: val ?? "" }))}
              options={consignees.map((o) => ({ value: String(o.id), label: o.name }))}
              showSearch filterOption={(input, option) => (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())} />
          </div>
        </>,
        filterGrid
      )}

      {filterButtons && createPortal(
        <div style={{ marginTop: 16, display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <Button onClick={() => { setStaged(EMPTY_FILTERS); setApplied(EMPTY_FILTERS); }}>Reset</Button>
          <Button type="primary" onClick={() => setApplied(staged)} loading={isFetching}>Apply Filters</Button>
        </div>,
        filterButtons
      )}

      {/* Results table */}
      <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-light)", borderRadius: 14, boxShadow: "var(--shadow-card)", overflow: "hidden" }}>
        <div style={{ padding: "16px 24px", borderBottom: "1px solid var(--border-light)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
            {rows.length} consignee{rows.length !== 1 ? "s" : ""}
          </span>
          <Button icon={<Download size={14} strokeWidth={1.5} />} onClick={() => exportToCsv(rows)} disabled={rows.length === 0}>
            Export CSV
          </Button>
        </div>
        <Table
          dataSource={rows}
          columns={columns}
          rowKey="consignee_id"
          loading={isFetching}
          size="small"
          scroll={{ x: "max-content", y: 480 }}
          pagination={{ pageSize: 20, showSizeChanger: false, showTotal: (total) => `${total} consignees` }}
          style={{ fontFamily: "var(--font-body)", fontSize: 13 }}
          summary={() =>
            rows.length > 0 ? (
              <Table.Summary.Row>
                <Table.Summary.Cell index={0} colSpan={3}>
                  <span style={{ fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" }}>
                    Grand Total ({rows.length} consignees)
                  </span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={3} align="right"><span style={{ fontWeight: 600, fontSize: 13 }}>{fmtUSD(String(grandTotalPI))}</span></Table.Summary.Cell>
                <Table.Summary.Cell index={4} align="right"><span style={{ fontWeight: 600, fontSize: 13 }}>{fmtUSD(String(grandTotalCI))}</span></Table.Summary.Cell>
                <Table.Summary.Cell index={5} align="right"><span style={{ fontWeight: 700, fontSize: 13 }}>{fmtUSD(String(grandTotal))}</span></Table.Summary.Cell>
                <Table.Summary.Cell index={6} />
              </Table.Summary.Row>
            ) : null
          }
        />
      </div>
    </>
  );
}

const labelStyle: React.CSSProperties = {
  fontFamily: "var(--font-body)",
  fontSize: 12,
  fontWeight: 500,
  color: "var(--text-secondary)",
  marginBottom: 4,
};
