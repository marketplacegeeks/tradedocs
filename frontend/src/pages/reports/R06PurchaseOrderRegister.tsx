// R-06 — Purchase Order Register
// Columns and filters defined in reports.md §R-06.
// Accessible to Checker and Company Admin only (enforced by ProtectedRoute in App.tsx).

import { useState, useMemo } from "react";
import { createPortal } from "react-dom";
import { useQuery } from "@tanstack/react-query";
import { DatePicker, Select, Button, Table, Tag } from "antd";
import { Download } from "lucide-react";
import dayjs from "dayjs";

import { listPurchaseOrdersReport } from "../../api/purchaseOrders";
import type { PurchaseOrder } from "../../api/purchaseOrders";
import { listOrganisations } from "../../api/organisations";
import { listCurrencies } from "../../api/currencies";
import { listCountries } from "../../api/countries";
import { listUsers } from "../../api/users";
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
  vendor: string;
  buyer: string;
  currency: string;
  transaction_type: string;
  internal_contact: string;
  country_of_origin: string;
}

const EMPTY_FILTERS: Filters = {
  dateFrom: "",
  dateTo: "",
  status: "",
  vendor: "",
  buyer: "",
  currency: "",
  transaction_type: "",
  internal_contact: "",
  country_of_origin: "",
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

const TX_TYPE_OPTIONS = [
  { value: "", label: "All Types" },
  { value: "IGST", label: "IGST (Inter-State)" },
  { value: "CGST_SGST", label: "CGST+SGST (Same State)" },
  { value: "ZERO_RATED", label: "Zero Rated (Export)" },
];

// ---- CSV export -------------------------------------------------------------

function exportToCsv(rows: PurchaseOrder[]) {
  const today = dayjs().format("DDMMYYYY");
  const filename = `${today}_PurchaseOrderRegister.csv`;

  const headers = [
    "PO Number", "PO Date", "Buyer", "Vendor", "Customer No.",
    "Internal Contact", "Delivery Address", "Currency",
    "Transaction Type", "Payment Terms", "Country of Origin",
    "Time of Delivery", "No. of Line Items",
    "Total Taxable Amt", "Total IGST", "Total CGST", "Total SGST",
    "Total Tax", "Total (Currency)", "Status", "Created By",
  ];

  const escape = (val: string | number | null | undefined) => {
    if (val == null) return "";
    const str = String(val);
    if (str.includes(",") || str.includes("\n") || str.includes('"')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const txLabel: Record<string, string> = {
    IGST: "IGST (Inter-State)",
    CGST_SGST: "CGST+SGST (Same State)",
    ZERO_RATED: "Zero Rated (Export)",
  };

  const csvLines = [
    headers.join(","),
    ...rows.map((po) =>
      [
        po.po_number,
        po.po_date,
        po.buyer_name ?? "",
        po.vendor_name,
        po.customer_no,
        po.internal_contact_name,
        po.delivery_city_country,
        po.currency_code,
        txLabel[po.transaction_type] ?? po.transaction_type,
        po.payment_terms_name ?? "",
        po.country_of_origin_name ?? "",
        po.time_of_delivery,
        po.line_item_count,
        po.total_taxable,
        po.total_igst,
        po.total_cgst,
        po.total_sgst,
        po.total_tax_amount,
        po.total,
        DOCUMENT_STATUS_LABELS[po.status as keyof typeof DOCUMENT_STATUS_LABELS] ?? po.status,
        po.created_by_name,
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

// ---- Helpers ----------------------------------------------------------------

function fmtNum(val: string | null | undefined) {
  const n = parseFloat(val ?? "0");
  if (isNaN(n)) return "—";
  return n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ---- Main component ---------------------------------------------------------

export default function R06PurchaseOrderRegister({ selectedReport }: Props) {
  const [staged, setStaged] = useState<Filters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS);

  const enabled = selectedReport === "R-06";

  // ---- Master data for dropdowns (only fetched when R-06 is active)
  const { data: vendors = [] } = useQuery({
    queryKey: ["organisations", "VENDOR"],
    queryFn: () => listOrganisations("VENDOR"),
    enabled,
  });
  const { data: buyers = [] } = useQuery({
    queryKey: ["organisations", "BUYER"],
    queryFn: () => listOrganisations("BUYER"),
    enabled,
  });
  const { data: currencies = [] } = useQuery({
    queryKey: ["currencies"],
    queryFn: listCurrencies,
    enabled,
  });
  const { data: countries = [] } = useQuery({
    queryKey: ["countries"],
    queryFn: listCountries,
    enabled,
  });
  const { data: users = [] } = useQuery({
    queryKey: ["users"],
    queryFn: listUsers,
    enabled,
  });

  // ---- Build query params from applied filters
  const queryParams = useMemo(() => {
    const p: Record<string, string | number> = {};
    if (applied.status) p.status = applied.status;
    if (applied.vendor) p.vendor = Number(applied.vendor);
    if (applied.buyer) p.buyer = Number(applied.buyer);
    if (applied.currency) p.currency = Number(applied.currency);
    if (applied.transaction_type) p.transaction_type = applied.transaction_type;
    if (applied.internal_contact) p.internal_contact = Number(applied.internal_contact);
    if (applied.country_of_origin) p.country_of_origin = Number(applied.country_of_origin);
    if (applied.dateFrom) p.po_date_after = applied.dateFrom;
    if (applied.dateTo) p.po_date_before = applied.dateTo;
    return p;
  }, [applied]);

  const { data: poList = [], isFetching } = useQuery({
    queryKey: ["purchase-orders-report", queryParams],
    queryFn: () => listPurchaseOrdersReport(queryParams),
    enabled,
  });

  const txLabel: Record<string, string> = {
    IGST: "IGST",
    CGST_SGST: "CGST+SGST",
    ZERO_RATED: "Zero Rated",
  };

  // ---- Table columns
  const columns = [
    {
      title: "PO Number",
      dataIndex: "po_number",
      key: "po_number",
      fixed: "left" as const,
      width: 130,
      sorter: (a: PurchaseOrder, b: PurchaseOrder) => a.po_number.localeCompare(b.po_number),
      render: (val: string) => (
        <span style={{ fontFamily: "var(--font-body)", fontWeight: 600, fontSize: 13 }}>{val}</span>
      ),
    },
    {
      title: "PO Date",
      dataIndex: "po_date",
      key: "po_date",
      width: 110,
      sorter: (a: PurchaseOrder, b: PurchaseOrder) => a.po_date.localeCompare(b.po_date),
      render: (val: string) => (val ? dayjs(val).format("DD MMM YYYY") : "—"),
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
      title: "Vendor",
      dataIndex: "vendor_name",
      key: "vendor_name",
      width: 180,
      ellipsis: true,
      sorter: (a: PurchaseOrder, b: PurchaseOrder) =>
        (a.vendor_name ?? "").localeCompare(b.vendor_name ?? ""),
    },
    {
      title: "Customer No.",
      dataIndex: "customer_no",
      key: "customer_no",
      width: 130,
      ellipsis: true,
      render: (val: string) => val || "—",
    },
    {
      title: "Internal Contact",
      dataIndex: "internal_contact_name",
      key: "internal_contact_name",
      width: 160,
      ellipsis: true,
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Delivery Address",
      dataIndex: "delivery_city_country",
      key: "delivery_city_country",
      width: 160,
      ellipsis: true,
      render: (val: string) => val || "—",
    },
    {
      title: "Currency",
      dataIndex: "currency_code",
      key: "currency_code",
      width: 90,
    },
    {
      title: "Transaction Type",
      dataIndex: "transaction_type",
      key: "transaction_type",
      width: 145,
      render: (val: string) => txLabel[val] ?? val,
    },
    {
      title: "Payment Terms",
      dataIndex: "payment_terms_name",
      key: "payment_terms_name",
      width: 150,
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
      title: "Time of Delivery",
      dataIndex: "time_of_delivery",
      key: "time_of_delivery",
      width: 145,
      ellipsis: true,
      render: (val: string) => val || "—",
    },
    {
      title: "# Items",
      dataIndex: "line_item_count",
      key: "line_item_count",
      width: 80,
      align: "right" as const,
    },
    {
      title: "Total Taxable",
      dataIndex: "total_taxable",
      key: "total_taxable",
      width: 130,
      align: "right" as const,
      render: (val: string) => fmtNum(val),
    },
    {
      title: "Total IGST",
      dataIndex: "total_igst",
      key: "total_igst",
      width: 115,
      align: "right" as const,
      render: (val: string) => fmtNum(val),
    },
    {
      title: "Total CGST",
      dataIndex: "total_cgst",
      key: "total_cgst",
      width: 115,
      align: "right" as const,
      render: (val: string) => fmtNum(val),
    },
    {
      title: "Total SGST",
      dataIndex: "total_sgst",
      key: "total_sgst",
      width: 115,
      align: "right" as const,
      render: (val: string) => fmtNum(val),
    },
    {
      title: "Total Tax",
      dataIndex: "total_tax_amount",
      key: "total_tax_amount",
      width: 115,
      align: "right" as const,
      render: (val: string) => fmtNum(val),
    },
    {
      title: "Total",
      dataIndex: "total",
      key: "total",
      width: 130,
      align: "right" as const,
      sorter: (a: PurchaseOrder, b: PurchaseOrder) =>
        parseFloat(a.total) - parseFloat(b.total),
      render: (val: string) => fmtNum(val),
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
      {filterGrid && createPortal(
        <>
          {/* Date range */}
          <div style={{ gridColumn: "span 2" }}>
            <div style={labelStyle}>PO Date Range</div>
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

          {/* Vendor */}
          <div>
            <div style={labelStyle}>Vendor</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All vendors"
              allowClear
              showSearch
              value={staged.vendor || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, vendor: val ?? "" }))}
              options={vendors.map((o) => ({ value: String(o.id), label: o.name }))}
              filterOption={(input, option) =>
                (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())
              }
            />
          </div>

          {/* Buyer */}
          <div>
            <div style={labelStyle}>Buyer</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All buyers"
              allowClear
              showSearch
              value={staged.buyer || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, buyer: val ?? "" }))}
              options={buyers.map((o) => ({ value: String(o.id), label: o.name }))}
              filterOption={(input, option) =>
                (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())
              }
            />
          </div>

          {/* Currency */}
          <div>
            <div style={labelStyle}>Currency</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All currencies"
              allowClear
              value={staged.currency || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, currency: val ?? "" }))}
              options={currencies.map((c) => ({ value: String(c.id), label: c.code }))}
            />
          </div>

          {/* Transaction Type */}
          <div>
            <div style={labelStyle}>Transaction Type</div>
            <Select
              style={{ width: "100%" }}
              options={TX_TYPE_OPTIONS}
              value={staged.transaction_type || ""}
              onChange={(val) => setStaged((prev) => ({ ...prev, transaction_type: val }))}
            />
          </div>

          {/* Internal Contact */}
          <div>
            <div style={labelStyle}>Internal Contact</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All contacts"
              allowClear
              showSearch
              value={staged.internal_contact || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, internal_contact: val ?? "" }))}
              options={users.filter((u) => u.is_active).map((u) => ({
                value: String(u.id),
                label: u.full_name,
              }))}
              filterOption={(input, option) =>
                (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())
              }
            />
          </div>

          {/* Country of Origin */}
          <div>
            <div style={labelStyle}>Country of Origin</div>
            <Select
              style={{ width: "100%" }}
              placeholder="All countries"
              allowClear
              showSearch
              value={staged.country_of_origin || undefined}
              onChange={(val) => setStaged((prev) => ({ ...prev, country_of_origin: val ?? "" }))}
              options={countries
                .filter((c) => c.is_active)
                .map((c) => ({ value: String(c.id), label: c.name }))}
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
            {poList.length} record{poList.length !== 1 ? "s" : ""}
          </span>
          <Button
            icon={<Download size={14} strokeWidth={1.5} />}
            onClick={() => exportToCsv(poList)}
            disabled={poList.length === 0}
          >
            Export CSV
          </Button>
        </div>
        <Table
          dataSource={poList}
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
