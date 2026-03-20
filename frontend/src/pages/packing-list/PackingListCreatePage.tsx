// Packing List + CI creation page — FR-14M.
// Step 0: Consignee + PI selection (pre-wizard, no step bar)
// Steps 1–4 wizard: 1) Header & Details, 2) Order References,
//                   3) Containers & Items, 4) Final Rates

import { useState, useEffect } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Select, DatePicker, message } from "antd";
import { Plus, Trash2, Copy, ChevronRight, ChevronLeft } from "lucide-react";
import dayjs from "dayjs";

import {
  getPackingList,
  createPackingList,
  updatePackingList,
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

const INPUT_READONLY: React.CSSProperties = {
  ...INPUT,
  background: "var(--bg-base)",
  color: "var(--text-muted)",
  cursor: "not-allowed",
  borderColor: "var(--border-light)",
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

// ---- Step indicators (shown for steps 1–5 only) -----------------------------

const STEP_LABELS = [
  "Header & Details",
  "Order References",
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

// ---- Step 0: Consignee + PI selection (pre-wizard) --------------------------

function Step0({
  form, setForm, onContinue, onCancel,
}: {
  form: Record<string, any>;
  setForm: (f: Record<string, any>) => void;
  onContinue: () => void;
  onCancel: () => void;
}) {
  // Fetch all approved PIs once; derive consignees from that list.
  const { data: piList = [], isLoading } = useQuery({
    queryKey: ["proforma-invoices", "APPROVED"],
    queryFn: () => listProformaInvoices({ status: DOCUMENT_STATUS.APPROVED }),
  });

  // Build a deduplicated consignee list from the approved PI list.
  const consigneeMap = new Map<number, string>();
  for (const pi of piList as any[]) {
    if (!consigneeMap.has(pi.consignee)) {
      consigneeMap.set(pi.consignee, pi.consignee_name);
    }
  }
  const consignees = Array.from(consigneeMap.entries()).map(([id, name]) => ({ id, name }));

  // Approved PIs for the selected consignee, sorted most-recent first.
  const filteredPIs = (piList as any[])
    .filter((pi) => !form.consignee || pi.consignee === form.consignee)
    .sort((a, b) => {
      if (b.pi_date !== a.pi_date) return b.pi_date.localeCompare(a.pi_date);
      return b.pi_number.localeCompare(a.pi_number);
    });

  const selectedPi: any = (piList as any[]).find((pi) => pi.id === form.proforma_invoice);

  function handleConsigneeChange(v: number) {
    // Clearing the PI selection when consignee changes.
    setForm({ ...form, consignee: v, proforma_invoice: undefined, _selectedPi: undefined });
  }

  function handlePiChange(v: number) {
    const pi = (piList as any[]).find((p) => p.id === v);
    if (pi) {
      // Pre-populate all PI-derived fields so Step 1 shows them auto-filled and editable.
      setForm({
        ...form,
        proforma_invoice: v,
        exporter: pi.exporter,
        consignee: pi.consignee,
        buyer: pi.buyer ?? null,
        bank: pi.bank ?? null,
        pre_carriage_by: pi.pre_carriage_by ?? null,
        place_of_receipt: pi.place_of_receipt ?? null,
        place_of_receipt_by_pre_carrier: pi.place_of_receipt_by_pre_carrier ?? null,
        vessel_flight_no: pi.vessel_flight_no ?? "",
        port_of_loading: pi.port_of_loading ?? null,
        port_of_discharge: pi.port_of_discharge ?? null,
        final_destination: pi.final_destination ?? null,
        country_of_origin: pi.country_of_origin ?? null,
        country_of_final_destination: pi.country_of_final_destination ?? null,
        incoterms: pi.incoterms ?? null,
        payment_terms: pi.payment_terms ?? null,
        _selectedPi: pi,
      });
    }
  }

  function handleContinue() {
    if (!form.consignee) { message.error("Please select a Consignee."); return; }
    if (!form.proforma_invoice) { message.error("Please select a Proforma Invoice."); return; }
    onContinue();
  }

  return (
    <div>
      {/* Info banner */}
      <div style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-light)",
        borderRadius: 10,
        padding: "12px 16px",
        marginBottom: 24,
        fontFamily: "var(--font-body)",
        fontSize: 13,
        color: "var(--text-secondary)",
      }}>
        Select a Consignee, then select an Approved Proforma Invoice. All matching fields will be auto-populated from the PI.
      </div>

      <div style={CARD}>
        {/* Consignee */}
        <div style={{ marginBottom: 20 }}>
          <label style={{ ...LABEL, fontSize: 13, color: "var(--text-primary)" }}>
            Consignee <span style={{ color: "var(--error, #e53e3e)", fontWeight: 400 }}>*required</span>
          </label>
          <Select
            showSearch
            loading={isLoading}
            style={{ width: "100%" }}
            placeholder="Select Consignee"
            value={form.consignee}
            onChange={handleConsigneeChange}
            options={consignees.map((c) => ({ value: c.id, label: c.name }))}
            filterOption={(input, opt) => (opt?.label ?? "").toLowerCase().includes(input.toLowerCase())}
            size="large"
          />
          <p style={{ margin: "4px 0 0", fontFamily: "var(--font-body)", fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>
            Organisations tagged as Consignee
          </p>
        </div>

        {/* Proforma Invoice */}
        <div style={{ marginBottom: selectedPi ? 20 : 0 }}>
          <label style={{ ...LABEL, fontSize: 13, color: "var(--text-primary)" }}>
            Proforma Invoice <span style={{ color: "var(--error, #e53e3e)", fontWeight: 400 }}>*required</span>
          </label>
          <Select
            showSearch
            style={{ width: "100%" }}
            placeholder={form.consignee ? "Select approved PI" : "Select a Consignee first"}
            disabled={!form.consignee}
            value={form.proforma_invoice}
            onChange={handlePiChange}
            options={filteredPIs.map((pi, idx) => ({
              value: pi.id,
              label: `${pi.pi_number} (${dayjs(pi.pi_date).format("DD MMM YYYY")})${idx === 0 ? " ← most recent" : ""}`,
            }))}
            filterOption={(input, opt) => (opt?.label ?? "").toLowerCase().includes(input.toLowerCase())}
            size="large"
          />
          <p style={{ margin: "4px 0 0", fontFamily: "var(--font-body)", fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>
            Shows only Approved PIs for the selected Consignee. Searchable. Most recently approved PI appears first.
          </p>
        </div>

        {/* PI Preview — shown after a PI is selected */}
        {selectedPi && (
          <div style={{ border: "1px solid var(--border-light)", borderRadius: 10, overflow: "hidden", marginTop: 20 }}>
            <div style={{ background: "var(--bg-base)", padding: "10px 16px", borderBottom: "1px solid var(--border-light)" }}>
              <span style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                PI Preview (read-only — auto-populated from selected PI)
              </span>
            </div>
            <div style={{ padding: 16 }}>
              {/* Exporter + Consignee read-only */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                <div>
                  <label style={LABEL}>Exporter</label>
                  <div style={INPUT_READONLY}>{selectedPi.exporter_name || "—"}</div>
                </div>
                <div>
                  <label style={LABEL}>Consignee</label>
                  <div style={INPUT_READONLY}>{selectedPi.consignee_name || "—"}</div>
                </div>
              </div>

              {/* Line items table */}
              <p style={{ ...LABEL, fontWeight: 600, marginBottom: 8 }}>Line Items (from original PI)</p>
              {(selectedPi.line_items ?? []).length === 0 ? (
                <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)" }}>No line items on this PI.</p>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      {["Item Code", "Description", "HSN", "Qty"].map((h) => (
                        <th key={h} style={TH}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(selectedPi.line_items ?? []).map((li: any) => (
                      <tr key={li.id}>
                        <td style={TD}>{li.item_code}</td>
                        <td style={TD}>{li.description}</td>
                        <td style={TD}>{li.hsn_code || "—"}</td>
                        <td style={TD}>{li.quantity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 12 }}>
        <button style={BTN_SECONDARY} onClick={onCancel}>Cancel</button>
        <button
          style={{ ...BTN_PRIMARY, opacity: (!form.consignee || !form.proforma_invoice) ? 0.5 : 1 }}
          onClick={handleContinue}
          disabled={!form.consignee || !form.proforma_invoice}
        >
          Continue <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}

// ---- Step 1: Header & Details -----------------------------------------------
// Combined page: Document numbers (read-only), dates, parties, shipping &
// logistics, countries, and bank details. All fields auto-populated from the
// selected PI and remain editable. The PL record is created on save.

function Step1({
  form, setForm, onNext, onBack, existingPl,
}: {
  form: Record<string, any>;
  setForm: (f: Record<string, any>) => void;
  onNext: (pl: PackingList) => void;
  onBack: () => void;
  existingPl?: PackingList;
}) {
  const [saving, setSaving] = useState(false);

  const { data: exporters = [] } = useQuery({ queryKey: ["organisations", "EXPORTER"], queryFn: () => listOrganisations("EXPORTER") });
  const { data: consignees = [] } = useQuery({ queryKey: ["organisations", "CONSIGNEE"], queryFn: () => listOrganisations("CONSIGNEE") });
  const { data: buyers = [] } = useQuery({ queryKey: ["organisations", "BUYER"], queryFn: () => listOrganisations("BUYER") });
  const { data: notifyParties = [] } = useQuery({ queryKey: ["organisations", "NOTIFY_PARTY"], queryFn: () => listOrganisations("NOTIFY_PARTY") });
  const { data: banks = [] } = useQuery({ queryKey: ["banks"], queryFn: listBanks });
  const { data: ports = [] } = useQuery({ queryKey: ["ports"], queryFn: listPorts });
  const { data: locations = [] } = useQuery({ queryKey: ["locations"], queryFn: listLocations });
  const { data: preCarriage = [] } = useQuery({ queryKey: ["pre-carriage"], queryFn: listPreCarriageBy });
  const { data: countries = [] } = useQuery({ queryKey: ["countries"], queryFn: listCountries });

  // When editing, the saved organisation might not appear in the tag-filtered list (e.g. an exporter
  // not tagged as EXPORTER). This helper injects a fallback option so the Select always shows the
  // name rather than the raw ID.
  function withFallback(
    list: any[],
    currentId: number | null | undefined,
    currentName: string | null | undefined,
  ): { value: number; label: string }[] {
    const opts = list.map((o: any) => ({ value: o.id, label: o.name }));
    if (currentId && !opts.find((o) => o.value === currentId)) {
      opts.unshift({ value: currentId, label: currentName || String(currentId) });
    }
    return opts;
  }

  // Find the currently selected bank object to show its details in the preview card.
  const selectedBank: any = banks.find((b: any) => b.id === form.bank);

  async function handleSave() {
    if (!form.exporter || !form.consignee) {
      message.error("Exporter and Consignee are required.");
      return;
    }
    if (!existingPl && !form.proforma_invoice) {
      message.error("Proforma Invoice is required.");
      return;
    }
    setSaving(true);
    const sharedFields = {
      pl_date: form.pl_date || dayjs().format("YYYY-MM-DD"),
      ci_date: form.ci_date || dayjs().format("YYYY-MM-DD"),
      exporter: form.exporter,
      consignee: form.consignee,
      buyer: form.buyer || null,
      notify_party: form.notify_party || null,
      bank: form.bank || null,
      pre_carriage_by: form.pre_carriage_by || null,
      place_of_receipt: form.place_of_receipt || null,
      place_of_receipt_by_pre_carrier: form.place_of_receipt_by_pre_carrier || null,
      vessel_flight_no: form.vessel_flight_no || "",
      port_of_loading: form.port_of_loading || null,
      port_of_discharge: form.port_of_discharge || null,
      final_destination: form.final_destination || null,
      country_of_origin: form.country_of_origin || null,
      country_of_final_destination: form.country_of_final_destination || null,
      incoterms: form.incoterms || null,
      payment_terms: form.payment_terms || null,
    };
    try {
      let result: PackingList;
      if (existingPl) {
        result = await updatePackingList(existingPl.id, sharedFields);
      } else {
        result = await createPackingList({ proforma_invoice: form.proforma_invoice, ...sharedFields });
      }
      onNext(result);
    } catch (err: any) {
      const data = err?.response?.data;
      let errorMsg = existingPl ? "Failed to save." : "Failed to create.";
      if (data) {
        if (typeof data === "string") {
          errorMsg = data;
        } else if (typeof data === "object") {
          const parts = Object.entries(data).map(([field, msgs]) =>
            `${field}: ${Array.isArray(msgs) ? msgs.join(", ") : msgs}`
          );
          errorMsg = parts.join(" | ");
        }
      }
      message.error(errorMsg, 6);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      {/* ── Document Numbers & Dates ── */}
      <div style={CARD}>
        <p style={SECTION_TITLE}>Document Numbers &amp; Dates</p>
        <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr 1fr 1fr" }}>
          <div>
            <label style={LABEL}>Packing List No</label>
            <div style={INPUT_READONLY}>{existingPl ? existingPl.pl_number : "— generated on save —"}</div>
          </div>
          <div>
            <label style={LABEL}>Commercial Invoice No</label>
            <div style={INPUT_READONLY}>{existingPl ? (existingPl.ci_number || "—") : "— generated on save —"}</div>
          </div>
          <div>
            <label style={LABEL}>PL Date</label>
            <DatePicker
              style={{ width: "100%" }}
              value={form.pl_date ? dayjs(form.pl_date) : dayjs()}
              onChange={(d) => setForm({ ...form, pl_date: d?.format("YYYY-MM-DD") })}
            />
          </div>
          <div>
            <label style={LABEL}>CI Date</label>
            <DatePicker
              style={{ width: "100%" }}
              value={form.ci_date ? dayjs(form.ci_date) : dayjs()}
              onChange={(d) => setForm({ ...form, ci_date: d?.format("YYYY-MM-DD") })}
            />
          </div>
        </div>
      </div>

      {/* ── Parties ── */}
      <div style={CARD}>
        <p style={SECTION_TITLE}>Parties</p>
        <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr" }}>
          <div>
            <label style={LABEL}>Exporter *</label>
            <Select
              showSearch
              style={{ width: "100%" }}
              value={form.exporter}
              onChange={(v) => setForm({ ...form, exporter: v })}
              options={withFallback(exporters, existingPl?.exporter, existingPl?.exporter_name)}
              filterOption={(i, o) => (o?.label ?? "").toLowerCase().includes(i.toLowerCase())}
            />
          </div>
          <div>
            <label style={LABEL}>Consignee *</label>
            <Select
              showSearch
              style={{ width: "100%" }}
              value={form.consignee}
              onChange={(v) => setForm({ ...form, consignee: v })}
              options={withFallback(consignees, existingPl?.consignee, existingPl?.consignee_name)}
              filterOption={(i, o) => (o?.label ?? "").toLowerCase().includes(i.toLowerCase())}
            />
          </div>
        </div>
        <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr" }}>
          <div>
            <label style={LABEL}>Buyer (optional)</label>
            <Select
              allowClear
              style={{ width: "100%" }}
              value={form.buyer}
              onChange={(v) => setForm({ ...form, buyer: v })}
              options={withFallback(buyers, existingPl?.buyer, existingPl?.buyer_name)}
            />
          </div>
          <div>
            <label style={LABEL}>Notify Party (optional)</label>
            <Select
              allowClear
              style={{ width: "100%" }}
              value={form.notify_party}
              onChange={(v) => setForm({ ...form, notify_party: v })}
              options={withFallback(notifyParties, existingPl?.notify_party, existingPl?.notify_party_name)}
            />
          </div>
        </div>
      </div>

      {/* ── Shipping & Logistics ── */}
      <div style={CARD}>
        <p style={SECTION_TITLE}>Shipping &amp; Logistics</p>
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
            <input style={INPUT} value={form.vessel_flight_no || ""}
              onChange={(e) => setForm({ ...form, vessel_flight_no: e.target.value })} />
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
        </div>
      </div>

      {/* ── Countries ── */}
      <div style={CARD}>
        <p style={SECTION_TITLE}>Countries</p>
        <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr" }}>
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
      </div>

      {/* ── Bank Details ── */}
      <div style={CARD}>
        <p style={SECTION_TITLE}>Bank Details (for Commercial Invoice)</p>
        <div style={{ maxWidth: 480, marginBottom: selectedBank ? 16 : 0 }}>
          <label style={LABEL}>Bank *required</label>
          <Select
            allowClear
            showSearch
            style={{ width: "100%" }}
            placeholder="Select Bank (Bank Name – Beneficiary Name)"
            value={form.bank}
            onChange={(v) => setForm({ ...form, bank: v })}
            options={banks.map((b: any) => ({ value: b.id, label: `${b.bank_name} – ${b.beneficiary_name}` }))}
            filterOption={(i, o) => (o?.label ?? "").toLowerCase().includes(i.toLowerCase())}
          />
          <p style={{ margin: "4px 0 0", fontFamily: "var(--font-body)", fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>
            Full bank details (branch, account, IFSC, SWIFT) print on the CI PDF
          </p>
        </div>

        {/* Bank preview card — shown once a bank is selected */}
        {selectedBank && (
          <div style={{
            background: "var(--bg-base)",
            border: "1px solid var(--border-light)",
            borderRadius: 10,
            padding: "14px 18px",
            maxWidth: 480,
            lineHeight: 2,
          }}>
            <p style={{ ...LABEL, fontWeight: 600, marginBottom: 8 }}>Bank Details Preview (read-only)</p>
            <div style={{ fontFamily: "var(--font-body)", fontSize: 12, color: "var(--text-secondary)" }}>
              <div><strong>Beneficiary Name:</strong> {selectedBank.beneficiary_name}</div>
              <div><strong>Bank Name:</strong> {selectedBank.bank_name}</div>
              {selectedBank.branch_address && <div><strong>Branch Address:</strong> {selectedBank.branch_address}</div>}
              <div><strong>A/C No:</strong> {selectedBank.account_number}</div>
              {selectedBank.swift_code && <div><strong>SWIFT:</strong> {selectedBank.swift_code}</div>}
              {selectedBank.iban && <div><strong>IBAN:</strong> {selectedBank.iban}</div>}
              {selectedBank.routing_number && <div><strong>Routing No:</strong> {selectedBank.routing_number}</div>}
            </div>
          </div>
        )}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        <button style={BTN_SECONDARY} onClick={onBack}><ChevronLeft size={14} /> Back</button>
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
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
        <div>
          <label style={LABEL}>Other References</label>
          <input style={INPUT} value={form.other_references || ""} onChange={(e) => setForm({ ...form, other_references: e.target.value })} />
        </div>
        <div>
          <label style={LABEL}>Other References Date</label>
          <DatePicker
            style={{ width: "100%" }}
            value={form.other_references_date ? dayjs(form.other_references_date) : null}
            onChange={(d) => setForm({ ...form, other_references_date: d?.format("YYYY-MM-DD") })}
          />
        </div>
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

// ---- Step 3: Containers & Items (fully inline — no modals) ------------------
// Wireframe S07: containers use inline cards. S08/S09 removed — add/edit
// container fields and items are all done inline on this page.

function Step3({
  pl, onNext, onBack,
}: {
  pl: PackingList;
  onNext: (refreshedPl: PackingList) => void;
  onBack: () => void;
}) {
  const queryClient = useQueryClient();

  // pendingContainers: unsaved new container forms (dashed-border cards). Each entry embeds _item for the first item.
  // Start with one blank only if there are no saved containers yet (create mode first visit).
  // In edit mode (containers already exist), start empty so we don't force a blank form.
  const [pendingContainers, setPendingContainers] = useState<Record<string, any>[]>(
    (pl.containers?.length ?? 0) > 0 ? [] : [{ _item: {} }]
  );
  // pendingItems: unsaved new item rows, keyed by container ID
  const [pendingItems, setPendingItems] = useState<Record<number, Record<string, any>[]>>({});

  const { data: uoms = [] } = useQuery({ queryKey: ["uoms"], queryFn: listUOMs });

  const { data: currentPl } = useQuery({
    queryKey: ["packing-list", pl.id],
    queryFn: () => import("../../api/packingLists").then((m) => m.getPackingList(pl.id)),
  });

  const containers = currentPl?.containers ?? pl.containers ?? [];

  // Invalidate helper used by onBlur saves
  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
  }

  async function savePendingContainer(idx: number) {
    const { _item, ...c } = pendingContainers[idx];
    if (!c.container_ref || !c.marks_numbers || !c.seal_number || !c.tare_weight) {
      message.error("Container Ref, Marks & Numbers, Seal Number, and Tare Weight are required.");
      return;
    }
    const item = _item as Record<string, any> | undefined;
    const itemReady = item && item.item_code && item.uom && item.quantity && item.net_weight && item.inner_packing_weight && item.packages_kind && item.description;
    try {
      const newContainer = await createContainer({
        packing_list: pl.id,
        container_ref: c.container_ref,
        marks_numbers: c.marks_numbers,
        seal_number: c.seal_number,
        tare_weight: c.tare_weight,
      });
      setPendingContainers((prev) => prev.filter((_, i) => i !== idx));
      if (itemReady && item) {
        await createContainerItem({
          container: newContainer.id,
          hsn_code: item.hsn_code || "",
          item_code: item.item_code,
          packages_kind: item.packages_kind,
          description: item.description,
          batch_details: item.batch_details || "",
          uom: item.uom,
          quantity: item.quantity,
          net_weight: item.net_weight,
          inner_packing_weight: item.inner_packing_weight,
        });
        invalidate();
        message.success("Container and item added.");
      } else {
        invalidate();
        message.success("Container added. Add items below.");
        // Auto-open a pending item row for the new container
        setPendingItems((prev) => ({ ...prev, [newContainer.id]: [{}] }));
      }
    } catch {
      message.error("Failed to add container.");
    }
  }

  async function removeContainer(id: number) {
    try {
      await deleteContainer(id);
      invalidate();
    } catch {
      message.error("Cannot remove container.");
    }
  }

  async function handleCopy(id: number) {
    try {
      await copyContainer(id);
      invalidate();
    } catch {
      message.error("Failed to copy container.");
    }
  }

  function updatePendingItem(containerId: number, idx: number, patch: Record<string, any>) {
    setPendingItems((prev) => {
      const items = [...(prev[containerId] ?? [])];
      items[idx] = { ...items[idx], ...patch };
      return { ...prev, [containerId]: items };
    });
  }

  function removePendingItem(containerId: number, idx: number) {
    setPendingItems((prev) => {
      const items = (prev[containerId] ?? []).filter((_, i) => i !== idx);
      return { ...prev, [containerId]: items };
    });
  }

  async function savePendingItem(containerId: number, idx: number) {
    const item = (pendingItems[containerId] ?? [])[idx];
    if (!item || !item.item_code || !item.uom || !item.quantity || !item.net_weight || !item.inner_packing_weight || !item.packages_kind || !item.description) {
      message.error("Item Code, Packages, Description, UOM, Quantity, Net Weight, and Inner Packing Weight are required.");
      return;
    }
    try {
      await createContainerItem({
        container: containerId,
        hsn_code: item.hsn_code || "",
        item_code: item.item_code,
        packages_kind: item.packages_kind,
        description: item.description,
        batch_details: item.batch_details || "",
        uom: item.uom,
        quantity: item.quantity,
        net_weight: item.net_weight,
        inner_packing_weight: item.inner_packing_weight,
      });
      removePendingItem(containerId, idx);
      invalidate();
      message.success("Item added.");
    } catch (err: any) {
      const detail = err?.response?.data || "Failed to add item.";
      message.error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
  }

  async function removeItem(id: number) {
    try {
      await deleteContainerItem(id);
      invalidate();
    } catch {
      message.error("Cannot remove item.");
    }
  }

  async function handleNext() {
    if (containers.length === 0 && pendingContainers.length === 0) {
      message.error("At least one container is required.");
      return;
    }
    if (containers.length === 0) {
      message.error("Save your containers before continuing.");
      return;
    }
    for (const c of containers) {
      if (!c.items || c.items.length === 0) {
        message.error(`Container "${c.container_ref || "unnamed"}" must have at least one item.`);
        return;
      }
    }
    onNext(currentPl ?? pl);
  }

  // Header row for container field labels
  const containerHeaderStyle: React.CSSProperties = {
    padding: "4px 10px",
    background: "var(--bg-base)",
    color: "var(--text-muted)",
    borderRight: "1px solid var(--border-light)",
    fontSize: 10,
    fontFamily: "var(--font-body)",
    fontWeight: 600,
  };

  return (
    <div style={CARD}>
      <p style={SECTION_TITLE}>Containers &amp; Items</p>

      {/* ── Saved containers ── */}
      {containers.map((c, idx) => (
        <div
          key={c.id}
          style={{ border: "2px solid var(--border-medium)", borderRadius: 10, marginBottom: 16, overflow: "hidden" }}
        >
          {/* Container header bar */}
          <div style={{ background: "var(--primary-light)", color: "var(--primary)", padding: "8px 14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ background: "var(--primary)", color: "#fff", fontWeight: 700, width: 22, height: 22, display: "inline-flex", alignItems: "center", justifyContent: "center", borderRadius: 4, fontSize: 12, flexShrink: 0 }}>
                {idx + 1}
              </span>
              <span style={{ fontFamily: "var(--font-heading)", fontSize: 13, fontWeight: 600 }}>
                Container {c.container_ref ? `— ${c.container_ref}` : ""}
              </span>
              {(!c.items || c.items.length === 0) && (
                <span style={{ fontSize: 11, color: "var(--pastel-yellow-text)" }}>⚠ needs at least 1 item</span>
              )}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                style={{ padding: "4px 10px", fontSize: 11, borderRadius: 6, border: "1px solid var(--primary)", background: "transparent", color: "var(--primary)", cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 4 }}
                onClick={() => handleCopy(c.id)}
              >
                <Copy size={11} /> Copy Container
              </button>
              <button
                style={{ padding: "4px 10px", fontSize: 11, borderRadius: 6, border: "1px solid var(--error, #f87171)", background: "transparent", color: "var(--error, #f87171)", cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 4 }}
                onClick={() => removeContainer(c.id)}
              >
                <Trash2 size={11} /> Remove Container
              </button>
            </div>
          </div>

          {/* Field label headers row 1 */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
            <div style={containerHeaderStyle}>Container Reference *</div>
            <div style={{ ...containerHeaderStyle, borderRight: "none" }}>Marks and Numbers *</div>
          </div>
          {/* Field inputs row 1 */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", borderBottom: "1px solid var(--border-light)" }}>
            <div style={{ padding: "6px 10px", borderRight: "1px solid var(--border-light)" }}>
              <input
                style={{ ...INPUT, fontSize: 13 }}
                defaultValue={c.container_ref}
                onBlur={(e) => updateContainer(c.id, { container_ref: e.target.value }).then(invalidate)}
              />
            </div>
            <div style={{ padding: "6px 10px" }}>
              <input
                style={{ ...INPUT, fontSize: 13 }}
                defaultValue={c.marks_numbers}
                onBlur={(e) => updateContainer(c.id, { marks_numbers: e.target.value }).then(invalidate)}
              />
            </div>
          </div>

          {/* Field label headers row 2 */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr" }}>
            {["Tare Weight (kg) *", "Seal Number *", "Gross Weight (auto)"].map((h, i) => (
              <div key={h} style={{ ...containerHeaderStyle, borderRight: i < 2 ? "1px solid var(--border-light)" : "none" }}>{h}</div>
            ))}
          </div>
          {/* Field inputs row 2 */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", borderBottom: "1px solid var(--border-light)" }}>
            <div style={{ padding: "6px 10px", borderRight: "1px solid var(--border-light)" }}>
              <input
                style={{ ...INPUT, fontSize: 13 }}
                defaultValue={c.tare_weight}
                onBlur={(e) => updateContainer(c.id, { tare_weight: e.target.value }).then(invalidate)}
              />
            </div>
            <div style={{ padding: "6px 10px", borderRight: "1px solid var(--border-light)" }}>
              <input
                style={{ ...INPUT, fontSize: 13 }}
                defaultValue={c.seal_number}
                onBlur={(e) => updateContainer(c.id, { seal_number: e.target.value }).then(invalidate)}
              />
            </div>
            <div style={{ padding: "6px 10px" }}>
              <input style={INPUT_READONLY} readOnly value={c.gross_weight || "—"} />
            </div>
          </div>

          {/* Items section */}
          <div style={{ padding: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <span style={{ fontFamily: "var(--font-heading)", fontSize: 12, fontWeight: 600 }}>
                Items in this Container
              </span>
              <button
                style={{ ...BTN_PRIMARY, padding: "5px 12px", fontSize: 12 }}
                onClick={() => setPendingItems((prev) => ({ ...prev, [c.id]: [...(prev[c.id] ?? []), {}] }))}
              >
                <Plus size={11} /> Add Item
              </button>
            </div>

            {/* Items table — all saved rows are always editable (auto-save on blur/change) */}
            <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 10 }}>
              <thead>
                <tr>
                  <th style={{ ...TH, width: 24 }}>#</th>
                  <th style={TH}>HSN Code</th>
                  <th style={TH}>Item Code</th>
                  <th style={TH}>No &amp; Kind of Pkgs</th>
                  <th style={TH}>Description</th>
                  <th style={TH}>Qty</th>
                  <th style={TH}>UOM</th>
                  <th style={TH}>Net Weight</th>
                  <th style={TH}>Inner Pkg Wt</th>
                  <th style={TH}>Gross Wt (auto)</th>
                  <th style={{ ...TH, width: 36 }}></th>
                </tr>
              </thead>
              <tbody>
                {(!c.items || c.items.length === 0) && !(pendingItems[c.id]?.length) && (
                  <tr>
                    <td colSpan={11} style={{ ...TD, textAlign: "center", fontStyle: "italic", color: "var(--text-muted)" }}>
                      No items yet — click "+ Add Item" to add the first item.
                    </td>
                  </tr>
                )}
                {/* Saved item rows — inputs save on blur / UOM saves on change */}
                {(c.items ?? []).map((item, itemIdx) => (
                  <tr key={item.id}>
                    <td style={{ ...TD, textAlign: "center", color: "var(--text-muted)", fontSize: 11 }}>{itemIdx + 1}</td>
                    <td style={TD}>
                      <input
                        key={`hsn-${item.id}`}
                        style={{ ...INPUT, fontSize: 12, padding: "3px 6px" }}
                        defaultValue={item.hsn_code || ""}
                        onBlur={(e) => { if (e.target.value !== (item.hsn_code || "")) updateContainerItem(item.id, { hsn_code: e.target.value }).then(invalidate); }}
                      />
                    </td>
                    <td style={TD}>
                      <input
                        key={`ic-${item.id}`}
                        style={{ ...INPUT, fontSize: 12, padding: "3px 6px" }}
                        defaultValue={item.item_code}
                        onBlur={(e) => { if (e.target.value !== item.item_code) updateContainerItem(item.id, { item_code: e.target.value }).then(invalidate); }}
                      />
                    </td>
                    <td style={TD}>
                      <input
                        key={`pk-${item.id}`}
                        style={{ ...INPUT, fontSize: 12, padding: "3px 6px" }}
                        defaultValue={item.packages_kind}
                        onBlur={(e) => { if (e.target.value !== item.packages_kind) updateContainerItem(item.id, { packages_kind: e.target.value }).then(invalidate); }}
                      />
                    </td>
                    <td style={TD}>
                      <input
                        key={`desc-${item.id}`}
                        style={{ ...INPUT, fontSize: 12, padding: "3px 6px" }}
                        defaultValue={item.description}
                        onBlur={(e) => { if (e.target.value !== item.description) updateContainerItem(item.id, { description: e.target.value }).then(invalidate); }}
                      />
                    </td>
                    <td style={TD}>
                      <input
                        key={`qty-${item.id}`}
                        type="number"
                        style={{ ...INPUT, fontSize: 12, padding: "3px 6px", width: 70 }}
                        defaultValue={item.quantity}
                        onBlur={(e) => { if (e.target.value !== String(item.quantity)) updateContainerItem(item.id, { quantity: e.target.value }).then(invalidate); }}
                      />
                    </td>
                    <td style={TD}>
                      <Select
                        size="small"
                        style={{ width: 80 }}
                        defaultValue={item.uom}
                        onChange={(v) => updateContainerItem(item.id, { uom: v }).then(invalidate)}
                        options={uoms.map((u: any) => ({ value: u.id, label: u.abbreviation }))}
                      />
                    </td>
                    <td style={TD}>
                      <input
                        key={`nw-${item.id}`}
                        type="number"
                        style={{ ...INPUT, fontSize: 12, padding: "3px 6px", width: 80 }}
                        defaultValue={item.net_weight}
                        onBlur={(e) => { if (e.target.value !== String(item.net_weight)) updateContainerItem(item.id, { net_weight: e.target.value }).then(invalidate); }}
                      />
                    </td>
                    <td style={TD}>
                      <input
                        key={`ipw-${item.id}`}
                        type="number"
                        style={{ ...INPUT, fontSize: 12, padding: "3px 6px", width: 80 }}
                        defaultValue={item.inner_packing_weight}
                        onBlur={(e) => { if (e.target.value !== String(item.inner_packing_weight)) updateContainerItem(item.id, { inner_packing_weight: e.target.value }).then(invalidate); }}
                      />
                    </td>
                    <td style={{ ...TD, color: "var(--text-muted)", fontSize: 12 }}>
                      {item.item_gross_weight ?? (
                        item.net_weight && item.inner_packing_weight
                          ? (parseFloat(String(item.net_weight)) + parseFloat(String(item.inner_packing_weight))).toFixed(3)
                          : "—"
                      )}
                    </td>
                    <td style={TD}>
                      <button style={{ background: "none", border: "none", cursor: "pointer", color: "var(--error, #f87171)", padding: 2 }} onClick={() => removeItem(item.id)}>
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
                {/* Pending (new) item rows — controlled inputs + Save/Cancel */}
                {(pendingItems[c.id] ?? []).map((pItem, pIdx) => (
                  <tr key={`pending-item-${c.id}-${pIdx}`} style={{ background: "var(--bg-base)" }}>
                    <td style={{ ...TD, textAlign: "center", color: "var(--primary)", fontWeight: 700, fontSize: 12 }}>+</td>
                    <td style={TD}>
                      <input style={{ ...INPUT, fontSize: 12, padding: "3px 6px" }} placeholder="HSN"
                        value={pItem.hsn_code || ""} onChange={(e) => updatePendingItem(c.id, pIdx, { hsn_code: e.target.value })} />
                    </td>
                    <td style={TD}>
                      <input style={{ ...INPUT, fontSize: 12, padding: "3px 6px" }} placeholder="Item Code *"
                        value={pItem.item_code || ""} onChange={(e) => updatePendingItem(c.id, pIdx, { item_code: e.target.value })} />
                    </td>
                    <td style={TD}>
                      <input style={{ ...INPUT, fontSize: 12, padding: "3px 6px" }} placeholder="e.g. 10 Bags *"
                        value={pItem.packages_kind || ""} onChange={(e) => updatePendingItem(c.id, pIdx, { packages_kind: e.target.value })} />
                    </td>
                    <td style={TD}>
                      <input style={{ ...INPUT, fontSize: 12, padding: "3px 6px" }} placeholder="Description *"
                        value={pItem.description || ""} onChange={(e) => updatePendingItem(c.id, pIdx, { description: e.target.value })} />
                    </td>
                    <td style={TD}>
                      <input type="number" style={{ ...INPUT, fontSize: 12, padding: "3px 6px", width: 70 }} placeholder="0"
                        value={pItem.quantity || ""} onChange={(e) => updatePendingItem(c.id, pIdx, { quantity: e.target.value })} />
                    </td>
                    <td style={TD}>
                      <Select size="small" style={{ width: 80 }} placeholder="UOM *"
                        value={pItem.uom}
                        onChange={(v) => updatePendingItem(c.id, pIdx, { uom: v })}
                        options={uoms.map((u: any) => ({ value: u.id, label: u.abbreviation }))} />
                    </td>
                    <td style={TD}>
                      <input type="number" style={{ ...INPUT, fontSize: 12, padding: "3px 6px", width: 80 }} placeholder="0.000"
                        value={pItem.net_weight || ""} onChange={(e) => updatePendingItem(c.id, pIdx, { net_weight: e.target.value })} />
                    </td>
                    <td style={TD}>
                      <input type="number" style={{ ...INPUT, fontSize: 12, padding: "3px 6px", width: 80 }} placeholder="0.000"
                        value={pItem.inner_packing_weight || ""} onChange={(e) => updatePendingItem(c.id, pIdx, { inner_packing_weight: e.target.value })} />
                    </td>
                    <td style={{ ...TD, color: "var(--text-muted)", fontSize: 12 }}>
                      {pItem.net_weight && pItem.inner_packing_weight
                        ? (parseFloat(pItem.net_weight) + parseFloat(pItem.inner_packing_weight)).toFixed(3)
                        : "—"}
                    </td>
                    <td style={{ ...TD, whiteSpace: "nowrap" }}>
                      <button
                        style={{ ...BTN_PRIMARY, padding: "3px 10px", fontSize: 12, marginRight: 4 }}
                        onClick={() => savePendingItem(c.id, pIdx)}
                      >Save</button>
                      <button
                        title="Cancel"
                        style={{ background: "none", border: "none", cursor: "pointer", fontSize: 14, color: "var(--text-muted)" }}
                        onClick={() => removePendingItem(c.id, pIdx)}
                      >✕</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {/* ── Pending (unsaved) container cards — dashed border ── */}
      {pendingContainers.map((data, pendingIdx) => {
        const displayIdx = containers.length + pendingIdx;
        return (
          <div
            key={`pending-${pendingIdx}`}
            style={{ border: "2px dashed var(--border-medium)", borderRadius: 10, marginBottom: 16, overflow: "hidden" }}
          >
            <div style={{ background: "var(--primary-light)", color: "var(--primary)", padding: "8px 14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ background: "var(--primary)", color: "#fff", fontWeight: 700, width: 22, height: 22, display: "inline-flex", alignItems: "center", justifyContent: "center", borderRadius: 4, fontSize: 12, flexShrink: 0 }}>
                  {displayIdx + 1}
                </span>
                <span style={{ fontFamily: "var(--font-heading)", fontSize: 13, fontWeight: 600 }}>
                  Container <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 400 }}>(new — fill in fields below)</span>
                </span>
              </div>
              <button
                style={{ padding: "4px 10px", fontSize: 11, borderRadius: 6, border: "1px solid var(--error, #f87171)", background: "transparent", color: "var(--error, #f87171)", cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 4 }}
                onClick={() => setPendingContainers((prev) => prev.filter((_, i) => i !== pendingIdx))}
              >
                <Trash2 size={11} /> Remove
              </button>
            </div>

            {/* Row 1 labels */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
              <div style={containerHeaderStyle}>Container Reference *</div>
              <div style={{ ...containerHeaderStyle, borderRight: "none" }}>Marks and Numbers *</div>
            </div>
            {/* Row 1 inputs */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", borderBottom: "1px solid var(--border-light)" }}>
              <div style={{ padding: "6px 10px", borderRight: "1px solid var(--border-light)" }}>
                <input style={{ ...INPUT, fontSize: 13 }} placeholder="e.g. CONT001" value={data.container_ref || ""}
                  onChange={(e) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, container_ref: e.target.value };
                    setPendingContainers(next);
                  }} />
              </div>
              <div style={{ padding: "6px 10px" }}>
                <input style={{ ...INPUT, fontSize: 13 }} placeholder="Shipping marks on packages" value={data.marks_numbers || ""}
                  onChange={(e) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, marks_numbers: e.target.value };
                    setPendingContainers(next);
                  }} />
              </div>
            </div>

            {/* Row 2 labels */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr" }}>
              {["Tare Weight (kg) *", "Seal Number *", "Gross Weight (auto)"].map((h, i) => (
                <div key={h} style={{ ...containerHeaderStyle, borderRight: i < 2 ? "1px solid var(--border-light)" : "none" }}>{h}</div>
              ))}
            </div>
            {/* Row 2 inputs */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", borderBottom: "1px solid var(--border-light)" }}>
              <div style={{ padding: "6px 10px", borderRight: "1px solid var(--border-light)" }}>
                <input type="number" style={{ ...INPUT, fontSize: 13 }} placeholder="0.000" value={data.tare_weight || ""}
                  onChange={(e) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, tare_weight: e.target.value };
                    setPendingContainers(next);
                  }} />
              </div>
              <div style={{ padding: "6px 10px", borderRight: "1px solid var(--border-light)" }}>
                <input style={{ ...INPUT, fontSize: 13 }} placeholder="e.g. SEAL-9901" value={data.seal_number || ""}
                  onChange={(e) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, seal_number: e.target.value };
                    setPendingContainers(next);
                  }} />
              </div>
              <div style={{ padding: "6px 10px" }}>
                <input style={INPUT_READONLY} readOnly value={(() => {
                  const tare = parseFloat(data.tare_weight || "0");
                  const netW = parseFloat(data._item?.net_weight || "0");
                  const innerW = parseFloat(data._item?.inner_packing_weight || "0");
                  return data.tare_weight ? (tare + netW + innerW).toFixed(3) : "—";
                })()} />
              </div>
            </div>

            {/* Inline first-item form — embedded directly in the pending container card */}
            <div style={{ borderTop: "1px solid var(--border-light)", background: "var(--bg-base)", padding: "12px 14px" }}>
              <div style={{ fontFamily: "var(--font-heading)", fontSize: 12, fontWeight: 600, color: "var(--text-muted)", marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                Item 1
              </div>
              <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr 1fr" }}>
                <div>
                  <label style={LABEL}>Item Code *</label>
                  <input style={INPUT} value={data._item?.item_code || ""} onChange={(e) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, _item: { ...data._item, item_code: e.target.value } };
                    setPendingContainers(next);
                  }} />
                </div>
                <div>
                  <label style={LABEL}>HSN Code</label>
                  <input style={INPUT} value={data._item?.hsn_code || ""} onChange={(e) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, _item: { ...data._item, hsn_code: e.target.value } };
                    setPendingContainers(next);
                  }} />
                </div>
                <div>
                  <label style={LABEL}>No &amp; Kind of Packages *</label>
                  <input style={INPUT} value={data._item?.packages_kind || ""} onChange={(e) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, _item: { ...data._item, packages_kind: e.target.value } };
                    setPendingContainers(next);
                  }} />
                </div>
              </div>
              <div style={{ marginBottom: 12 }}>
                <label style={LABEL}>Description of Goods *</label>
                <textarea style={{ ...INPUT, height: 40, resize: "vertical" }} value={data._item?.description || ""} onChange={(e) => {
                  const next = [...pendingContainers];
                  next[pendingIdx] = { ...data, _item: { ...data._item, description: e.target.value } };
                  setPendingContainers(next);
                }} />
              </div>
              <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr" }}>
                <div>
                  <label style={LABEL}>Quantity *</label>
                  <input type="number" style={INPUT} value={data._item?.quantity || ""} onChange={(e) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, _item: { ...data._item, quantity: e.target.value } };
                    setPendingContainers(next);
                  }} />
                </div>
                <div>
                  <label style={LABEL}>UOM *</label>
                  <Select style={{ width: "100%" }} value={data._item?.uom} onChange={(v) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, _item: { ...data._item, uom: v } };
                    setPendingContainers(next);
                  }} options={uoms.map((u: any) => ({ value: u.id, label: `${u.name} (${u.abbreviation})` }))} />
                </div>
                <div>
                  <label style={LABEL}>Net Weight/unit (kg) *</label>
                  <input type="number" style={INPUT} value={data._item?.net_weight || ""} onChange={(e) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, _item: { ...data._item, net_weight: e.target.value } };
                    setPendingContainers(next);
                  }} />
                </div>
                <div>
                  <label style={LABEL}>Inner Packing Wt (kg) *</label>
                  <input type="number" style={INPUT} value={data._item?.inner_packing_weight || ""} onChange={(e) => {
                    const next = [...pendingContainers];
                    next[pendingIdx] = { ...data, _item: { ...data._item, inner_packing_weight: e.target.value } };
                    setPendingContainers(next);
                  }} />
                </div>
                <div>
                  <label style={LABEL}>Item Gross Wt (auto)</label>
                  <input style={INPUT_READONLY} readOnly value={
                    data._item?.net_weight && data._item?.inner_packing_weight
                      ? (parseFloat(data._item.net_weight) + parseFloat(data._item.inner_packing_weight)).toFixed(3)
                      : "—"
                  } />
                </div>
              </div>
            </div>

            <div style={{ padding: "10px 12px", display: "flex", gap: 8, alignItems: "center", borderTop: "1px solid var(--border-light)" }}>
              <button style={{ ...BTN_PRIMARY, padding: "7px 16px", fontSize: 13 }} onClick={() => savePendingContainer(pendingIdx)}>
                Save Container &amp; Item
              </button>
              <button style={{ ...BTN_SECONDARY, padding: "7px 16px", fontSize: 13 }} onClick={() => setPendingContainers((prev) => prev.filter((_, i) => i !== pendingIdx))}>
                Cancel
              </button>
            </div>
          </div>
        );
      })}

      {/* Full-width Add New Container button */}
      <button
        style={{
          width: "100%",
          background: "var(--primary-light)",
          color: "var(--primary)",
          border: "2px dashed var(--primary)",
          borderRadius: 8,
          padding: "12px 0",
          fontFamily: "var(--font-heading)",
          fontSize: 13,
          fontWeight: 700,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          marginBottom: 20,
        }}
        onClick={() => setPendingContainers([...pendingContainers, { _item: {} }])}
      >
        <Plus size={14} /> Add New Container
      </button>

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        <button style={BTN_SECONDARY} onClick={onBack}><ChevronLeft size={14} /> Back</button>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={BTN_SECONDARY} onClick={() => invalidate()}>Refresh</button>
          <button style={BTN_PRIMARY} onClick={handleNext}>
            Next: Final Rates <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ---- Step 4: Final Rates ----------------------------------------------------

function Step4({
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
  // Pre-populated from the auto-aggregated packages_kind on each CI line item; editable by Maker.
  const [pkgForm, setPkgForm] = useState<Record<number, string>>({});
  const [financials, setFinancials] = useState<Record<string, string>>({
    fob_rate: "",
    freight: "",
    insurance: "",
    lc_details: "",
    incoterms: pl.incoterms != null ? String(pl.incoterms) : "",
    payment_terms: pl.payment_terms != null ? String(pl.payment_terms) : "",
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

  // When CI line items load for the first time, seed pkgForm with the auto-aggregated values.
  const ciLineItemsKey = ci?.line_items.map((li) => li.id).join(",") ?? "";
  useEffect(() => {
    if (!ci) return;
    setPkgForm((prev) => {
      // Only seed entries that haven't been touched by the user yet.
      const seeded: Record<number, string> = { ...prev };
      for (const li of ci.line_items) {
        if (!(li.id in seeded)) {
          seeded[li.id] = li.packages_kind ?? "";
        }
      }
      return seeded;
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ciLineItemsKey]);

  async function handleSave() {
    if (!ci) return;
    if (!financials.incoterms) {
      message.error("Incoterms is required before saving.");
      return;
    }
    setSaving(true);
    try {
      // Save rate_usd and packages_kind for each line item.
      for (const li of ci.line_items) {
        const updates: { rate_usd?: string; packages_kind?: string } = {};
        if (rateForm[li.id] !== undefined) updates.rate_usd = rateForm[li.id];
        if (pkgForm[li.id] !== undefined) updates.packages_kind = pkgForm[li.id];
        if (Object.keys(updates).length > 0) {
          await updateCILineItem(li.id, updates);
        }
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
              <th style={TH}>Rate (USD) *</th>
              <th style={TH}>Amount (USD)</th>
              <th style={TH}>
                No. &amp; Kind of Packages
                <div style={{ fontWeight: 400, fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                  for commercial invoice
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {ci.line_items.map((li) => {
              const rate = rateForm[li.id] ?? li.rate_usd;
              const amount = (parseFloat(li.total_quantity) * parseFloat(rate || "0")).toFixed(2);
              // pkgForm is seeded from li.packages_kind on load; user can edit freely.
              const pkg = pkgForm[li.id] ?? li.packages_kind ?? "";
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
                    {li.uom_abbr && (
                      <div style={{ fontFamily: "var(--font-body)", fontSize: 11, color: "var(--text-muted)", marginTop: 3 }}>
                        USD per {li.uom_abbr}
                      </div>
                    )}
                  </td>
                  <td style={{ ...TD, fontWeight: 600 }}>${amount}</td>
                  <td style={TD}>
                    <textarea
                      style={{ ...INPUT, minHeight: 60, resize: "vertical", width: "100%", fontSize: 13 }}
                      value={pkg}
                      onChange={(e) => setPkgForm({ ...pkgForm, [li.id]: e.target.value })}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      <p style={{ ...SECTION_TITLE, marginTop: 24 }}>Payment & Terms</p>
      <div style={{ ...FORM_ROW, gridTemplateColumns: "1fr 1fr" }}>
        <div>
          <label style={LABEL}>Incoterms *</label>
          <Select style={{ width: "100%" }} value={financials.incoterms ? Number(financials.incoterms) : undefined}
            onChange={(v) => handleIncotermChange(v)}
            placeholder="Select Incoterms"
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
// Create mode: step 0 (PI selection) → steps 1–4 wizard
// Edit mode (/packing-lists/:id/edit?step=N): skip step 0, jump straight to step N

export default function PackingListCreatePage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const isEditMode = !!id;

  // In edit mode, read ?step=N (1–4). Default to 1 if not provided or out of range.
  const requestedStep = isEditMode
    ? Math.min(Math.max(parseInt(searchParams.get("step") ?? "1", 10), 1), 4)
    : 0;

  const [step, setStep] = useState(requestedStep);
  const [form, setForm] = useState<Record<string, any>>({});
  const [pl, setPl] = useState<PackingList | null>(null);

  // In edit mode: fetch the existing PL and pre-populate state
  const { data: fetchedPl, isLoading: plLoading } = useQuery({
    queryKey: ["packing-list", Number(id)],
    queryFn: () => getPackingList(Number(id)),
    enabled: isEditMode && !!id,
  });

  useEffect(() => {
    if (!fetchedPl || !isEditMode) return;
    setPl(fetchedPl);
    setForm({
      proforma_invoice: fetchedPl.proforma_invoice,
      exporter: fetchedPl.exporter,
      consignee: fetchedPl.consignee,
      buyer: fetchedPl.buyer,
      notify_party: fetchedPl.notify_party,
      pl_date: fetchedPl.pl_date,
      ci_date: fetchedPl.ci_date,
      bank: fetchedPl.bank_id,
      pre_carriage_by: fetchedPl.pre_carriage_by,
      place_of_receipt: fetchedPl.place_of_receipt,
      place_of_receipt_by_pre_carrier: fetchedPl.place_of_receipt_by_pre_carrier,
      vessel_flight_no: fetchedPl.vessel_flight_no,
      port_of_loading: fetchedPl.port_of_loading,
      port_of_discharge: fetchedPl.port_of_discharge,
      final_destination: fetchedPl.final_destination,
      country_of_origin: fetchedPl.country_of_origin,
      country_of_final_destination: fetchedPl.country_of_final_destination,
      po_number: fetchedPl.po_number,
      po_date: fetchedPl.po_date,
      lc_number: fetchedPl.lc_number,
      lc_date: fetchedPl.lc_date,
      bl_number: fetchedPl.bl_number,
      bl_date: fetchedPl.bl_date,
      so_number: fetchedPl.so_number,
      so_date: fetchedPl.so_date,
      other_references: fetchedPl.other_references,
      other_references_date: (fetchedPl as any).other_references_date ?? null,
      additional_description: fetchedPl.additional_description,
    });
  // Run only once when the PL first loads (id won't change mid-session)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchedPl?.id]);

  if (isEditMode && plLoading) {
    return <div style={PAGE}><p style={{ fontFamily: "var(--font-body)", color: "var(--text-muted)", padding: 32 }}>Loading…</p></div>;
  }

  const backToDetail = () => navigate(`/packing-lists/${id}`);

  return (
    <div style={PAGE}>
      {/* Breadcrumb + page title */}
      <div style={{ marginBottom: 24 }}>
        <p style={{
          fontFamily: "var(--font-body)", fontSize: 12, color: "var(--text-muted)",
          margin: "0 0 8px", letterSpacing: "0.02em",
        }}>
          Documents / PL+CI / {isEditMode ? "Edit" : "New"}
        </p>
        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
          {isEditMode ? `Edit ${pl?.pl_number ?? "Packing List"}` : "Create Packing List + Commercial Invoice"}
        </h1>
      </div>

      {/* Step bar only for wizard steps 1–4 */}
      {step >= 1 && <StepBar current={step - 1} />}

      {step === 0 && (
        <Step0
          form={form}
          setForm={setForm}
          onContinue={() => setStep(1)}
          onCancel={() => navigate("/packing-lists")}
        />
      )}
      {step === 1 && (
        <Step1
          form={form}
          setForm={setForm}
          existingPl={isEditMode ? (pl ?? undefined) : undefined}
          onNext={(savedPl) => { setPl(savedPl); setStep(2); }}
          onBack={() => isEditMode ? backToDetail() : setStep(0)}
        />
      )}
      {step === 2 && pl && (
        <Step2 pl={pl} form={form} setForm={setForm} onNext={() => setStep(3)} onBack={() => setStep(1)} />
      )}
      {step === 3 && pl && (
        <Step3 pl={pl} onNext={(refreshed) => { setPl(refreshed); setStep(4); }} onBack={() => setStep(2)} />
      )}
      {step === 4 && pl && (
        <Step4 pl={pl} onDone={() => navigate(`/packing-lists/${pl.id}`)} onBack={() => setStep(3)} />
      )}
    </div>
  );
}
