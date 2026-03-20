// FR-06 Reference Data page — single tabbed page for all 7 lookup entities.
// Checker and Company Admin can add, edit, and soft-delete records.
// All authenticated users can view.

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal, Select, message } from "antd";
import { Plus, Pencil, Trash2 } from "lucide-react";

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
} from "../../api/referenceData";
import type {
  Incoterm, IncotermPayload,
  UOM, UOMPayload,
  PaymentTerm, PaymentTermPayload,
  Port, PortPayload,
  Location, LocationPayload,
  PreCarriageBy, PreCarriageByPayload,
} from "../../api/referenceData";

// ---- Tab definitions --------------------------------------------------------

const TABS = [
  { key: "countries",     label: "Countries" },
  { key: "incoterms",     label: "Incoterms" },
  { key: "uom",           label: "UOM" },
  { key: "payment-terms", label: "Payment Terms" },
  { key: "ports",         label: "Ports" },
  { key: "locations",     label: "Locations" },
  { key: "pre-carriage",  label: "Pre-Carriage By" },
] as const;

type TabKey = typeof TABS[number]["key"];

// ---- Shared UI helpers ------------------------------------------------------

function TableHeader({ columns }: { columns: string[] }) {
  return (
    <thead>
      <tr style={{ background: "var(--bg-base)" }}>
        {columns.map((col) => (
          <th
            key={col}
            style={{
              padding: "12px 16px",
              textAlign: "left",
              fontFamily: "var(--font-body)",
              fontSize: 11,
              fontWeight: 600,
              textTransform: "uppercase" as const,
              letterSpacing: "0.06em",
              color: "var(--text-muted)",
              borderBottom: "1px solid var(--border-light)",
              whiteSpace: "nowrap" as const,
            }}
          >
            {col}
          </th>
        ))}
        <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
      </tr>
    </thead>
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

function EmptyState({ canWrite, onAdd }: { canWrite: boolean; onAdd: () => void }) {
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
  const canWrite = user?.role === ROLES.CHECKER || user?.role === ROLES.COMPANY_ADMIN;
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<TabKey>("countries");

  // Modal state: null = closed, "add" = add modal, number = edit modal for that ID
  const [modal, setModal] = useState<null | "add" | number>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Generic form state for each tab's add/edit modal
  const [form, setForm] = useState<Record<string, string>>({});

  function openAdd() {
    setForm({});
    setModal("add");
  }

  function openEdit(record: Record<string, unknown>) {
    // Seed the form with the record's current values (string-ified for input fields).
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

  // ---- Query & mutation helpers (per active tab) ---------------------------

  const queryKey = [activeTab];

  // Map tab key → list function
  const listFns: Record<TabKey, () => Promise<unknown[]>> = {
    "countries":     listCountries,
    "incoterms":     listIncoterms,
    "uom":           listUOMs,
    "payment-terms": listPaymentTerms,
    "ports":         listPorts,
    "locations":     listLocations,
    "pre-carriage":  listPreCarriageBy,
  };

  const { data: records = [], isLoading } = useQuery({
    queryKey,
    queryFn: listFns[activeTab] as () => Promise<Record<string, unknown>[]>,
  });

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
        // Create
        if (activeTab === "countries")     return createCountry(payload as CountryPayload);
        if (activeTab === "incoterms")     return createIncoterm(payload as IncotermPayload);
        if (activeTab === "uom")           return createUOM(payload as UOMPayload);
        if (activeTab === "payment-terms") return createPaymentTerm(payload as PaymentTermPayload);
        if (activeTab === "ports")         return createPort(payload as PortPayload);
        if (activeTab === "locations")     return createLocation(payload as LocationPayload);
        if (activeTab === "pre-carriage")  return createPreCarriageBy(payload as PreCarriageByPayload);
      } else if (typeof modal === "number") {
        // Update
        if (activeTab === "countries")     return updateCountry(modal, payload as Partial<CountryPayload>);
        if (activeTab === "incoterms")     return updateIncoterm(modal, payload as Partial<IncotermPayload>);
        if (activeTab === "uom")           return updateUOM(modal, payload as Partial<UOMPayload>);
        if (activeTab === "payment-terms") return updatePaymentTerm(modal, payload as Partial<PaymentTermPayload>);
        if (activeTab === "ports")         return updatePort(modal, payload as Partial<PortPayload>);
        if (activeTab === "locations")     return updateLocation(modal, payload as Partial<LocationPayload>);
        if (activeTab === "pre-carriage")  return updatePreCarriageBy(modal, payload as Partial<PreCarriageByPayload>);
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
      if (activeTab === "pre-carriage")  return deletePreCarriageBy(id);
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

  // ---- Table columns & row renderer per tab --------------------------------

  function renderTable() {
    if (isLoading) {
      return (
        <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-body)" }}>
          Loading…
        </div>
      );
    }
    if (records.length === 0) return <EmptyState canWrite={canWrite} onAdd={openAdd} />;

    const rows = records as Record<string, unknown>[];

    return (
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 500 }}>
          {activeTab === "countries" && (
            <>
              <TableHeader columns={["Country", "ISO2", "ISO3"]} />
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
              <TableHeader columns={["Code", "Full Name", "Description"]} />
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
              <TableHeader columns={["Name", "Abbreviation"]} />
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
              <TableHeader columns={["Name", "Description"]} />
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
              <TableHeader columns={["Port Name", "UN/LOCODE", "Country"]} />
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
              <TableHeader columns={["Location Name", "Country"]} />
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
              <TableHeader columns={["Carrier / Mode"]} />
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
        </table>
      </div>
    );
  }

  // ---- Modal form fields per tab ------------------------------------------

  // Countries available for Port/Location dropdowns
  const { data: allCountries = [] } = useQuery({
    queryKey: ["countries"],
    queryFn: listCountries,
  });

  function renderModalFields() {
    const countryOptions = (allCountries as Country[]).map((c) => ({ value: String(c.id), label: `${c.name} (${c.iso2})` }));

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
    }
  }

  const tabLabel = TABS.find((t) => t.key === activeTab)?.label ?? "";
  const isAdding = modal === "add";

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
            Lookup values used across all trade documents
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
          marginBottom: 20,
          borderBottom: "1px solid var(--border-light)",
          overflowX: "auto",
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setActiveTab(tab.key);
              closeModal();
              setDeletingId(null);
            }}
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
