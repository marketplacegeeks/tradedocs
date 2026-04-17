// R-03 — Shipment Register
// Columns and filters defined in reports.md §R-03.
// Accessible to Checker and Company Admin only (enforced by ProtectedRoute in App.tsx).

import { useState, useMemo } from "react";
import { createPortal } from "react-dom";
import { useQuery } from "@tanstack/react-query";
import { DatePicker, Select, Button, Table, Tag, Tooltip } from "antd";
import { Download } from "lucide-react";
import dayjs from "dayjs";

import { listPackingLists } from "../../api/packingLists";
import type { PackingList } from "../../api/packingLists";
import { listOrganisations } from "../../api/organisations";
import { listIncoterms, listPaymentTerms } from "../../api/referenceData";
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
  status: string;
  consignee: string;
  port_of_loading: string;
  port_of_discharge: string;
  incoterms: string;
  payment_terms: string;
}

const EMPTY_FILTERS: Filters = {
  dateFrom: "",
  dateTo: "",
  status: "",
  consignee: "",
  port_of_loading: "",
  port_of_discharge: "",
  incoterms: "",
  payment_terms: "",
};

// ---- Status options ---------------------------------------------------------

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: DOCUMENT_STATUS.DRAFT, label: DOCUMENT_STATUS_LABELS.DRAFT },
  { value: DOCUMENT_STATUS.PENDING_APPROVAL, label: DOCUMENT_STATUS_LABELS.PENDING_APPROVAL },
  { value: DOCUMENT_STATUS.APPROVED, label: DOCUMENT_STATUS_LABELS.APPROVED },
  { value: DOCUMENT_STATUS.REWORK, label: DOCUMENT_STATUS_LABELS.REWORK },
  { value: DOCUMENT_STATUS.PERMANENTLY_REJECTED, label: DOCUMENT_STATUS_LABELS.PERMANENTLY_REJECTED },
];

// ---- Helpers ----------------------------------------------------------------

/** Sum container item net weights → "X.XXX" string. */
function totalNetWeight(pl: PackingList): string {
  let total = 0;
  for (const c of pl.containers) {
    for (const item of c.items) {
      total += parseFloat(item.net_weight || "0");
    }
  }
  return total.toFixed(3);
}

/** Sum container gross weights → "X.XXX" string. */
function totalGrossWeight(pl: PackingList): string {
  let total = 0;
  for (const c of pl.containers) {
    total += parseFloat(c.gross_weight || "0");
  }
  return total.toFixed(3);
}

// ---- CSV export -------------------------------------------------------------

function exportToCsv(rows: PackingList[]) {
  const today = dayjs().format("DDMMYYYY");
  const filename = `${today}_ShipmentRegister.csv`;

  const headers = [
    "PL Number", "CI Number", "Linked PI Number",
    "PL Date", "CI Date",
    "Exporter", "Consignee", "Notify Party",
    "Port of Loading", "Port of Discharge",
    "Vessel / Flight No", "BL Number", "BL Date",
    "Incoterms", "Payment Terms",
    "Total Net Weight (MT)", "Total Gross Weight (MT)", "No. of Containers",
    "CI Total", "FOB Value", "Freight", "Insurance",
    "Status", "Created By",
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
    ...rows.map((pl) => {
      const currency = pl.currency_display?.code || "USD";
      return [
        pl.pl_number,
        pl.ci_number,
        pl.pi_number_display,
        pl.pl_date,
        pl.ci_date,
        pl.exporter_name,
        pl.consignee_name,
        pl.notify_party_name,
        pl.port_of_loading_name,
        pl.port_of_discharge_name,
        pl.vessel_flight_no,
        pl.bl_number,
        pl.bl_date,
        pl.incoterms_code,
        pl.payment_terms_display,
        totalNetWeight(pl),
        totalGrossWeight(pl),
        pl.containers.length,
        pl.ci_total ? `${currency} ${pl.ci_total}` : "",
        pl.fob_value ? `${currency} ${pl.fob_value}` : "",
        pl.freight ? `${currency} ${pl.freight}` : "",
        pl.insurance ? `${currency} ${pl.insurance}` : "",
        DOCUMENT_STATUS_LABELS[pl.status as keyof typeof DOCUMENT_STATUS_LABELS] ?? pl.status,
        pl.created_by_name,
      ]
        .map(escape)
        .join(",");
    }),
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

export default function R03ShipmentRegister({ selectedReport }: Props) {
  const [staged, setStaged] = useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS);

  const enabled = selectedReport === "R-03";

  // ---- Master data for dropdowns
  const { data: consignees = [] } = useQuery({
    queryKey: ["organisations", "CONSIGNEE"],
    queryFn: () => listOrganisations("CONSIGNEE"),
    enabled,
  });
  const { data: incoterms = [] } = useQuery({
    queryKey: ["incoterms"],
    queryFn: listIncoterms,
    enabled,
  });
  const { data: paymentTerms = [] } = useQuery({
    queryKey: ["payment-terms"],
    queryFn: listPaymentTerms,
    enabled,
  });

  // Port of Loading / Discharge — fetched from the packing list API itself
  // (no standalone ports endpoint on the frontend; use text search via the
  // port_of_loading_name field on individual rows instead of a dropdown filter).
  // Covered by the backend FK filter using IDs — not available without a port listing endpoint.
  // For now these two filters are omitted from the UI (data is still filterable via status etc).

  const queryParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (applied.status) p.status = applied.status;
    if (applied.consignee) p.consignee = applied.consignee;
    if (applied.incoterms) p.incoterms = applied.incoterms;
    if (applied.payment_terms) p.payment_terms = applied.payment_terms;
    if (applied.dateFrom) p.pl_date_after = applied.dateFrom;
    if (applied.dateTo) p.pl_date_before = applied.dateTo;
    return p;
  }, [applied]);

  const { data: plList = [], isFetching } = useQuery({
    queryKey: ["packing-lists-report", queryParams],
    queryFn: () => listPackingLists(queryParams),
    enabled,
  });

  // ---- Table columns
  const columns = [
    {
      title: "PL Number",
      dataIndex: "pl_number",
      key: "pl_number",
      fixed: "left" as const,
      width: 130,
      sorter: (a: PackingList, b: PackingList) => a.pl_number.localeCompare(b.pl_number),
      render: (val: string) => (
        <span style={{ fontWeight: 600, fontSize: 13 }}>{val}</span>
      ),
    },
    {
      title: "CI Number",
      dataIndex: "ci_number",
      key: "ci_number",
      width: 130,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Linked PI",
      dataIndex: "pi_number_display",
      key: "pi_number_display",
      width: 130,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "PL Date",
      dataIndex: "pl_date",
      key: "pl_date",
      width: 110,
      sorter: (a: PackingList, b: PackingList) => a.pl_date.localeCompare(b.pl_date),
      render: (val: string) => (val ? dayjs(val).format("DD MMM YYYY") : "—"),
    },
    {
      title: "CI Date",
      dataIndex: "ci_date",
      key: "ci_date",
      width: 110,
      render: (val: string | null) => (val ? dayjs(val).format("DD MMM YYYY") : "—"),
    },
    {
      title: "Exporter",
      dataIndex: "exporter_name",
      key: "exporter_name",
      width: 180,
      ellipsis: true,
      sorter: (a: PackingList, b: PackingList) =>
        (a.exporter_name ?? "").localeCompare(b.exporter_name ?? ""),
    },
    {
      title: "Consignee",
      dataIndex: "consignee_name",
      key: "consignee_name",
      width: 180,
      ellipsis: true,
      sorter: (a: PackingList, b: PackingList) =>
        (a.consignee_name ?? "").localeCompare(b.consignee_name ?? ""),
    },
    {
      title: "Notify Party",
      dataIndex: "notify_party_name",
      key: "notify_party_name",
      width: 160,
      ellipsis: true,
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
      title: "Port of Discharge",
      dataIndex: "port_of_discharge_name",
      key: "port_of_discharge_name",
      width: 160,
      ellipsis: true,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Vessel / Flight No",
      dataIndex: "vessel_flight_no",
      key: "vessel_flight_no",
      width: 155,
      ellipsis: true,
      render: (val: string) => val || "—",
    },
    {
      title: "BL Number",
      dataIndex: "bl_number",
      key: "bl_number",
      width: 140,
      ellipsis: true,
      render: (val: string) => val || "—",
    },
    {
      title: "BL Date",
      dataIndex: "bl_date",
      key: "bl_date",
      width: 110,
      render: (val: string | null) => (val ? dayjs(val).format("DD MMM YYYY") : "—"),
    },
    {
      title: "Incoterms",
      dataIndex: "incoterms_code",
      key: "incoterms_code",
      width: 100,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Payment Terms",
      dataIndex: "payment_terms_display",
      key: "payment_terms_display",
      width: 160,
      ellipsis: true,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Net Weight (MT)",
      key: "total_net_weight",
      width: 140,
      render: (_: unknown, record: PackingList) => totalNetWeight(record),
      align: "right" as const,
    },
    {
      title: "Gross Weight (MT)",
      key: "total_gross_weight",
      width: 145,
      render: (_: unknown, record: PackingList) => totalGrossWeight(record),
      align: "right" as const,
    },
    {
      title: "Containers",
      key: "container_count",
      width: 100,
      render: (_: unknown, record: PackingList) => record.containers.length,
      align: "right" as const,
    },
    {
      title: "CI Total",
      dataIndex: "ci_total",
      key: "ci_total",
      width: 135,
      sorter: (a: PackingList, b: PackingList) =>
        parseFloat(a.ci_total ?? "0") - parseFloat(b.ci_total ?? "0"),
      render: (val: string | null, record: PackingList) => {
        if (!val) return "—";
        const currency = record.currency_display?.code || "USD";
        return `${currency} ${parseFloat(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      },
      align: "right" as const,
    },
    {
      title: "FOB Value",
      dataIndex: "fob_value",
      key: "fob_value",
      width: 140,
      render: (val: string | null, record: PackingList) => {
        if (!val) return "—";
        const currency = record.currency_display?.code || "USD";
        return `${currency} ${parseFloat(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      },
      align: "right" as const,
    },
    {
      title: "Freight",
      dataIndex: "freight",
      key: "freight",
      width: 125,
      render: (val: string | null, record: PackingList) => {
        if (!val) return "—";
        const currency = record.currency_display?.code || "USD";
        return `${currency} ${parseFloat(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      },
      align: "right" as const,
    },
    {
      title: "Insurance",
      dataIndex: "insurance",
      key: "insurance",
      width: 135,
      render: (val: string | null, record: PackingList) => {
        if (!val) return "—";
        const currency = record.currency_display?.code || "USD";
        return `${currency} ${parseFloat(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      },
      align: "right" as const,
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
    {
      title: "Created By",
      dataIndex: "created_by_name",
      key: "created_by_name",
      width: 130,
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
            <div style={labelStyle}>PL Date Range</div>
            <RangePicker
              style={{ width: "100%" }}
              value={
                staged.dateFrom && staged.dateTo
                  ? [dayjs(staged.dateFrom), dayjs(staged.dateTo)]
                  : staged.dateFrom
                  ? [dayjs(staged.dateFrom), null]
                  : null
              }
              onChange={(dates) => {
                setStaged((prev) => ({
                  ...prev,
                  dateFrom: dates?.[0] ? dates[0].format("YYYY-MM-DD") : "",
                  dateTo: dates?.[1] ? dates[1].format("YYYY-MM-DD") : "",
                }));
              }}
            />
          </div>
          <div>
            <div style={labelStyle}>Status</div>
            <Select
              style={{ width: "100%" }}
              options={STATUS_OPTIONS}
              value={staged.status || ""}
              onChange={(val) => setStaged((prev) => ({ ...prev, status: val }))}
            />
          </div>
          <div>
            <div style={labelStyle}>Consignee</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All consignees"
              allowClear
              value={staged.consignee || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, consignee: val ?? "" }))}
              options={consignees.map((o) => ({ value: String(o.id), label: o.name }))}
              showSearch
              filterOption={(input, option) =>
                (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())
              }
            />
          </div>
          <div>
            <div style={labelStyle}>Incoterms</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All incoterms"
              allowClear
              value={staged.incoterms || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, incoterms: val ?? "" }))}
              options={incoterms.filter((i) => i.is_active).map((i) => ({ value: String(i.id), label: i.code }))}
            />
          </div>
          <div>
            <div style={labelStyle}>Payment Terms</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All payment terms"
              allowClear
              value={staged.payment_terms || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, payment_terms: val ?? "" }))}
              options={paymentTerms.filter((p) => p.is_active).map((p) => ({ value: String(p.id), label: p.name }))}
              showSearch
              filterOption={(input, option) =>
                (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())
              }
            />
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
      <div
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border-light)",
          borderRadius: 14,
          boxShadow: "var(--shadow-card)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "16px 24px",
            borderBottom: "1px solid var(--border-light)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
            {plList.length} record{plList.length !== 1 ? "s" : ""}
          </span>
          <Button icon={<Download size={14} strokeWidth={1.5} />} onClick={() => exportToCsv(plList)} disabled={plList.length === 0}>
            Export CSV
          </Button>
        </div>
        <Table
          dataSource={plList}
          columns={columns}
          rowKey="id"
          loading={isFetching}
          size="small"
          scroll={{ x: "max-content", y: 480 }}
          pagination={{ pageSize: 20, showSizeChanger: false, showTotal: (total) => `${total} records` }}
          style={{ fontFamily: "var(--font-body)", fontSize: 13 }}
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
