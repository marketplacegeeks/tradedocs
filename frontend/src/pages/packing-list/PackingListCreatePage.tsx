// Packing List + CI creation page — FR-14M.
// 5-step wizard: 1) Header & Parties, 2) Order References,
//                3) Shipping & Logistics, 4) Containers & Items, 5) Final Rates

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Select, DatePicker, message, Modal } from "antd";
import { Plus, Trash2, Copy, ChevronRight, ChevronLeft } from "lucide-react";
import dayjs from "dayjs";

import {
  createPackingList,
  createContainer,
  updateContainer,
  deleteContainer,
  copyContainer,
  createContainerItem,
  updateContainerItem,
  deleteContainerItem,
  updateCILineItem,
  getCommercialInvoice,
} from "../../api/packingLists";
import type { PackingList, Container, ContainerItem } from "../../api/packingLists";
import { listOrganisations } from "../../api/organisations";
import { listIncoterms, listPaymentTerms, listUOMs, listPorts, listLocations, listPreCarriageBy } from "../../api/referenceData";
import { listCountries } from "../../api/countries";
import { listBanks } from "../../api/banks";
import { listProformaInvoices } from "../../api/proformaInvoices";
import { DOCUMENT_STATUS, INCOTERM_PL_FIELDS } from "../../utils/constants";

// ---- Styles -----------------------------------------------------------------

const PAGE: React.CSSProperties = {
  padding: 32,
  background: "var(--bg-base)",
  minHeight: "100vh",
};

const CARD: React.CSSProperties = {
  background: "var(--bg-surface)",
  borderRadius: 14,
  border: "1px solid var(--border-light)",
  boxShadow: "var(--shadow-card)",
  padding: "24px 28px",
  marginBottom: 20,
};

const SECTION_TITLE: React.CSSProperties = {
  fontFamily: "var(--font-heading)",
  fontSize: 15,
  fontWeight: 600,
  color: "var(--text-primary)",
  marginBottom: 16,
  marginTop: 0,
};

const LABEL: React.CSSProperties = {
  display: "block",
  fontFamily: "var(--font-body)",
  fontSize: 12,
  fontWeight: 500,
  color: "var(--text-muted)",
  marginBottom: 6,
};

const INPUT: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-input)",
  border: "1px solid var(--border-medium)",
  borderRadius: 8,
  padding: "9px 12px",
  fontFamily: "var(--font-body)",
  fontSize: 14,
  color: "var(--text-primary)",
  outline: "none",
  boxSizing: "border-box" as const,
};

const FORM_ROW: React.CSSProperties = {
  display: "grid",
  gap: 16,
  marginBottom: 16,
};

const BTN_PRIMARY: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "10px 20px",
  borderRadius: 8,
  border: "none",
  background: "var(--primary)",
  color: "#fff",
  fontFamily: "var(--font-body)",
  fontSize: 14,
  fontWeight: 500,
  cursor: "pointer",
};

const BTN_SECONDARY: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "10px 20px",
  borderRadius: 8,
  border: "1px solid var(--border-medium)",
  background: "var(--bg-surface)",
  color: "var(--text-secondary)",
  fontFamily: "var(--font-body)",
  fontSize: 14,
  fontWeight: 500,
  cursor: "pointer",
};

const TH: React.CSSProperties = {
  padding: "10px 12px",
  fontFamily: "var(--font-body)",
  fontSize: 11,
  fontWeight: 600,
  color: "var(--text-muted)",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  background: "var(--bg-base)",
  borderBottom: "1px solid var(--border-light)",
  textAlign: "left" as const,
};

const TD: React.CSSProperties = {
  padding: "10px 12px",
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-secondary)",
  borderBottom: "1px solid var(--border-light)",
  verticalAlign: "middle",
};

// ---- Step indicators --------------------------------------------------------

const STEP_LABELS = [
  "Header & Parties",
  "Order References",
  "Shipping & Logistics",
  "Containers & Items",
  "Final Rates",
];

function StepBar({ current }: { current: number }) {
  return (
    <div style={{ display: "flex", gap: 0, marginBottom: 28 }}>
      {STEP_LABELS.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", position: "relative" }}>
            {i > 0 && (
              <div style={{
                position: "absolute", top: 16, left: 0, right: "50%",
                height: 2, background: done ? "var(--primary)" : "var(--border-light)",
              }} />
            )}
            {i < STEP_LABELS.length - 1 && (
              <div style={{
                position: "absolute", top: 16, left: "50%", right: 0,
                height: 2, background: done ? "var(--primary)" : "var(--border-light)",
              }} />
            )}
            <div style={{
              width: 32, height: 32, borderRadius: "50%",
              background: active ? "var(--primary)" : done ? "var(--primary)" : "var(--bg-base)",
              border: `2px solid ${active || done ? "var(--primary)" : "var(--border-medium)"}`,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 600,
              color: active || done ? "#fff" : "var(--text-muted)",
              zIndex: 1, position: "relative",
            }}>
              {i + 1}
            </div>
            <span style={{
              marginTop: 8,
              fontFamily: "var(--font-body)", fontSize: 12,
              color: active ? "var(--primary)" : done ? "var(--text-secondary)" : "var(--text-muted)",
              fontWeight: active ? 600 : 400,
              textAlign: "center",
            }}>
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ---- Step 1: Header & Parties -----------------------------------------------

function Step1({
  form, setForm, onNext,
}: {
  form: Record<string, any>;
  setForm: (f: Record<string, any>) => void;
  onNext: (pl: PackingList) => void;
}) {
  const [saving, setSaving] = useState(false);

  const { data: organisations = [] } = useQuery({
    queryKey: ["organisations"],
    queryFn: () => listOrganisations(),
  });
  const { data: piList = [] } = useQuery({
    queryKey: ["proforma-invoices", "APPROVED"],
    queryFn: () => listProformaInvoices({ status: DOCUMENT_STATUS.APPROVED }),
  });
  const { data: banks = [] } = useQuery({
    queryKey: ["banks"],
    queryFn: () => listBanks(),
  });

  const exporters = organisations.filter((o: any) => o.tags?.includes("EXPORTER"));
  const consignees = organisations.filter((o: any) => o.tags?.includes("CONSIGNEE"));
  const buyers = organisations.filter((o: any) => o.tags?.includes("BUYER"));
  const notifyParties = organisations.filter((o: any) => o.tags?.includes("NOTIFY_PARTY"));

  async function handleSave() {
    if (!form.proforma_invoice || !form.exporter || !form.consignee) {
      message.error("Proforma Invoice, Exporter, and Consignee are required.");
      return;
    }
    setSaving(true);
    try {
      const pl = await createPackingList({
        proforma_invoice: form.proforma_invoice,
        pl_date: form.pl_date || dayjs().format("YYYY-MM-DD"),
        ci_date: form.ci_date || dayjs().format("YYYY-MM-DD"),
        exporter: form.exporter,
        consignee: form.consignee,
        buyer: form.buyer || null,
        notify_party: form.notify_party || null,
        bank: form.bank || null,
      });
      onNext(pl);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.response?.data?.proforma_invoice || "Failed to create.";
      message.error(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setSaving(false);
    }
  }

  const selectedPi = piList.find((pi: any) => pi.id === form.proforma_invoice);

  return (
    <div style={CARD}>
      <p style={SECTION_TITLE}>Header & Parties</p>

      <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr" }}>
        <div>
          <label style={LABEL}>Consignee (to filter PIs) *</label>
          <Select
            showSearch
            style={{ width: "100%" }}
            placeholder="Select Consignee first"
            value={form.consignee}
            onChange={(v) => setForm({ ...form, consignee: v, proforma_invoice: undefined })}
            options={consignees.map((o: any) => ({ value: o.id, label: o.name }))}
            filterOption={(input, opt) => (opt?.label ?? "").toLowerCase().includes(input.toLowerCase())}
          />
        </div>
        <div>
          <label style={LABEL}>Proforma Invoice *</label>
          <Select
            showSearch
            style={{ width: "100%" }}
            placeholder="Select approved PI"
            value={form.proforma_invoice}
            onChange={(v) => {
              const pi = piList.find((p: any) => p.id === v);
              if (pi) {
                setForm({
                  ...form,
                  proforma_invoice: v,
                  exporter: pi.exporter,
                  buyer: pi.buyer,
                });
              }
            }}
            options={piList
              .filter((pi: any) => !form.consignee || pi.consignee === form.consignee)
              .map((pi: any) => ({ value: pi.id, label: pi.pi_number }))}
            filterOption={(input, opt) => (opt?.label ?? "").toLowerCase().includes(input.toLowerCase())}
          />
        </div>
      </div>

      {/* PI Preview card */}
      {selectedPi && (
        <div style={{ background: "var(--pastel-blue)", borderRadius: 10, padding: "12px 16px", marginBottom: 16 }}>
          <p style={{ margin: "0 0 8px", fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 600, color: "var(--pastel-blue-text)" }}>
            PI Preview — {selectedPi.pi_number}
          </p>
          {(selectedPi.line_items ?? []).length === 0 ? (
            <p style={{ margin: 0, fontFamily: "var(--font-body)", fontSize: 12, color: "var(--text-muted)" }}>No line items on this PI.</p>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {["Item Code", "Description", "HSN Code", "Quantity"].map((h) => (
                    <th key={h} style={{ ...TH, background: "transparent", fontSize: 10 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(selectedPi.line_items ?? []).map((li: any) => (
                  <tr key={li.id}>
                    <td style={{ ...TD, fontSize: 12 }}>{li.item_code}</td>
                    <td style={{ ...TD, fontSize: 12 }}>{li.description}</td>
                    <td style={{ ...TD, fontSize: 12 }}>{li.hsn_code || "—"}</td>
                    <td style={{ ...TD, fontSize: 12 }}>{li.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr 1fr 1fr" }}>
        <div>
          <label style={LABEL}>Exporter *</label>
          <Select
            style={{ width: "100%" }}
            value={form.exporter}
            onChange={(v) => setForm({ ...form, exporter: v })}
            options={exporters.map((o: any) => ({ value: o.id, label: o.name }))}
          />
        </div>
        <div>
          <label style={LABEL}>Buyer (optional)</label>
          <Select
            allowClear
            style={{ width: "100%" }}
            value={form.buyer}
            onChange={(v) => setForm({ ...form, buyer: v })}
            options={buyers.map((o: any) => ({ value: o.id, label: o.name }))}
          />
        </div>
        <div>
          <label style={LABEL}>Notify Party (optional)</label>
          <Select
            allowClear
            style={{ width: "100%" }}
            value={form.notify_party}
            onChange={(v) => setForm({ ...form, notify_party: v })}
            options={notifyParties.map((o: any) => ({ value: o.id, label: o.name }))}
          />
        </div>
        <div>
          <label style={LABEL}>Bank (for CI)</label>
          <Select
            allowClear
            style={{ width: "100%" }}
            value={form.bank}
            onChange={(v) => setForm({ ...form, bank: v })}
            options={banks.map((b: any) => ({ value: b.id, label: `${b.bank_name} – ${b.beneficiary_name}` }))}
          />
        </div>
      </div>

      <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr" }}>
        <div>
          <label style={LABEL}>Packing List Date</label>
          <DatePicker
            style={{ width: "100%" }}
            value={form.pl_date ? dayjs(form.pl_date) : dayjs()}
            onChange={(d) => setForm({ ...form, pl_date: d?.format("YYYY-MM-DD") })}
          />
        </div>
        <div>
          <label style={LABEL}>Commercial Invoice Date</label>
          <DatePicker
            style={{ width: "100%" }}
            value={form.ci_date ? dayjs(form.ci_date) : dayjs()}
            onChange={(d) => setForm({ ...form, ci_date: d?.format("YYYY-MM-DD") })}
          />
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
        <button style={BTN_PRIMARY} onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save & Continue"}
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}

// ---- Step 2: Order References -----------------------------------------------

function Step2({
  pl, form, setForm, onNext, onBack,
}: {
  pl: PackingList;
  form: Record<string, any>;
  setForm: (f: Record<string, any>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      const { updatePackingList } = await import("../../api/packingLists");
      await updatePackingList(pl.id, {
        po_number: form.po_number || "",
        po_date: form.po_date || null,
        lc_number: form.lc_number || "",
        lc_date: form.lc_date || null,
        bl_number: form.bl_number || "",
        bl_date: form.bl_date || null,
        so_number: form.so_number || "",
        so_date: form.so_date || null,
        other_references: form.other_references || "",
        other_references_date: form.other_references_date || null,
        additional_description: form.additional_description || "",
      });
      onNext();
    } catch {
      message.error("Failed to save references.");
    } finally {
      setSaving(false);
    }
  }

  function ref(key: string, label: string) {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
        <div>
          <label style={LABEL}>{label} Number</label>
          <input style={INPUT} value={form[key] || ""} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
        </div>
        <div>
          <label style={LABEL}>{label} Date</label>
          <DatePicker
            style={{ width: "100%" }}
            value={form[`${key.replace("_number", "")}_date`] ? dayjs(form[`${key.replace("_number", "")}_date`]) : null}
            onChange={(d) => setForm({ ...form, [`${key.replace("_number", "")}_date`]: d?.format("YYYY-MM-DD") })}
          />
        </div>
      </div>
    );
  }

  return (
    <div style={CARD}>
      <p style={SECTION_TITLE}>Order References (all optional)</p>
      {ref("po_number", "PO")}
      {ref("lc_number", "LC")}
      {ref("bl_number", "BL")}
      {ref("so_number", "SO")}
      <div style={{ marginBottom: 12 }}>
        <label style={LABEL}>Other References</label>
        <input style={INPUT} value={form.other_references || ""} onChange={(e) => setForm({ ...form, other_references: e.target.value })} />
      </div>
      <div style={{ marginBottom: 16 }}>
        <label style={LABEL}>Additional Description</label>
        <textarea style={{ ...INPUT, minHeight: 80, resize: "vertical" }} value={form.additional_description || ""} onChange={(e) => setForm({ ...form, additional_description: e.target.value })} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        <button style={BTN_SECONDARY} onClick={onBack}><ChevronLeft size={14} /> Back</button>
        <button style={BTN_PRIMARY} onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save & Continue"} <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}

// ---- Step 3: Shipping & Logistics -------------------------------------------

function Step3({
  pl, form, setForm, onNext, onBack,
}: {
  pl: PackingList;
  form: Record<string, any>;
  setForm: (f: Record<string, any>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const [saving, setSaving] = useState(false);

  const { data: ports = [] } = useQuery({ queryKey: ["ports"], queryFn: listPorts });
  const { data: locations = [] } = useQuery({ queryKey: ["locations"], queryFn: listLocations });
  const { data: preCarriage = [] } = useQuery({ queryKey: ["pre-carriage"], queryFn: listPreCarriageBy });
  const { data: countries = [] } = useQuery({ queryKey: ["countries"], queryFn: listCountries });

  async function handleSave() {
    setSaving(true);
    try {
      const { updatePackingList } = await import("../../api/packingLists");
      await updatePackingList(pl.id, {
        pre_carriage_by: form.pre_carriage_by || null,
        place_of_receipt: form.place_of_receipt || null,
        place_of_receipt_by_pre_carrier: form.place_of_receipt_by_pre_carrier || null,
        vessel_flight_no: form.vessel_flight_no || "",
        port_of_loading: form.port_of_loading || null,
        port_of_discharge: form.port_of_discharge || null,
        final_destination: form.final_destination || null,
        country_of_origin: form.country_of_origin || null,
        country_of_final_destination: form.country_of_final_destination || null,
      });
      onNext();
    } catch {
      message.error("Failed to save shipping details.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={CARD}>
      <p style={SECTION_TITLE}>Shipping & Logistics (all optional)</p>
      <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr 1fr" }}>
        <div>
          <label style={LABEL}>Pre-Carriage By</label>
          <Select allowClear style={{ width: "100%" }} value={form.pre_carriage_by}
            onChange={(v) => setForm({ ...form, pre_carriage_by: v })}
            options={preCarriage.map((p: any) => ({ value: p.id, label: p.name }))} />
        </div>
        <div>
          <label style={LABEL}>Place of Receipt</label>
          <Select allowClear showSearch style={{ width: "100%" }} value={form.place_of_receipt}
            onChange={(v) => setForm({ ...form, place_of_receipt: v })}
            options={locations.map((l: any) => ({ value: l.id, label: l.name }))}
            filterOption={(i, o) => (o?.label ?? "").toLowerCase().includes(i.toLowerCase())} />
        </div>
        <div>
          <label style={LABEL}>Place of Receipt by Pre-Carrier</label>
          <Select allowClear showSearch style={{ width: "100%" }} value={form.place_of_receipt_by_pre_carrier}
            onChange={(v) => setForm({ ...form, place_of_receipt_by_pre_carrier: v })}
            options={locations.map((l: any) => ({ value: l.id, label: l.name }))}
            filterOption={(i, o) => (o?.label ?? "").toLowerCase().includes(i.toLowerCase())} />
        </div>
        <div>
          <label style={LABEL}>Vessel / Flight No</label>
          <input style={INPUT} value={form.vessel_flight_no || ""} onChange={(e) => setForm({ ...form, vessel_flight_no: e.target.value })} />
        </div>
        <div>
          <label style={LABEL}>Port of Loading</label>
          <Select allowClear showSearch style={{ width: "100%" }} value={form.port_of_loading}
            onChange={(v) => setForm({ ...form, port_of_loading: v })}
            options={ports.map((p: any) => ({ value: p.id, label: p.name }))}
            filterOption={(i, o) => (o?.label ?? "").toLowerCase().includes(i.toLowerCase())} />
        </div>
        <div>
          <label style={LABEL}>Port of Discharge</label>
          <Select allowClear showSearch style={{ width: "100%" }} value={form.port_of_discharge}
            onChange={(v) => setForm({ ...form, port_of_discharge: v })}
            options={ports.map((p: any) => ({ value: p.id, label: p.name }))}
            filterOption={(i, o) => (o?.label ?? "").toLowerCase().includes(i.toLowerCase())} />
        </div>
        <div>
          <label style={LABEL}>Final Destination</label>
          <Select allowClear showSearch style={{ width: "100%" }} value={form.final_destination}
            onChange={(v) => setForm({ ...form, final_destination: v })}
            options={locations.map((l: any) => ({ value: l.id, label: l.name }))}
            filterOption={(i, o) => (o?.label ?? "").toLowerCase().includes(i.toLowerCase())} />
        </div>
        <div>
          <label style={LABEL}>Country of Origin of Goods</label>
          <Select allowClear showSearch style={{ width: "100%" }} value={form.country_of_origin}
            onChange={(v) => setForm({ ...form, country_of_origin: v })}
            options={countries.map((c: any) => ({ value: c.id, label: c.name }))}
            filterOption={(i, o) => (o?.label ?? "").toLowerCase().includes(i.toLowerCase())} />
        </div>
        <div>
          <label style={LABEL}>Country of Final Destination</label>
          <Select allowClear showSearch style={{ width: "100%" }} value={form.country_of_final_destination}
            onChange={(v) => setForm({ ...form, country_of_final_destination: v })}
            options={countries.map((c: any) => ({ value: c.id, label: c.name }))}
            filterOption={(i, o) => (o?.label ?? "").toLowerCase().includes(i.toLowerCase())} />
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        <button style={BTN_SECONDARY} onClick={onBack}><ChevronLeft size={14} /> Back</button>
        <button style={BTN_PRIMARY} onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save & Continue"} <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}

// ---- Step 4: Containers & Items ---------------------------------------------

function Step4({
  pl, onNext, onBack,
}: {
  pl: PackingList;
  onNext: (refreshedPl: PackingList) => void;
  onBack: () => void;
}) {
  const queryClient = useQueryClient();
  const [addingItem, setAddingItem] = useState<{ containerId: number } | null>(null);
  const [itemForm, setItemForm] = useState<Record<string, any>>({});

  const { data: uoms = [] } = useQuery({ queryKey: ["uoms"], queryFn: listUOMs });

  const { data: currentPl } = useQuery({
    queryKey: ["packing-list", pl.id],
    queryFn: () => import("../../api/packingLists").then((m) => m.getPackingList(pl.id)),
  });

  const containers = currentPl?.containers ?? pl.containers ?? [];

  async function addContainer() {
    try {
      await createContainer({
        packing_list: pl.id,
        container_ref: "",
        marks_numbers: "",
        seal_number: "",
        tare_weight: "0.000",
      });
      queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
    } catch {
      message.error("Failed to add container.");
    }
  }

  async function removeContainer(id: number) {
    try {
      await deleteContainer(id);
      queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
    } catch {
      message.error("Cannot remove container.");
    }
  }

  async function handleCopy(id: number) {
    try {
      await copyContainer(id);
      queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
    } catch {
      message.error("Failed to copy container.");
    }
  }

  async function saveItem() {
    if (!addingItem) return;
    if (!itemForm.item_code || !itemForm.uom || !itemForm.quantity || !itemForm.net_weight || !itemForm.inner_packing_weight || !itemForm.packages_kind || !itemForm.description) {
      message.error("Item Code, Packages, Description, UOM, Quantity, Net Weight, and Inner Packing Weight are required.");
      return;
    }
    try {
      await createContainerItem({
        container: addingItem.containerId,
        hsn_code: itemForm.hsn_code || "",
        item_code: itemForm.item_code,
        packages_kind: itemForm.packages_kind,
        description: itemForm.description,
        batch_details: itemForm.batch_details || "",
        uom: itemForm.uom,
        quantity: itemForm.quantity,
        net_weight: itemForm.net_weight,
        inner_packing_weight: itemForm.inner_packing_weight,
      });
      setAddingItem(null);
      setItemForm({});
      queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
      message.success("Item added.");
    } catch (err: any) {
      const detail = err?.response?.data || "Failed to add item.";
      message.error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
  }

  async function removeItem(id: number) {
    try {
      await deleteContainerItem(id);
      queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
    } catch {
      message.error("Cannot remove item.");
    }
  }

  async function handleNext() {
    if (containers.length === 0) {
      message.error("At least one container is required.");
      return;
    }
    for (const c of containers) {
      if (!c.items || c.items.length === 0) {
        message.error(`Container "${c.container_ref || "unnamed"}" must have at least one item.`);
        return;
      }
    }
    const refreshed = currentPl ?? pl;
    onNext(refreshed);
  }

  return (
    <div style={CARD}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <p style={{ ...SECTION_TITLE, margin: 0 }}>Containers & Items</p>
        <button style={BTN_PRIMARY} onClick={addContainer}>
          <Plus size={14} /> Add Container
        </button>
      </div>

      {containers.length === 0 && (
        <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)", marginBottom: 16 }}>
          No containers yet. Add at least one container.
        </p>
      )}

      {containers.map((c, idx) => (
        <div key={c.id} style={{ border: "1px solid var(--border-light)", borderRadius: 10, padding: 16, marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <span style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: 14 }}>
              Container {idx + 1}
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <button style={{ ...BTN_SECONDARY, padding: "6px 12px", fontSize: 12 }} onClick={() => handleCopy(c.id)}>
                <Copy size={12} /> Copy
              </button>
              <button style={{ ...BTN_SECONDARY, padding: "6px 12px", fontSize: 12, color: "var(--pastel-pink-text)" }} onClick={() => removeContainer(c.id)}>
                <Trash2 size={12} />
              </button>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 12, marginBottom: 12 }}>
            {[
              ["container_ref", "Container Ref *"],
              ["marks_numbers", "Marks & Numbers *"],
              ["seal_number", "Seal Number *"],
              ["tare_weight", "Tare Weight (kg) *"],
            ].map(([field, label]) => (
              <div key={field}>
                <label style={LABEL}>{label}</label>
                <input
                  style={INPUT}
                  defaultValue={(c as any)[field]}
                  onBlur={(e) => updateContainer(c.id, { [field]: e.target.value }).then(() =>
                    queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] })
                  )}
                />
              </div>
            ))}
          </div>

          {/* Items table */}
          {c.items && c.items.length > 0 && (
            <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 12 }}>
              <thead>
                <tr>
                  <th style={TH}>Item Code</th>
                  <th style={TH}>Description</th>
                  <th style={TH}>HSN</th>
                  <th style={TH}>Pkgs</th>
                  <th style={TH}>Qty</th>
                  <th style={TH}>UOM</th>
                  <th style={TH}>Net Wt</th>
                  <th style={TH}>Inner Pkg Wt</th>
                  <th style={TH}></th>
                </tr>
              </thead>
              <tbody>
                {c.items.map((item) => (
                  <tr key={item.id}>
                    <td style={TD}>{item.item_code}</td>
                    <td style={TD}>{item.description}</td>
                    <td style={TD}>{item.hsn_code || "—"}</td>
                    <td style={TD}>{item.packages_kind}</td>
                    <td style={TD}>{item.quantity}</td>
                    <td style={TD}>{item.uom_abbr ?? item.uom ?? "—"}</td>
                    <td style={TD}>{item.net_weight}</td>
                    <td style={TD}>{item.inner_packing_weight}</td>
                    <td style={TD}>
                      <button style={{ background: "none", border: "none", cursor: "pointer", color: "var(--pastel-pink-text)" }} onClick={() => removeItem(item.id)}>
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <button
            style={{ ...BTN_SECONDARY, padding: "6px 14px", fontSize: 12 }}
            onClick={() => { setAddingItem({ containerId: c.id }); setItemForm({}); }}
          >
            <Plus size={12} /> Add Item
          </button>
        </div>
      ))}

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        <button style={BTN_SECONDARY} onClick={onBack}><ChevronLeft size={14} /> Back</button>
        <button style={BTN_PRIMARY} onClick={handleNext}>
          Save & Continue <ChevronRight size={14} />
        </button>
      </div>

      {/* Add item modal */}
      <Modal
        title="Add Item to Container"
        open={addingItem !== null}
        onOk={saveItem}
        onCancel={() => { setAddingItem(null); setItemForm({}); }}
        okText="Add Item"
        width={640}
      >
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {[
            ["item_code", "Item Code *", "text"],
            ["packages_kind", "No & Kind of Packages *", "text"],
            ["description", "Description *", "text"],
            ["hsn_code", "HSN Code", "text"],
            ["batch_details", "Batch Details", "text"],
            ["quantity", "Quantity *", "number"],
            ["net_weight", "Net Weight (kg) *", "number"],
            ["inner_packing_weight", "Inner Packing Weight (kg) *", "number"],
          ].map(([field, label, type]) => (
            <div key={field} style={field === "description" ? { gridColumn: "1 / -1" } : {}}>
              <label style={LABEL}>{label as string}</label>
              <input
                style={INPUT}
                type={type as string}
                value={itemForm[field as string] || ""}
                onChange={(e) => setItemForm({ ...itemForm, [field as string]: e.target.value })}
              />
            </div>
          ))}
          <div>
            <label style={LABEL}>UOM *</label>
            <Select
              style={{ width: "100%" }}
              value={itemForm.uom}
              onChange={(v) => setItemForm({ ...itemForm, uom: v })}
              options={uoms.map((u: any) => ({ value: u.id, label: `${u.name} (${u.abbreviation})` }))}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ---- Step 5: Final Rates ----------------------------------------------------

function Step5({
  pl, onDone, onBack,
}: {
  pl: PackingList;
  onDone: () => void;
  onBack: () => void;
}) {
  const [saving, setSaving] = useState(false);

  const { data: incoterms = [] } = useQuery({ queryKey: ["incoterms"], queryFn: listIncoterms });
  const { data: paymentTerms = [] } = useQuery({ queryKey: ["payment-terms"], queryFn: listPaymentTerms });

  const { data: ci } = useQuery({
    queryKey: ["commercial-invoice", pl.ci_id],
    queryFn: () => getCommercialInvoice(pl.ci_id!),
    enabled: pl.ci_id != null,
  });

  const queryClient = useQueryClient();
  const [rateForm, setRateForm] = useState<Record<number, string>>({});
  const [financials, setFinancials] = useState<Record<string, string>>({
    fob_rate: "",
    freight: "",
    insurance: "",
    lc_details: "",
    incoterms: String(pl.incoterms ?? ""),
    payment_terms: String(pl.payment_terms ?? ""),
  });

  // Derive which cost fields are visible based on the selected Incoterm code (FR-14M.8B).
  const selectedIncotermCode = incoterms.find((t: any) => t.id === Number(financials.incoterms))?.code ?? null;
  const visibleCostFields: Set<string> = selectedIncotermCode
    ? (INCOTERM_PL_FIELDS[selectedIncotermCode] ?? new Set(["fob_rate", "freight", "insurance"]))
    : new Set(["fob_rate", "freight", "insurance"]); // show all when no incoterm selected

  // When the incoterm changes, clear now-hidden fields from local state.
  function handleIncotermChange(incotermId: number | undefined) {
    const code = incoterms.find((t: any) => t.id === incotermId)?.code ?? null;
    const newVisible = code ? (INCOTERM_PL_FIELDS[code] ?? new Set(["fob_rate", "freight", "insurance"])) : new Set(["fob_rate", "freight", "insurance"]);
    setFinancials((prev) => ({
      ...prev,
      incoterms: incotermId ? String(incotermId) : "",
      fob_rate: newVisible.has("fob_rate") ? prev.fob_rate : "",
      freight: newVisible.has("freight") ? prev.freight : "",
      insurance: newVisible.has("insurance") ? prev.insurance : "",
    }));
  }

  async function handleSave() {
    if (!ci) return;
    setSaving(true);
    try {
      // Save each rate
      for (const [idStr, rate] of Object.entries(rateForm)) {
        await updateCILineItem(Number(idStr), { rate_usd: rate });
      }
      // Save financial fields on the PL (incoterms, payment_terms) and CI (fob_rate etc.)
      const { updatePackingList } = await import("../../api/packingLists");
      await updatePackingList(pl.id, {
        incoterms: financials.incoterms ? Number(financials.incoterms) : null,
        payment_terms: financials.payment_terms ? Number(financials.payment_terms) : null,
        fob_rate: financials.fob_rate || null,
        freight: financials.freight || null,
        insurance: financials.insurance || null,
        lc_details: financials.lc_details,
      });
      queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
      queryClient.invalidateQueries({ queryKey: ["commercial-invoice", pl.ci_id] });
      message.success("Rates saved.");
      onDone();
    } catch {
      message.error("Failed to save rates.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={CARD}>
      <p style={SECTION_TITLE}>Final Rates</p>

      {!ci || ci.line_items.length === 0 ? (
        <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)", marginBottom: 20 }}>
          No items found. Go back and add containers with items first.
        </p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 20 }}>
          <thead>
            <tr>
              <th style={TH}>Item Code</th>
              <th style={TH}>Description</th>
              <th style={TH}>Total Qty</th>
              <th style={TH}>UOM</th>
              <th style={TH}>Rate (USD per UOM) *</th>
              <th style={TH}>Amount (USD)</th>
            </tr>
          </thead>
          <tbody>
            {ci.line_items.map((li) => {
              const rate = rateForm[li.id] ?? li.rate_usd;
              const amount = (parseFloat(li.total_quantity) * parseFloat(rate || "0")).toFixed(2);
              return (
                <tr key={li.id}>
                  <td style={{ ...TD, fontWeight: 600 }}>{li.item_code}</td>
                  <td style={TD}>{li.description}</td>
                  <td style={TD}>{li.total_quantity}</td>
                  <td style={TD}>{li.uom_abbr ?? "—"}</td>
                  <td style={TD}>
                    <input
                      type="number"
                      style={{ ...INPUT, width: 120 }}
                      value={rate}
                      onChange={(e) => setRateForm({ ...rateForm, [li.id]: e.target.value })}
                    />
                  </td>
                  <td style={{ ...TD, fontWeight: 600 }}>${amount}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      <p style={{ ...SECTION_TITLE, marginTop: 24 }}>Payment & Terms</p>
      <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr" }}>
        <div>
          <label style={LABEL}>Incoterms</label>
          <Select allowClear style={{ width: "100%" }} value={financials.incoterms ? Number(financials.incoterms) : undefined}
            onChange={(v) => handleIncotermChange(v)}
            options={incoterms.map((t: any) => ({ value: t.id, label: `${t.code} – ${t.full_name}` }))} />
        </div>
        <div>
          <label style={LABEL}>Payment Terms</label>
          <Select allowClear style={{ width: "100%" }} value={financials.payment_terms ? Number(financials.payment_terms) : undefined}
            onChange={(v) => setFinancials({ ...financials, payment_terms: v ? String(v) : "" })}
            options={paymentTerms.map((t: any) => ({ value: t.id, label: t.name }))} />
        </div>
      </div>

      <p style={{ ...SECTION_TITLE, marginTop: 24 }}>Break-up in USD</p>
      <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr 1fr" }}>
        {visibleCostFields.has("fob_rate") && (
          <div>
            <label style={LABEL}>FOB Rate (USD per UOM)</label>
            <input type="number" style={INPUT} value={financials.fob_rate || ""} onChange={(e) => setFinancials({ ...financials, fob_rate: e.target.value })} />
          </div>
        )}
        {visibleCostFields.has("freight") && (
          <div>
            <label style={LABEL}>Freight (USD)</label>
            <input type="number" style={INPUT} value={financials.freight || ""} onChange={(e) => setFinancials({ ...financials, freight: e.target.value })} />
          </div>
        )}
        {visibleCostFields.has("insurance") && (
          <div>
            <label style={LABEL}>Insurance (USD)</label>
            <input type="number" style={INPUT} value={financials.insurance || ""} onChange={(e) => setFinancials({ ...financials, insurance: e.target.value })} />
          </div>
        )}
      </div>
      <div>
        <label style={LABEL}>L/C Details</label>
        <textarea style={{ ...INPUT, minHeight: 80, resize: "vertical" }} value={financials.lc_details || ""} onChange={(e) => setFinancials({ ...financials, lc_details: e.target.value })} />
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 24 }}>
        <button style={BTN_SECONDARY} onClick={onBack}><ChevronLeft size={14} /> Back</button>
        <button style={BTN_PRIMARY} onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save & Finish"} <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}

// ---- Main wizard ------------------------------------------------------------

export default function PackingListCreatePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<Record<string, any>>({});
  const [pl, setPl] = useState<PackingList | null>(null);

  function handleStep1Done(createdPl: PackingList) {
    setPl(createdPl);
    setStep(1);
  }

  return (
    <div style={PAGE}>
      <div style={{ marginBottom: 24 }}>
        <button
          onClick={() => navigate("/packing-lists")}
          style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4, fontFamily: "var(--font-body)", fontSize: 13, padding: 0, marginBottom: 12 }}
        >
          <ChevronLeft size={14} /> Back to Packing Lists
        </button>
        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
          New Packing List + Commercial Invoice
        </h1>
      </div>

      <StepBar current={step} />

      {step === 0 && (
        <Step1 form={form} setForm={setForm} onNext={handleStep1Done} />
      )}
      {step === 1 && pl && (
        <Step2 pl={pl} form={form} setForm={setForm} onNext={() => setStep(2)} onBack={() => setStep(0)} />
      )}
      {step === 2 && pl && (
        <Step3 pl={pl} form={form} setForm={setForm} onNext={() => setStep(3)} onBack={() => setStep(1)} />
      )}
      {step === 3 && pl && (
        <Step4 pl={pl} onNext={(refreshed) => { setPl(refreshed); setStep(4); }} onBack={() => setStep(2)} />
      )}
      {step === 4 && pl && (
        <Step5 pl={pl} onDone={() => navigate(`/packing-lists/${pl.id}`)} onBack={() => setStep(3)} />
      )}
    </div>
  );
}
