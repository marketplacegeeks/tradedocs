// R-04 — Commodity Sales Report
// Flat line-item report combining PI and CI line items.
// Columns and filters defined in reports.md §R-04.
// Accessible to Checker and Company Admin only (enforced by ProtectedRoute in App.tsx).

import { useState, useMemo } from "react";
import { createPortal } from "react-dom";
import { useQuery } from "@tanstack/react-query";
import { DatePicker, Select, Input, Button, Table, Tag } from "antd";
import { Download } from "lucide-react";
import dayjs from "dayjs";

import { getCommoditySalesReport } from "../../api/reports";
import type { CommoditySalesRow } from "../../api/reports";
import { listOrganisations } from "../../api/organisations";
import { listUOMs } from "../../api/referenceData";
import {
  DOCUMENT_STATUS,
  DOCUMENT_STATUS_LABELS,
  DOCUMENT_STATUS_CHIP,
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
  hsn_code: string;
  item_code: string;
  uom: string;
}

const EMPTY_FILTERS: Filters = {
  dateFrom: "",
  dateTo: "",
  doc_type: "",
  status: "",
  consignee: "",
  hsn_code: "",
  item_code: "",
  uom: "",
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

function exportToCsv(rows: CommoditySalesRow[]) {
  const today = dayjs().format("DDMMYYYY");
  const filename = `${today}_CommoditySalesReport.csv`;

  const headers = [
    "Doc Type", "Document Number", "Date", "Status",
    "Consignee", "Country of Destination",
    "HSN Code", "Item Code", "Description",
    "Quantity", "UOM",
    "Rate", "Amount",
    "Incoterms", "Port of Loading",
  ];

  const escape = (val: string | null | undefined) => {
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
        row.doc_type,
        row.doc_number,
        row.doc_date,
        DOCUMENT_STATUS_LABELS[row.status as keyof typeof DOCUMENT_STATUS_LABELS] ?? row.status,
        row.consignee_name,
        row.country_of_destination,
        row.hsn_code,
        row.item_code,
        row.description,
        row.quantity,
        row.uom_abbr,
        row.rate_usd,
        row.amount_usd,
        row.incoterms_code,
        row.port_of_loading_name,
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

// ---- Main component ---------------------------------------------------------

export default function R04CommoditySalesReport({ selectedReport }: Props) {
  const [staged, setStaged] = useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS);

  const enabled = selectedReport === "R-04";

  // ---- Master data for dropdowns
  const { data: consignees = [] } = useQuery({
    queryKey: ["organisations", "CONSIGNEE"],
    queryFn: () => listOrganisations("CONSIGNEE"),
    enabled,
  });
  const { data: uoms = [] } = useQuery({
    queryKey: ["uoms"],
    queryFn: listUOMs,
    enabled,
  });

  // ---- Build API params from applied filters
  const queryParams = useMemo(() => ({
    doc_type: applied.doc_type || undefined,
    date_after: applied.dateFrom || undefined,
    date_before: applied.dateTo || undefined,
    status: applied.status || undefined,
    consignee: applied.consignee || undefined,
    hsn_code: applied.hsn_code || undefined,
    item_code: applied.item_code || undefined,
    uom: applied.uom || undefined,
  }), [applied]);

  const { data: rows = [], isFetching } = useQuery({
    queryKey: ["commodity-sales-report", queryParams],
    queryFn: () => getCommoditySalesReport(queryParams),
    enabled,
  });

  // ---- Footer totals
  const totalQuantity = useMemo(
    () => rows.reduce((sum, r) => sum + parseFloat(r.quantity || "0"), 0),
    [rows]
  );
  const totalAmount = useMemo(
    () => rows.reduce((sum, r) => sum + parseFloat(r.amount_usd || "0"), 0),
    [rows]
  );

  // ---- Table columns
  const columns = [
    {
      title: "Type",
      dataIndex: "doc_type",
      key: "doc_type",
      fixed: "left" as const,
      width: 60,
      render: (val: string) => (
        <Tag
          style={{
            fontSize: 11,
            fontWeight: 600,
            borderRadius: 4,
            background: val === "PI" ? "var(--pastel-blue)" : "var(--pastel-green)",
            color: val === "PI" ? "var(--pastel-blue-text)" : "var(--pastel-green-text)",
            border: "none",
          }}
        >
          {val}
        </Tag>
      ),
    },
    {
      title: "Document No.",
      dataIndex: "doc_number",
      key: "doc_number",
      fixed: "left" as const,
      width: 140,
      sorter: (a: CommoditySalesRow, b: CommoditySalesRow) =>
        a.doc_number.localeCompare(b.doc_number),
      render: (val: string) => (
        <span style={{ fontWeight: 600, fontSize: 13 }}>{val}</span>
      ),
    },
    {
      title: "Date",
      dataIndex: "doc_date",
      key: "doc_date",
      width: 110,
      sorter: (a: CommoditySalesRow, b: CommoditySalesRow) =>
        (a.doc_date ?? "").localeCompare(b.doc_date ?? ""),
      render: (val: string | null) => (val ? dayjs(val).format("DD MMM YYYY") : "—"),
    },
    {
      title: "Consignee",
      dataIndex: "consignee_name",
      key: "consignee_name",
      width: 180,
      ellipsis: true,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Country of Destination",
      dataIndex: "country_of_destination",
      key: "country_of_destination",
      width: 185,
      ellipsis: true,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "HSN Code",
      dataIndex: "hsn_code",
      key: "hsn_code",
      width: 110,
    },
    {
      title: "Item Code",
      dataIndex: "item_code",
      key: "item_code",
      width: 120,
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
      width: 220,
      ellipsis: true,
    },
    {
      title: "Qty",
      dataIndex: "quantity",
      key: "quantity",
      width: 90,
      align: "right" as const,
      sorter: (a: CommoditySalesRow, b: CommoditySalesRow) =>
        parseFloat(a.quantity) - parseFloat(b.quantity),
      render: (val: string) =>
        parseFloat(val).toLocaleString("en-US", {
          minimumFractionDigits: 3,
          maximumFractionDigits: 3,
        }),
    },
    {
      title: "UOM",
      dataIndex: "uom_abbr",
      key: "uom_abbr",
      width: 75,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Rate",
      dataIndex: "rate_usd",
      key: "rate_usd",
      width: 115,
      align: "right" as const,
      sorter: (a: CommoditySalesRow, b: CommoditySalesRow) =>
        parseFloat(a.rate_usd) - parseFloat(b.rate_usd),
      render: (val: string) =>
        parseFloat(val).toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }),
    },
    {
      title: "Amount",
      dataIndex: "amount_usd",
      key: "amount_usd",
      width: 125,
      align: "right" as const,
      sorter: (a: CommoditySalesRow, b: CommoditySalesRow) =>
        parseFloat(a.amount_usd) - parseFloat(b.amount_usd),
      render: (val: string) =>
        parseFloat(val).toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }),
    },
    {
      title: "Incoterms",
      dataIndex: "incoterms_code",
      key: "incoterms_code",
      width: 100,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Port of Loading",
      dataIndex: "port_of_loading_name",
      key: "port_of_loading_name",
      width: 160,
      ellipsis: true,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 150,
      fixed: "right" as const,
      render: (val: string) => {
        const chipClass = DOCUMENT_STATUS_CHIP[val as keyof typeof DOCUMENT_STATUS_CHIP] ?? "chip-blue";
        const label = DOCUMENT_STATUS_LABELS[val as keyof typeof DOCUMENT_STATUS_LABELS] ?? val;
        return <Tag className={chipClass}>{label}</Tag>;
      },
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
                dateTo: dates?.[1] ? dates[1].format("YYYY-MM-DD") : "",
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
          <div>
            <div style={labelStyle}>UOM</div>
            <Select style={{ width: "100%" }} placeholder="All UOMs" allowClear
              value={staged.uom || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, uom: val ?? "" }))}
              options={uoms.filter((u) => u.is_active).map((u) => ({ value: String(u.id), label: `${u.abbreviation} — ${u.name}` }))}
              showSearch filterOption={(input, option) => (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())} />
          </div>
          <div>
            <div style={labelStyle}>HSN Code</div>
            <Input placeholder="Partial match" value={staged.hsn_code}
              onChange={(e) => setStaged((prev) => ({ ...prev, hsn_code: e.target.value }))} allowClear />
          </div>
          <div>
            <div style={labelStyle}>Item Code</div>
            <Input placeholder="Partial match" value={staged.item_code}
              onChange={(e) => setStaged((prev) => ({ ...prev, item_code: e.target.value }))} allowClear />
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
            {rows.length} line item{rows.length !== 1 ? "s" : ""}
          </span>
          <Button icon={<Download size={14} strokeWidth={1.5} />} onClick={() => exportToCsv(rows)} disabled={rows.length === 0}>
            Export CSV
          </Button>
        </div>
        <Table
          dataSource={rows}
          columns={columns}
          rowKey={(row) => `${row.doc_type}-${row.doc_number}-${row.item_code}-${row.hsn_code}`}
          loading={isFetching}
          size="small"
          scroll={{ x: "max-content", y: 480 }}
          pagination={{ pageSize: 20, showSizeChanger: false, showTotal: (total) => `${total} line items` }}
          style={{ fontFamily: "var(--font-body)", fontSize: 13 }}
          summary={() =>
            rows.length > 0 ? (
              <Table.Summary.Row>
                <Table.Summary.Cell index={0} colSpan={8}>
                  <span style={{ fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" }}>
                    Totals ({rows.length} items)
                  </span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={8} align="right">
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{totalQuantity.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={9} />
                <Table.Summary.Cell index={10} />
                <Table.Summary.Cell index={11} align="right">
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{totalAmount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={12} colSpan={3} />
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
