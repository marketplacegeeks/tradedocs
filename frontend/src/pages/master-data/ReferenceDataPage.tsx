// FR-06 Reference Data page — single tabbed page for all 7 lookup entities.
// Checker and Company Admin can add, edit, and soft-delete records.
// All authenticated users can view.

import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal, Select, message } from "antd";
import { Plus, Pencil, Trash2, Search, ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";

import { useAuth } from "../../store/AuthContext";
import { extractApiError } from "../../utils/apiErrors";
import { ROLES } from "../../utils/constants";
import { listCountries, createCountry, updateCountry, deleteCountry } from "../../api/countries";
import type { Country, CountryPayload } from "../../api/countries";
import {
  listIncoterms, createIncoterm, updateIncoterm, deleteIncoterm,
  listUOMs, createUOM, updateUOM, deleteUOM,
  listPaymentTerms, createPaymentTerm, updatePaymentTerm, deletePaymentTerm,
  listPorts, createPort, updatePort, deletePort,
  listLocations, createLocation, updateLocation, deleteLocation,
  listPreCarriageBy, createPreCarriageBy, updatePreCarriageBy, deletePreCarriageBy,
  listTypeOfPackages, createTypeOfPackage, updateTypeOfPackage, deleteTypeOfPackage,
} from "../../api/referenceData";
import type {
  Incoterm, IncotermPayload,
  UOM, UOMPayload,
  PaymentTerm, PaymentTermPayload,
  Port, PortPayload,
  Location, LocationPayload,
  PreCarriageBy, PreCarriageByPayload,
  TypeOfPackage, TypeOfPackagePayload,
} from "../../api/referenceData";
import { listCurrencies, createCurrency, updateCurrency, deleteCurrency } from "../../api/currencies";
import type { Currency, CurrencyPayload } from "../../api/currencies";
import {
  listProducts, createProduct, updateProduct, deleteProduct,
  listTestParameters, createTestParameter, updateTestParameter, deleteTestParameter,
  listTestMethods, createTestMethod, updateTestMethod, deleteTestMethod,
  createProductGrade, updateProductGrade,
} from "../../api/coa";
import type { Product, TestParameter, TestMethod } from "../../api/coa";

// ---- Tab definitions --------------------------------------------------------

const TABS = [
  { key: "countries",        label: "Countries" },
  { key: "incoterms",        label: "Incoterms" },
  { key: "uom",              label: "Material Unit" },
  { key: "payment-terms",    label: "Payment Terms" },
  { key: "ports",            label: "Ports" },
  { key: "locations",        label: "Locations" },
  { key: "pre-carriage",     label: "Pre-Carriage By" },
  { key: "currency",         label: "Currency" },
  { key: "type-of-packages", label: "Type of Package" },
  { key: "products",         label: "Products" },
  { key: "test-parameters",  label: "Test Parameters" },
  { key: "test-methods",     label: "Test Methods" },
] as const;

type TabKey = typeof TABS[number]["key"];
type SortDir = "asc" | "desc" | null;

// The primary field to sort by for each tab
const TAB_SORT_KEY: Record<TabKey, string> = {
  "countries":        "name",
  "incoterms":        "code",
  "uom":              "name",
  "payment-terms":    "name",
  "ports":            "name",
  "locations":        "name",
  "pre-carriage":     "name",
  "currency":         "code",
  "type-of-packages": "name",
  "products":         "name",
  "test-parameters":  "name",
  "test-methods":     "code",
};

// Which fields to search within for each tab
function matchesSearch(r: Record<string, unknown>, tab: TabKey, q: string): boolean {
  switch (tab) {
    case "countries":
      return ["name", "iso2", "iso3"].some((k) => String(r[k] ?? "").toLowerCase().includes(q));
    case "incoterms":
      return ["code", "full_name"].some((k) => String(r[k] ?? "").toLowerCase().includes(q));
    case "uom":
      return ["name", "abbreviation"].some((k) => String(r[k] ?? "").toLowerCase().includes(q));
    case "ports":
      return ["name", "code", "country_name"].some((k) => String(r[k] ?? "").toLowerCase().includes(q));
    case "locations":
      return ["name", "country_name"].some((k) => String(r[k] ?? "").toLowerCase().includes(q));
    case "currency":
      return ["code", "name"].some((k) => String(r[k] ?? "").toLowerCase().includes(q));
    case "products":
      return ["name", "cas_number"].some((k) => String(r[k] ?? "").toLowerCase().includes(q));
    case "test-parameters":
      return String(r["name"] ?? "").toLowerCase().includes(q);
    case "test-methods":
      return ["code", "description"].some((k) => String(r[k] ?? "").toLowerCase().includes(q));
    default:
      return String(r["name"] ?? "").toLowerCase().includes(q);
  }
}

// ---- Shared UI helpers ------------------------------------------------------

const thBaseStyle: React.CSSProperties = {
  padding: "12px 16px",
  textAlign: "left",
  fontFamily: "var(--font-body)",
  fontSize: 11,
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "var(--text-muted)",
  borderBottom: "1px solid var(--border-light)",
  whiteSpace: "nowrap",
};

function StaticTh({ label }: { label: string }) {
  return <th style={thBaseStyle}>{label}</th>;
}

function SortableTh({
  label,
  active,
  dir,
  onClick,
}: {
  label: string;
  active: boolean;
  dir: SortDir;
  onClick: () => void;
}) {
  return (
    <th
      onClick={onClick}
      style={{
        ...thBaseStyle,
        color: active ? "var(--primary)" : "var(--text-muted)",
        cursor: "pointer",
        userSelect: "none",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
        {label}
        {active && dir === "asc" ? (
          <ChevronUp size={12} strokeWidth={2} color="var(--primary)" />
        ) : active && dir === "desc" ? (
          <ChevronDown size={12} strokeWidth={2} color="var(--primary)" />
        ) : (
          <ChevronsUpDown size={12} strokeWidth={1.5} color="var(--text-muted)" />
        )}
      </div>
    </th>
  );
}

const tdStyle: React.CSSProperties = {
  padding: "13px 16px",
  borderBottom: "1px solid var(--border-light)",
  fontFamily: "var(--font-body)",
  fontSize: 14,
  color: "var(--text-primary)",
};

const tdMutedStyle: React.CSSProperties = {
  ...tdStyle,
  fontSize: 13,
  color: "var(--text-secondary)",
};

function ActionCell({
  onEdit,
  onDelete,
  canWrite,
}: {
  onEdit: () => void;
  onDelete: () => void;
  canWrite: boolean;
}) {
  if (!canWrite) return <td style={{ padding: "13px 16px", borderBottom: "1px solid var(--border-light)" }} />;
  return (
    <td
      style={{
        padding: "13px 16px",
        borderBottom: "1px solid var(--border-light)",
        textAlign: "right",
      }}
    >
      <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
        <button
          onClick={onEdit}
          style={{
            display: "inline-flex", alignItems: "center", gap: 4,
            padding: "5px 10px", background: "transparent",
            border: "1px solid var(--border-medium)", borderRadius: 6,
            fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 500,
            color: "var(--text-secondary)", cursor: "pointer",
          }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)")}
          onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}
        >
          <Pencil size={12} strokeWidth={1.5} />
          Edit
        </button>
        <button
          onClick={onDelete}
          style={{
            display: "inline-flex", alignItems: "center", gap: 4,
            padding: "5px 10px", background: "transparent",
            border: "1px solid var(--border-medium)", borderRadius: 6,
            fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 500,
            color: "var(--pastel-pink-text)", cursor: "pointer",
          }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--pastel-pink)")}
          onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}
        >
          <Trash2 size={12} strokeWidth={1.5} />
          Deactivate
        </button>
      </div>
    </td>
  );
}

function EmptyState({ canWrite, onAdd, searchQuery }: { canWrite: boolean; onAdd: () => void; searchQuery: string }) {
  if (searchQuery.trim()) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "48px 24px", gap: 12 }}>
        <p style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
          No results for "{searchQuery.trim()}"
        </p>
        <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
          Try a different search term.
        </p>
      </div>
    );
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "48px 24px", gap: 12 }}>
      <p style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
        No records yet
      </p>
      {canWrite && (
        <button
          onClick={onAdd}
          style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            padding: "8px 14px", background: "var(--primary)", color: "#fff",
            border: "none", borderRadius: 8, fontFamily: "var(--font-body)",
            fontSize: 13, fontWeight: 500, cursor: "pointer",
          }}
        >
          <Plus size={14} strokeWidth={2} /> Add first record
        </button>
      )}
    </div>
  );
}

function fieldLabel(text: string) {
  return (
    <div style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", marginBottom: 4 }}>
      {text}
    </div>
  );
}

function TextInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: "100%", padding: "8px 12px", borderRadius: 8,
        border: "1px solid var(--border-medium)", fontFamily: "var(--font-body)",
        fontSize: 14, color: "var(--text-primary)", background: "var(--bg-surface)",
        boxSizing: "border-box" as const, outline: "none",
      }}
    />
  );
}

function TextAreaInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={3}
      style={{
        width: "100%", padding: "8px 12px", borderRadius: 8,
        border: "1px solid var(--border-medium)", fontFamily: "var(--font-body)",
        fontSize: 14, color: "var(--text-primary)", background: "var(--bg-surface)",
        boxSizing: "border-box" as const, outline: "none", resize: "vertical",
      }}
    />
  );
}

// ---- Main page component ----------------------------------------------------

export default function ReferenceDataPage() {
  const { user } = useAuth();
  const canWrite = user?.role === ROLES.CHECKER || user?.role === ROLES.COMPANY_ADMIN || user?.role === ROLES.SUPER_ADMIN;
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<TabKey>("countries");

  // Modal state: null = closed, "add" = add modal, number = edit modal for that ID
  const [modal, setModal] = useState<null | "add" | number>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Generic form state for each tab's add/edit modal
  const [form, setForm] = useState<Record<string, string>>({});

  // Product grade management: which product's grades are expanded inline
  const [managingGradesFor, setManagingGradesFor] = useState<number | null>(null);
  const [gradeForm, setGradeForm] = useState<{ id: number | null; grade: string }>({ id: null, grade: "" });

  // Search and sort — both reset when switching tabs
  const [searchQuery, setSearchQuery] = useState("");
  const [sortDir, setSortDir] = useState<SortDir>(null);

  function openAdd() {
    setForm({});
    setModal("add");
  }

  function openEdit(record: Record<string, unknown>) {
    const seed: Record<string, string> = {};
    for (const [k, v] of Object.entries(record)) {
      if (k !== "id" && k !== "is_active" && !k.endsWith("_name")) {
        seed[k] = String(v ?? "");
      }
    }
    setForm(seed);
    setModal(record.id as number);
  }

  function closeModal() {
    setModal(null);
    setForm({});
  }

  function handleTabChange(tab: TabKey) {
    setActiveTab(tab);
    setSearchQuery("");
    setSortDir(null);
    closeModal();
    setDeletingId(null);
  }

  function toggleSort() {
    setSortDir((prev) => (prev === null ? "asc" : prev === "asc" ? "desc" : null));
  }

  // ---- Query & mutation helpers (per active tab) ---------------------------

  const queryKey = [activeTab];

  const listFns: Record<TabKey, () => Promise<unknown[]>> = {
    "countries":        listCountries,
    "incoterms":        listIncoterms,
    "uom":              listUOMs,
    "payment-terms":    listPaymentTerms,
    "ports":            listPorts,
    "locations":        listLocations,
    "pre-carriage":     listPreCarriageBy,
    "currency":         listCurrencies,
    "type-of-packages": listTypeOfPackages,
    "products":         () => listProducts().then((r) => r.data),
    "test-parameters":  () => listTestParameters().then((r) => r.data),
    "test-methods":     () => listTestMethods().then((r) => r.data),
  };

  const { data: records = [], isLoading } = useQuery({
    queryKey,
    queryFn: listFns[activeTab] as () => Promise<Record<string, unknown>[]>,
  });

  // Filter then sort the fetched records
  const displayed = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    let rows = (records as Record<string, unknown>[]);
    if (q) {
      rows = rows.filter((r) => matchesSearch(r, activeTab, q));
    }
    if (sortDir) {
      const key = TAB_SORT_KEY[activeTab];
      rows = [...rows].sort((a, b) => {
        const av = String(a[key] ?? "").toLowerCase();
        const bv = String(b[key] ?? "").toLowerCase();
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      });
    }
    return rows;
  }, [records, searchQuery, sortDir, activeTab]);

  // Build the payload from form state, parsing country ID to number where needed
  function buildPayload(): Record<string, unknown> {
    const p: Record<string, unknown> = { ...form };
    if ("country" in p) p.country = Number(p.country);
    return p;
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = buildPayload();
      if (modal === "add") {
        if (activeTab === "countries")     return createCountry(payload as CountryPayload);
        if (activeTab === "incoterms")     return createIncoterm(payload as IncotermPayload);
        if (activeTab === "uom")           return createUOM(payload as UOMPayload);
        if (activeTab === "payment-terms") return createPaymentTerm(payload as PaymentTermPayload);
        if (activeTab === "ports")         return createPort(payload as PortPayload);
        if (activeTab === "locations")     return createLocation(payload as LocationPayload);
        if (activeTab === "pre-carriage")     return createPreCarriageBy(payload as PreCarriageByPayload);
        if (activeTab === "currency")         return createCurrency(payload as CurrencyPayload);
        if (activeTab === "type-of-packages") return createTypeOfPackage(payload as TypeOfPackagePayload);
        if (activeTab === "products")         return createProduct({ name: payload.name as string, cas_number: payload.cas_number as string });
        if (activeTab === "test-parameters")  return createTestParameter({ name: payload.name as string, default_unit: payload.default_unit ? Number(payload.default_unit) : null });
        if (activeTab === "test-methods")     return createTestMethod({ code: payload.code as string, description: payload.description as string });
      } else if (typeof modal === "number") {
        if (activeTab === "countries")        return updateCountry(modal, payload as Partial<CountryPayload>);
        if (activeTab === "incoterms")        return updateIncoterm(modal, payload as Partial<IncotermPayload>);
        if (activeTab === "uom")              return updateUOM(modal, payload as Partial<UOMPayload>);
        if (activeTab === "payment-terms")    return updatePaymentTerm(modal, payload as Partial<PaymentTermPayload>);
        if (activeTab === "ports")            return updatePort(modal, payload as Partial<PortPayload>);
        if (activeTab === "locations")        return updateLocation(modal, payload as Partial<LocationPayload>);
        if (activeTab === "pre-carriage")     return updatePreCarriageBy(modal, payload as Partial<PreCarriageByPayload>);
        if (activeTab === "currency")         return updateCurrency(modal, payload as Partial<CurrencyPayload>);
        if (activeTab === "type-of-packages") return updateTypeOfPackage(modal, payload as Partial<TypeOfPackagePayload>);
        if (activeTab === "products")         return updateProduct(modal, { name: payload.name as string, cas_number: payload.cas_number as string });
        if (activeTab === "test-parameters")  return updateTestParameter(modal, { name: payload.name as string, default_unit: payload.default_unit ? Number(payload.default_unit) : null });
        if (activeTab === "test-methods")     return updateTestMethod(modal, { code: payload.code as string, description: payload.description as string });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      message.success(modal === "add" ? "Record added." : "Record updated.");
      closeModal();
    },
    onError: (err: unknown) => {
      message.error(extractApiError(err, "Failed to save. Please check your inputs and try again."));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      if (activeTab === "countries")     return deleteCountry(id);
      if (activeTab === "incoterms")     return deleteIncoterm(id);
      if (activeTab === "uom")           return deleteUOM(id);
      if (activeTab === "payment-terms") return deletePaymentTerm(id);
      if (activeTab === "ports")         return deletePort(id);
      if (activeTab === "locations")     return deleteLocation(id);
      if (activeTab === "pre-carriage")     return deletePreCarriageBy(id);
      if (activeTab === "currency")         return deleteCurrency(id);
      if (activeTab === "type-of-packages") return deleteTypeOfPackage(id);
      if (activeTab === "products")         return deleteProduct(id);
      if (activeTab === "test-parameters")  return deleteTestParameter(id);
      if (activeTab === "test-methods")     return deleteTestMethod(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      message.success("Record deactivated.");
      setDeletingId(null);
    },
    onError: (err: unknown) => {
      message.error(extractApiError(err, "Failed to deactivate. Please try again."));
      setDeletingId(null);
    },
  });

  // ---- Table renderer per tab -----------------------------------------------

  function renderTable() {
    if (isLoading) {
      return (
        <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-body)" }}>
          Loading…
        </div>
      );
    }

    if (displayed.length === 0) {
      return <EmptyState canWrite={canWrite} onAdd={openAdd} searchQuery={searchQuery} />;
    }

    const rows = displayed;

    return (
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 500 }}>
          {activeTab === "countries" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Country" active={true} dir={sortDir} onClick={toggleSort} />
                  <StaticTh label="ISO2" />
                  <StaticTh label="ISO3" />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as Country[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}>{r.name}</td>
                    <td style={tdMutedStyle}>{r.iso2}</td>
                    <td style={tdMutedStyle}>{r.iso3}</td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "incoterms" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Code" active={true} dir={sortDir} onClick={toggleSort} />
                  <StaticTh label="Full Name" />
                  <StaticTh label="Description" />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as Incoterm[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}><span className="chip chip-blue">{r.code}</span></td>
                    <td style={tdStyle}>{r.full_name}</td>
                    <td style={tdMutedStyle}>{r.description || "—"}</td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "uom" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Name" active={true} dir={sortDir} onClick={toggleSort} />
                  <StaticTh label="Abbreviation" />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as UOM[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}>{r.name}</td>
                    <td style={tdStyle}><span className="chip chip-purple">{r.abbreviation}</span></td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "payment-terms" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Name" active={true} dir={sortDir} onClick={toggleSort} />
                  <StaticTh label="Description" />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as PaymentTerm[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}>{r.name}</td>
                    <td style={tdMutedStyle}>{r.description || "—"}</td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "ports" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Port Name" active={true} dir={sortDir} onClick={toggleSort} />
                  <StaticTh label="UN/LOCODE" />
                  <StaticTh label="Country" />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as Port[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}>{r.name}</td>
                    <td style={tdStyle}><span className="chip chip-yellow">{r.code}</span></td>
                    <td style={tdMutedStyle}>{r.country_name}</td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "locations" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Location Name" active={true} dir={sortDir} onClick={toggleSort} />
                  <StaticTh label="Country" />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as Location[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}>{r.name}</td>
                    <td style={tdMutedStyle}>{r.country_name}</td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "pre-carriage" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Carrier / Mode" active={true} dir={sortDir} onClick={toggleSort} />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as PreCarriageBy[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}>{r.name}</td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "type-of-packages" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Package Type" active={true} dir={sortDir} onClick={toggleSort} />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as TypeOfPackage[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}>{r.name}</td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "currency" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Code" active={true} dir={sortDir} onClick={toggleSort} />
                  <StaticTh label="Currency Name" />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as Currency[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}><span className="chip chip-blue">{r.code}</span></td>
                    <td style={tdStyle}>{r.name}</td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "products" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Product Name" active={true} dir={sortDir} onClick={toggleSort} />
                  <StaticTh label="CAS Number" />
                  <StaticTh label="Grades" />
                  <StaticTh label="Status" />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as Product[]).map((r) => (
                  <>
                    <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                      <td style={tdStyle}>{r.name}</td>
                      <td style={tdMutedStyle}>{r.cas_number || "—"}</td>
                      <td style={tdStyle}>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                          {(r.grades ?? []).filter((g) => g.is_active).map((g) => (
                            <span key={g.id} className="chip chip-purple" style={{ fontSize: 11 }}>{g.grade}</span>
                          ))}
                          {(r.grades ?? []).filter((g) => g.is_active).length === 0 && (
                            <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)" }}>No grades</span>
                          )}
                        </div>
                      </td>
                      <td style={tdStyle}>
                        <span className={r.is_active ? "chip-green" : "chip-pink"} style={{ fontSize: 11 }}>
                          {r.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td style={{ padding: "13px 16px", borderBottom: "1px solid var(--border-light)", textAlign: "right" }}>
                        {canWrite && (
                          <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                            <button
                              onClick={() => openEdit(r as unknown as Record<string, unknown>)}
                              style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "5px 10px", background: "transparent", border: "1px solid var(--border-medium)", borderRadius: 6, fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 500, color: "var(--text-secondary)", cursor: "pointer" }}
                              onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)")}
                              onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}
                            >Edit</button>
                            <button
                              onClick={() => setManagingGradesFor(managingGradesFor === r.id ? null : r.id)}
                              style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "5px 10px", background: "transparent", border: "1px solid var(--border-medium)", borderRadius: 6, fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 500, color: "var(--text-secondary)", cursor: "pointer" }}
                              onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)")}
                              onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}
                            >Manage Grades</button>
                            <button
                              onClick={() => setDeletingId(r.id)}
                              style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "5px 10px", background: "transparent", border: "1px solid var(--border-medium)", borderRadius: 6, fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 500, color: "var(--pastel-pink-text)", cursor: "pointer" }}
                              onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--pastel-pink)")}
                              onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}
                            >Deactivate</button>
                          </div>
                        )}
                      </td>
                    </tr>
                    {managingGradesFor === r.id && (
                      <tr key={`grades-${r.id}`}>
                        <td colSpan={5} style={{ padding: "0 16px 16px 32px", borderBottom: "1px solid var(--border-light)", background: "var(--bg-base)" }}>
                          <GradeManager
                            product={r}
                            gradeForm={gradeForm}
                            setGradeForm={setGradeForm}
                            canWrite={canWrite}
                            onSaved={() => queryClient.invalidateQueries({ queryKey })}
                          />
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "test-parameters" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Parameter Name" active={true} dir={sortDir} onClick={toggleSort} />
                  <StaticTh label="Default Unit" />
                  <StaticTh label="Status" />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as TestParameter[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}>{r.name}</td>
                    <td style={tdMutedStyle}>{r.default_unit_abbreviation || "—"}</td>
                    <td style={tdStyle}>
                      <span className={r.is_active ? "chip-green" : "chip-pink"} style={{ fontSize: 11 }}>
                        {r.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}

          {activeTab === "test-methods" && (
            <>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <SortableTh label="Code" active={true} dir={sortDir} onClick={toggleSort} />
                  <StaticTh label="Description" />
                  <StaticTh label="Status" />
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {(rows as TestMethod[]).map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = "transparent"; }}>
                    <td style={tdStyle}><span className="chip chip-blue">{r.code}</span></td>
                    <td style={tdMutedStyle}>{r.description || "—"}</td>
                    <td style={tdStyle}>
                      <span className={r.is_active ? "chip-green" : "chip-pink"} style={{ fontSize: 11 }}>
                        {r.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <ActionCell canWrite={canWrite} onEdit={() => openEdit(r as unknown as Record<string, unknown>)} onDelete={() => setDeletingId(r.id)} />
                  </tr>
                ))}
              </tbody>
            </>
          )}
        </table>
      </div>
    );
  }

  // ---- Modal form fields per tab ------------------------------------------

  const { data: allCountries = [] } = useQuery({
    queryKey: ["countries"],
    queryFn: listCountries,
  });

  // UOM options — used in the test-parameters modal for default unit
  const { data: allUOMs = [] } = useQuery({
    queryKey: ["uoms"],
    queryFn: listUOMs,
  });

  function renderModalFields() {
    const countryOptions = (allCountries as Country[]).map((c) => ({ value: String(c.id), label: `${c.name} (${c.iso2})` }));
    const uomOptions = (allUOMs as UOM[]).filter((u) => u.is_active).map((u) => ({ value: String(u.id), label: `${u.name} (${u.abbreviation})` }));

    switch (activeTab) {
      case "countries":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingTop: 8 }}>
            <div>{fieldLabel("Country Name")}<TextInput value={form.name ?? ""} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="e.g. India" /></div>
            <div style={{ display: "flex", gap: 12 }}>
              <div style={{ flex: 1 }}>{fieldLabel("ISO2 Code")}<TextInput value={form.iso2 ?? ""} onChange={(v) => setForm((f) => ({ ...f, iso2: v.toUpperCase() }))} placeholder="e.g. IN" /></div>
              <div style={{ flex: 1 }}>{fieldLabel("ISO3 Code")}<TextInput value={form.iso3 ?? ""} onChange={(v) => setForm((f) => ({ ...f, iso3: v.toUpperCase() }))} placeholder="e.g. IND" /></div>
            </div>
          </div>
        );
      case "incoterms":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingTop: 8 }}>
            <div>{fieldLabel("Code")}<TextInput value={form.code ?? ""} onChange={(v) => setForm((f) => ({ ...f, code: v.toUpperCase() }))} placeholder="e.g. FOB" /></div>
            <div>{fieldLabel("Full Name")}<TextInput value={form.full_name ?? ""} onChange={(v) => setForm((f) => ({ ...f, full_name: v }))} placeholder="e.g. Free On Board" /></div>
            <div>{fieldLabel("Description (optional)")}<TextAreaInput value={form.description ?? ""} onChange={(v) => setForm((f) => ({ ...f, description: v }))} placeholder="Brief explanation of this incoterm…" /></div>
          </div>
        );
      case "uom":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingTop: 8 }}>
            <div>{fieldLabel("Unit Name")}<TextInput value={form.name ?? ""} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="e.g. Metric Tonnes" /></div>
            <div>{fieldLabel("Abbreviation")}<TextInput value={form.abbreviation ?? ""} onChange={(v) => setForm((f) => ({ ...f, abbreviation: v.toUpperCase() }))} placeholder="e.g. MT" /></div>
          </div>
        );
      case "payment-terms":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingTop: 8 }}>
            <div>{fieldLabel("Term Name")}<TextInput value={form.name ?? ""} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="e.g. Advance Payment" /></div>
            <div>{fieldLabel("Description (optional)")}<TextAreaInput value={form.description ?? ""} onChange={(v) => setForm((f) => ({ ...f, description: v }))} placeholder="Details about this payment term…" /></div>
          </div>
        );
      case "ports":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingTop: 8 }}>
            <div>{fieldLabel("Port Name")}<TextInput value={form.name ?? ""} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="e.g. Nhava Sheva" /></div>
            <div>{fieldLabel("UN/LOCODE")}<TextInput value={form.code ?? ""} onChange={(v) => setForm((f) => ({ ...f, code: v.toUpperCase() }))} placeholder="e.g. INNSA" /></div>
            <div>
              {fieldLabel("Country")}
              <Select
                value={form.country || undefined}
                onChange={(v) => setForm((f) => ({ ...f, country: v }))}
                showSearch
                filterOption={(input, option) => (option?.label ?? "").toLowerCase().includes(input.toLowerCase())}
                placeholder="Select country"
                style={{ width: "100%" }}
                options={countryOptions}
              />
            </div>
          </div>
        );
      case "locations":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingTop: 8 }}>
            <div>{fieldLabel("Location Name")}<TextInput value={form.name ?? ""} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="e.g. Inland Container Depot, Tughlakabad" /></div>
            <div>
              {fieldLabel("Country")}
              <Select
                value={form.country || undefined}
                onChange={(v) => setForm((f) => ({ ...f, country: v }))}
                showSearch
                filterOption={(input, option) => (option?.label ?? "").toLowerCase().includes(input.toLowerCase())}
                placeholder="Select country"
                style={{ width: "100%" }}
                options={countryOptions}
              />
            </div>
          </div>
        );
      case "pre-carriage":
        return (
          <div style={{ paddingTop: 8 }}>
            {fieldLabel("Carrier / Mode Name")}
            <TextInput value={form.name ?? ""} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="e.g. Truck, Rail, Feeder Vessel" />
          </div>
        );
      case "currency":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingTop: 8 }}>
            <div>{fieldLabel("Currency Name")}<TextInput value={form.name ?? ""} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="e.g. US Dollar" /></div>
            <div>{fieldLabel("Currency Code")}<TextInput value={form.code ?? ""} onChange={(v) => setForm((f) => ({ ...f, code: v.toUpperCase() }))} placeholder="e.g. USD" /></div>
          </div>
        );
      case "type-of-packages":
        return (
          <div style={{ paddingTop: 8 }}>
            {fieldLabel("Package Type Name")}
            <TextInput value={form.name ?? ""} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="e.g. Drums, Cartons, Bags" />
          </div>
        );
      case "products":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingTop: 8 }}>
            <div>{fieldLabel("Product Name")}<TextInput value={form.name ?? ""} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="e.g. Sodium Chloride" /></div>
            <div>{fieldLabel("CAS Number (optional)")}<TextInput value={form.cas_number ?? ""} onChange={(v) => setForm((f) => ({ ...f, cas_number: v }))} placeholder="e.g. 7647-14-5" /></div>
          </div>
        );
      case "test-parameters":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingTop: 8 }}>
            <div>{fieldLabel("Parameter Name")}<TextInput value={form.name ?? ""} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="e.g. Assay (as NaCl)" /></div>
            <div>
              {fieldLabel("Default Unit (optional)")}
              <Select
                value={form.default_unit || undefined}
                onChange={(v) => setForm((f) => ({ ...f, default_unit: v ?? "" }))}
                allowClear
                showSearch
                filterOption={(input, option) => (option?.label ?? "").toLowerCase().includes(input.toLowerCase())}
                placeholder="Select unit"
                style={{ width: "100%" }}
                options={uomOptions}
              />
            </div>
          </div>
        );
      case "test-methods":
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, paddingTop: 8 }}>
            <div>{fieldLabel("Method Code")}<TextInput value={form.code ?? ""} onChange={(v) => setForm((f) => ({ ...f, code: v.toUpperCase() }))} placeholder="e.g. IP-105" /></div>
            <div>{fieldLabel("Description (optional)")}<TextAreaInput value={form.description ?? ""} onChange={(v) => setForm((f) => ({ ...f, description: v }))} placeholder="Brief description of the test method…" /></div>
          </div>
        );
    }
  }

  const tabLabel = TABS.find((t) => t.key === activeTab)?.label ?? "";
  const isAdding = modal === "add";
  const totalCount = (records as Record<string, unknown>[]).length;
  const countLabel = searchQuery.trim()
    ? `${displayed.length} of ${totalCount} record${totalCount !== 1 ? "s" : ""}`
    : undefined;

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
          <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
            Reference Data
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            {countLabel ?? "Lookup values used across all trade documents"}
          </p>
        </div>
        {canWrite && (
          <button
            onClick={openAdd}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "9px 16px", background: "var(--primary)", color: "#fff",
              border: "none", borderRadius: 8, fontFamily: "var(--font-body)",
              fontSize: 14, fontWeight: 500, cursor: "pointer",
            }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--primary-hover)")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--primary)")}
          >
            <Plus size={16} strokeWidth={2} />
            Add {tabLabel}
          </button>
        )}
      </div>

      {/* Tab bar */}
      <div
        style={{
          display: "flex",
          gap: 2,
          marginBottom: 16,
          borderBottom: "1px solid var(--border-light)",
          overflowX: "auto",
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => handleTabChange(tab.key)}
            style={{
              padding: "9px 16px",
              border: "none",
              borderBottom: activeTab === tab.key ? "2px solid var(--primary)" : "2px solid transparent",
              background: "transparent",
              fontFamily: "var(--font-body)",
              fontSize: 13,
              fontWeight: activeTab === tab.key ? 600 : 400,
              color: activeTab === tab.key ? "var(--primary)" : "var(--text-secondary)",
              cursor: "pointer",
              whiteSpace: "nowrap",
              marginBottom: -1,
              transition: "color 0.15s ease",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search bar — resets on tab switch */}
      <div style={{ position: "relative", marginBottom: 16 }}>
        <Search
          size={15}
          strokeWidth={1.5}
          style={{
            position: "absolute",
            left: 12,
            top: "50%",
            transform: "translateY(-50%)",
            color: "var(--text-muted)",
            pointerEvents: "none",
          }}
        />
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={`Search ${tabLabel.toLowerCase()}…`}
          style={{
            width: "100%",
            padding: "9px 14px 9px 36px",
            background: "var(--bg-input)",
            border: "1px solid var(--border-medium)",
            borderRadius: 8,
            fontFamily: "var(--font-body)",
            fontSize: 14,
            color: "var(--text-primary)",
            outline: "none",
            boxSizing: "border-box",
            transition: "border-color 0.15s ease",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "var(--primary)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border-medium)")}
        />
      </div>

      {/* Table card */}
      <div
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border-light)",
          borderRadius: 14,
          boxShadow: "var(--shadow-card)",
          overflow: "hidden",
        }}
      >
        {renderTable()}
      </div>

      {/* Add / Edit modal */}
      <Modal
        title={
          <span style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: 16 }}>
            {isAdding ? `Add ${tabLabel}` : `Edit ${tabLabel}`}
          </span>
        }
        open={modal !== null}
        onOk={() => saveMutation.mutate()}
        onCancel={closeModal}
        okText={isAdding ? "Add" : "Save Changes"}
        okButtonProps={{ loading: saveMutation.isPending }}
        cancelText="Cancel"
        width={460}
        destroyOnClose
      >
        {renderModalFields()}
      </Modal>

      {/* Deactivate confirmation modal */}
      <Modal
        title="Deactivate Record"
        open={deletingId !== null}
        onOk={() => { if (deletingId !== null) deleteMutation.mutate(deletingId); }}
        onCancel={() => setDeletingId(null)}
        okText="Deactivate"
        okButtonProps={{ danger: true, loading: deleteMutation.isPending }}
        cancelText="Cancel"
      >
        <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-secondary)" }}>
          This record will be deactivated and will no longer appear in document dropdowns.
        </p>
      </Modal>
    </div>
  );
}

// ---- GradeManager: inline grade panel for a single product -----------------

function GradeManager({
  product,
  gradeForm,
  setGradeForm,
  canWrite,
  onSaved,
}: {
  product: Product;
  gradeForm: { id: number | null; grade: string };
  setGradeForm: React.Dispatch<React.SetStateAction<{ id: number | null; grade: string }>>;
  canWrite: boolean;
  onSaved: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  async function handleSaveGrade() {
    if (!gradeForm.grade.trim()) {
      message.error("Grade name is required.");
      return;
    }
    setSaving(true);
    try {
      if (gradeForm.id) {
        await updateProductGrade(product.id, gradeForm.id, { grade: gradeForm.grade });
        message.success("Grade updated.");
      } else {
        await createProductGrade(product.id, { grade: gradeForm.grade });
        message.success("Grade added.");
      }
      setGradeForm({ id: null, grade: "" });
      onSaved();
    } catch (err: unknown) {
      message.error(extractApiError(err, "Failed to save grade."));
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivateGrade(gradeId: number) {
    setSaving(true);
    try {
      await updateProductGrade(product.id, gradeId, { is_active: false });
      message.success("Grade deactivated.");
      onSaved();
    } catch (err: unknown) {
      message.error(extractApiError(err, "Failed to deactivate grade."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ paddingTop: 12 }}>
      <div
        style={{
          fontFamily: "var(--font-body)",
          fontSize: 12,
          fontWeight: 600,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          marginBottom: 10,
        }}
      >
        Grades for {product.name}
      </div>

      {/* Grade list */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 14 }}>
        {product.grades.length === 0 && (
          <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
            No grades defined yet.
          </p>
        )}
        {product.grades.map((g) => (
          <div
            key={g.id}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "6px 10px",
              background: "var(--bg-surface)",
              border: "1px solid var(--border-light)",
              borderRadius: 6,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-primary)" }}>
                {g.grade}
              </span>
              {!g.is_active && (
                <span className="chip-pink" style={{ fontSize: 10 }}>Inactive</span>
              )}
            </div>
            {canWrite && g.is_active && (
              <div style={{ display: "flex", gap: 6 }}>
                <button
                  onClick={() => setGradeForm({ id: g.id ?? null, grade: g.grade })}
                  style={{
                    padding: "3px 8px", background: "transparent",
                    border: "1px solid var(--border-medium)", borderRadius: 5,
                    fontFamily: "var(--font-body)", fontSize: 11, cursor: "pointer",
                    color: "var(--text-secondary)",
                  }}
                >
                  Edit
                </button>
                <button
                  onClick={() => navigate(`/master-data/products/${product.id}/grades/${g.id}/template`)}
                  style={{
                    padding: "3px 8px", background: "transparent",
                    border: "1px solid var(--border-medium)", borderRadius: 5,
                    fontFamily: "var(--font-body)", fontSize: 11, cursor: "pointer",
                    color: "var(--pastel-blue-text)",
                  }}
                >
                  Edit Template
                </button>
                <button
                  onClick={() => g.id && handleDeactivateGrade(g.id)}
                  disabled={saving}
                  style={{
                    padding: "3px 8px", background: "transparent",
                    border: "1px solid var(--border-medium)", borderRadius: 5,
                    fontFamily: "var(--font-body)", fontSize: 11, cursor: "pointer",
                    color: "var(--pastel-pink-text)",
                  }}
                >
                  Deactivate
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add / edit grade form */}
      {canWrite && (
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="text"
            value={gradeForm.grade}
            onChange={(e) => setGradeForm((f) => ({ ...f, grade: e.target.value }))}
            placeholder="Grade name, e.g. LR Grade"
            style={{
              flex: 1, padding: "7px 10px", borderRadius: 6,
              border: "1px solid var(--border-medium)", fontFamily: "var(--font-body)",
              fontSize: 13, color: "var(--text-primary)", background: "var(--bg-surface)",
              outline: "none",
            }}
            onKeyDown={(e) => { if (e.key === "Enter") handleSaveGrade(); }}
          />
          <button
            onClick={handleSaveGrade}
            disabled={saving}
            style={{
              padding: "7px 14px", background: "var(--primary)", color: "#fff",
              border: "none", borderRadius: 6, fontFamily: "var(--font-body)",
              fontSize: 13, fontWeight: 500, cursor: saving ? "not-allowed" : "pointer",
              opacity: saving ? 0.6 : 1,
            }}
          >
            {gradeForm.id ? "Update" : "Add Grade"}
          </button>
          {gradeForm.id && (
            <button
              onClick={() => setGradeForm({ id: null, grade: "" })}
              style={{
                padding: "7px 10px", background: "transparent",
                border: "1px solid var(--border-medium)", borderRadius: 6,
                fontFamily: "var(--font-body)", fontSize: 13, cursor: "pointer",
                color: "var(--text-secondary)",
              }}
            >
              Cancel
            </button>
          )}
        </div>
      )}
    </div>
  );
}
