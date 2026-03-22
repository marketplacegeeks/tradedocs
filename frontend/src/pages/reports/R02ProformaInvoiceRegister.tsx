// R-02 — Proforma Invoice Register
// Columns and filters defined in reports.md §R-02.
// Accessible to Checker and Company Admin only (enforced by ProtectedRoute in App.tsx).

import { useState, useMemo } from "react";
import { createPortal } from "react-dom";
import { useQuery } from "@tanstack/react-query";
import { DatePicker, Select, Button, Table, Tag, Tooltip } from "antd";
import { Download } from "lucide-react";
import dayjs from "dayjs";

import { listProformaInvoices } from "../../api/proformaInvoices";
import type { ProformaInvoice } from "../../api/proformaInvoices";
import { listOrganisations } from "../../api/organisations";
import { listCountries } from "../../api/countries";
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

// ---- Filter state type -------------------------------------------------------

interface Filters {
  dateFrom: string;
  dateTo: string;
  status: string;
  exporter: string;
  consignee: string;
  country_of_final_destination: string;
  incoterms: string;
  payment_terms: string;
}

const EMPTY_FILTERS: Filters = {
  dateFrom: "",
  dateTo: "",
  status: "",
  exporter: "",
  consignee: "",
  country_of_final_destination: "",
  incoterms: "",
  payment_terms: "",
};

// ---- Status options for filter dropdown -------------------------------------

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: DOCUMENT_STATUS.DRAFT, label: DOCUMENT_STATUS_LABELS.DRAFT },
  { value: DOCUMENT_STATUS.PENDING_APPROVAL, label: DOCUMENT_STATUS_LABELS.PENDING_APPROVAL },
  { value: DOCUMENT_STATUS.APPROVED, label: DOCUMENT_STATUS_LABELS.APPROVED },
  { value: DOCUMENT_STATUS.REWORK, label: DOCUMENT_STATUS_LABELS.REWORK },
  { value: DOCUMENT_STATUS.PERMANENTLY_REJECTED, label: DOCUMENT_STATUS_LABELS.PERMANENTLY_REJECTED },
];

// ---- CSV export helper -------------------------------------------------------

function exportToCsv(rows: ProformaInvoice[]) {
  const today = dayjs().format("DDMMYYYY");
  const filename = `${today}_ProformaInvoiceRegister.csv`;

  const headers = [
    "PI Number", "PI Date", "Exporter", "Consignee", "Buyer",
    "Country of Origin", "Country of Destination",
    "Port of Loading", "Port of Discharge",
    "Incoterms", "Payment Terms", "Buyer Order No",
    "Grand Total (USD)", "Invoice Total (USD)",
    "Validity for Acceptance", "Validity for Shipment",
    "Linked PL Number", "Status", "Created By",
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
    ...rows.map((pi) =>
      [
        pi.pi_number,
        pi.pi_date,
        pi.exporter_name,
        pi.consignee_name,
        pi.buyer_name,
        pi.country_of_origin_name,
        pi.country_of_final_destination_name,
        pi.port_of_loading_name,
        pi.port_of_discharge_name,
        pi.incoterms_code,
        pi.payment_terms_name,
        pi.buyer_order_no,
        pi.grand_total,
        pi.invoice_total,
        pi.validity_for_acceptance,
        pi.validity_for_shipment,
        pi.linked_pl_number,
        DOCUMENT_STATUS_LABELS[pi.status as keyof typeof DOCUMENT_STATUS_LABELS] ?? pi.status,
        pi.created_by_name,
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

export default function R02ProformaInvoiceRegister({ selectedReport }: Props) {
  // Staged filters: pending state that only gets applied when "Apply" is clicked
  const [staged, setStaged] = useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS);

  // ---- Master data for filter dropdowns (only fetched when R-02 is active)
  const enabled = selectedReport === "R-02";

  const { data: exporters = [] } = useQuery({
    queryKey: ["organisations", "EXPORTER"],
    queryFn: () => listOrganisations("EXPORTER"),
    enabled,
  });
  const { data: consignees = [] } = useQuery({
    queryKey: ["organisations", "CONSIGNEE"],
    queryFn: () => listOrganisations("CONSIGNEE"),
    enabled,
  });
  const { data: countries = [] } = useQuery({
    queryKey: ["countries"],
    queryFn: listCountries,
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

  // ---- Build query params from applied filters
  const queryParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (applied.status) p.status = applied.status;
    if (applied.exporter) p.exporter = applied.exporter;
    if (applied.consignee) p.consignee = applied.consignee;
    if (applied.country_of_final_destination) p.country_of_final_destination = applied.country_of_final_destination;
    if (applied.incoterms) p.incoterms = applied.incoterms;
    if (applied.payment_terms) p.payment_terms = applied.payment_terms;
    if (applied.dateFrom) p.pi_date_after = applied.dateFrom;
    if (applied.dateTo) p.pi_date_before = applied.dateTo;
    return p;
  }, [applied]);

  const { data: piList = [], isFetching } = useQuery({
    queryKey: ["proforma-invoices-report", queryParams],
    queryFn: () => listProformaInvoices(queryParams),
    enabled,
  });

  // ---- Table columns
  const today = dayjs().format("YYYY-MM-DD");

  const columns = [
    {
      title: "PI Number",
      dataIndex: "pi_number",
      key: "pi_number",
      fixed: "left" as const,
      width: 130,
      sorter: (a: ProformaInvoice, b: ProformaInvoice) => a.pi_number.localeCompare(b.pi_number),
      render: (val: string) => (
        <span style={{ fontFamily: "var(--font-body)", fontWeight: 600, fontSize: 13 }}>{val}</span>
      ),
    },
    {
      title: "PI Date",
      dataIndex: "pi_date",
      key: "pi_date",
      width: 110,
      sorter: (a: ProformaInvoice, b: ProformaInvoice) => a.pi_date.localeCompare(b.pi_date),
      render: (val: string) => (val ? dayjs(val).format("DD MMM YYYY") : "—"),
    },
    {
      title: "Exporter",
      dataIndex: "exporter_name",
      key: "exporter_name",
      width: 180,
      ellipsis: true,
      sorter: (a: ProformaInvoice, b: ProformaInvoice) =>
        (a.exporter_name ?? "").localeCompare(b.exporter_name ?? ""),
    },
    {
      title: "Consignee",
      dataIndex: "consignee_name",
      key: "consignee_name",
      width: 180,
      ellipsis: true,
      sorter: (a: ProformaInvoice, b: ProformaInvoice) =>
        (a.consignee_name ?? "").localeCompare(b.consignee_name ?? ""),
    },
    {
      title: "Buyer",
      dataIndex: "buyer_name",
      key: "buyer_name",
      width: 160,
      ellipsis: true,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Country of Origin",
      dataIndex: "country_of_origin_name",
      key: "country_of_origin_name",
      width: 160,
      ellipsis: true,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Country of Destination",
      dataIndex: "country_of_final_destination_name",
      key: "country_of_final_destination_name",
      width: 185,
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
      title: "Incoterms",
      dataIndex: "incoterms_code",
      key: "incoterms_code",
      width: 100,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Payment Terms",
      dataIndex: "payment_terms_name",
      key: "payment_terms_name",
      width: 160,
      ellipsis: true,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Buyer Order No",
      dataIndex: "buyer_order_no",
      key: "buyer_order_no",
      width: 140,
      ellipsis: true,
      render: (val: string) => val || "—",
    },
    {
      title: "Grand Total (USD)",
      dataIndex: "grand_total",
      key: "grand_total",
      width: 150,
      sorter: (a: ProformaInvoice, b: ProformaInvoice) =>
        parseFloat(a.grand_total) - parseFloat(b.grand_total),
      render: (val: string) =>
        parseFloat(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      align: "right" as const,
    },
    {
      title: "Invoice Total (USD)",
      dataIndex: "invoice_total",
      key: "invoice_total",
      width: 155,
      sorter: (a: ProformaInvoice, b: ProformaInvoice) =>
        parseFloat(a.invoice_total) - parseFloat(b.invoice_total),
      render: (val: string) =>
        parseFloat(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      align: "right" as const,
    },
    {
      title: "Validity for Acceptance",
      dataIndex: "validity_for_acceptance",
      key: "validity_for_acceptance",
      width: 170,
      render: (val: string | null) => (val ? dayjs(val).format("DD MMM YYYY") : "—"),
    },
    {
      title: "Validity for Shipment",
      key: "validity_for_shipment",
      width: 160,
      render: (_: unknown, record: ProformaInvoice) => {
        const val = record.validity_for_shipment;
        if (!val) return "—";
        // Highlight red if date is in the past AND PI is not yet Approved (per reports.md)
        const isPast = val < today;
        const notApproved = record.status !== DOCUMENT_STATUS.APPROVED;
        const overdue = isPast && notApproved;
        return (
          <Tooltip title={overdue ? "Shipment validity has passed" : undefined}>
            <span
              style={{
                color: overdue ? "var(--danger, #dc2626)" : undefined,
                fontWeight: overdue ? 600 : undefined,
              }}
            >
              {dayjs(val).format("DD MMM YYYY")}
            </span>
          </Tooltip>
        );
      },
    },
    {
      title: "Linked PL",
      dataIndex: "linked_pl_number",
      key: "linked_pl_number",
      width: 120,
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
    {
      title: "Created By",
      dataIndex: "created_by_name",
      key: "created_by_name",
      width: 150,
      ellipsis: true,
      render: (val: string | null) => val ?? "—",
    },
  ];

  if (!enabled) return null;

  const filterGrid = document.getElementById("report-filter-grid");
  const filterButtons = document.getElementById("report-filter-buttons");

  return (
    <>
      {/* Portal filter fields into the unified card's grid */}
      {filterGrid && createPortal(
        <>
          {/* Date range — spans two columns */}
          <div style={{ gridColumn: "span 2" }}>
            <div style={labelStyle}>PI Date Range</div>
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

          {/* Status */}
          <div>
            <div style={labelStyle}>Status</div>
            <Select
              style={{ width: "100%" }}
              options={STATUS_OPTIONS}
              value={staged.status || ""}
              onChange={(val) => setStaged((prev) => ({ ...prev, status: val }))}
            />
          </div>

          {/* Exporter */}
          <div>
            <div style={labelStyle}>Exporter</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All exporters"
              allowClear
              value={staged.exporter || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, exporter: val ?? "" }))}
              options={exporters.map((o) => ({ value: String(o.id), label: o.name }))}
              showSearch
              filterOption={(input, option) =>
                (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())
              }
            />
          </div>

          {/* Consignee */}
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

          {/* Country of Final Destination */}
          <div>
            <div style={labelStyle}>Country of Destination</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All countries"
              allowClear
              value={staged.country_of_final_destination || undefined}
              onChange={(val) =>
                setStaged((prev) => ({ ...prev, country_of_final_destination: val ?? "" }))
              }
              options={countries
                .filter((c) => c.is_active)
                .map((c) => ({ value: String(c.id), label: c.name }))}
              showSearch
              filterOption={(input, option) =>
                (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())
              }
            />
          </div>

          {/* Incoterms */}
          <div>
            <div style={labelStyle}>Incoterms</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All incoterms"
              allowClear
              value={staged.incoterms || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, incoterms: val ?? "" }))}
              options={incoterms
                .filter((i) => i.is_active)
                .map((i) => ({ value: String(i.id), label: i.code }))}
            />
          </div>

          {/* Payment Terms */}
          <div>
            <div style={labelStyle}>Payment Terms</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All payment terms"
              allowClear
              value={staged.payment_terms || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, payment_terms: val ?? "" }))}
              options={paymentTerms
                .filter((p) => p.is_active)
                .map((p) => ({ value: String(p.id), label: p.name }))}
              showSearch
              filterOption={(input, option) =>
                (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())
              }
            />
          </div>
        </>,
        filterGrid
      )}

      {/* Portal Apply/Reset buttons into the unified card */}
      {filterButtons && createPortal(
        <div style={{ marginTop: 16, display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <Button onClick={() => { setStaged(EMPTY_FILTERS); setApplied(EMPTY_FILTERS); }}>
            Reset
          </Button>
          <Button type="primary" onClick={() => setApplied(staged)} loading={isFetching}>
            Apply Filters
          </Button>
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
            {piList.length} record{piList.length !== 1 ? "s" : ""}
          </span>
          <Button
            icon={<Download size={14} strokeWidth={1.5} />}
            onClick={() => exportToCsv(piList)}
            disabled={piList.length === 0}
          >
            Export CSV
          </Button>
        </div>
        <Table
          dataSource={piList}
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

// ---- Shared inline label style ----------------------------------------------
const labelStyle: React.CSSProperties = {
  fontFamily: "var(--font-body)",
  fontSize: 12,
  fontWeight: 500,
  color: "var(--text-secondary)",
  marginBottom: 4,
};
