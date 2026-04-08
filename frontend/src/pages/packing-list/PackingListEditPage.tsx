// Packing List edit page — pre-populated multi-section form.
// Only accessible in DRAFT or REWORK status, by the document creator or Admin.
// Unlike create, the PL already exists — each section saves via PATCH.

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Select, DatePicker, message, Modal } from "antd";
import { Plus, Trash2, Copy, ChevronLeft, Check } from "lucide-react";
import dayjs from "dayjs";

import {
  getPackingList,
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
import type { PackingList } from "../../api/packingLists";
import { listOrganisations } from "../../api/organisations";
import { listIncoterms, listPaymentTerms, listUOMs, listPorts, listLocations, listPreCarriageBy } from "../../api/referenceData";
import { listCountries } from "../../api/countries";
import { listBanks } from "../../api/banks";
import { useAuth } from "../../store/AuthContext";
import { DOCUMENT_STATUS, INCOTERM_PL_FIELDS, ROLES } from "../../utils/constants";
import { extractApiError } from "../../utils/apiErrors";

// ---- Styles (reuse the same tokens as Create page) --------------------------

const PAGE: React.CSSProperties = { padding: 32, background: "var(--bg-base)", minHeight: "100vh" };

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

const BTN_PRIMARY: React.CSSProperties = {
  display: "inline-flex", alignItems: "center", gap: 6,
  padding: "10px 20px", borderRadius: 8, border: "none",
  background: "var(--primary)", color: "#fff",
  fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, cursor: "pointer",
};

const BTN_SECONDARY: React.CSSProperties = {
  display: "inline-flex", alignItems: "center", gap: 6,
  padding: "10px 20px", borderRadius: 8, border: "1px solid var(--border-medium)",
  background: "var(--bg-surface)", color: "var(--text-secondary)",
  fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, cursor: "pointer",
};

// ---- Page -------------------------------------------------------------------

export default function PackingListEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: pl, isLoading } = useQuery({
    queryKey: ["packing-list", Number(id)],
    queryFn: () => getPackingList(Number(id)),
    enabled: !!id,
  });

  // Redirect if not editable
  useEffect(() => {
    if (!pl) return;
    const isEditable = pl.status === DOCUMENT_STATUS.DRAFT || pl.status === DOCUMENT_STATUS.REWORK;
    const isCreator = user?.id === pl.created_by;
    const isAdmin = user?.role === ROLES.COMPANY_ADMIN || user?.role === ROLES.SUPER_ADMIN;
    // Any Maker can access the edit page for any editable PL — not just the creator.
    const isMaker = user?.role === ROLES.MAKER;
    if (!isEditable || (!isMaker && !isCreator && !isAdmin)) {
      navigate(`/packing-lists/${id}`);
    }
  }, [pl, user]);

  const { data: exporters = [] } = useQuery({ queryKey: ["organisations", "EXPORTER"], queryFn: () => listOrganisations("EXPORTER") });
  const { data: consignees = [] } = useQuery({ queryKey: ["organisations", "CONSIGNEE"], queryFn: () => listOrganisations("CONSIGNEE") });
  const { data: buyers = [] } = useQuery({ queryKey: ["organisations", "BUYER"], queryFn: () => listOrganisations("BUYER") });
  const { data: notifyParties = [] } = useQuery({ queryKey: ["organisations", "NOTIFY_PARTY"], queryFn: () => listOrganisations("NOTIFY_PARTY") });
  const { data: banks = [] } = useQuery({ queryKey: ["banks"], queryFn: listBanks });
  const { data: incoterms = [] } = useQuery({ queryKey: ["incoterms"], queryFn: listIncoterms });
  const { data: paymentTerms = [] } = useQuery({ queryKey: ["payment-terms"], queryFn: listPaymentTerms });
  const { data: ports = [] } = useQuery({ queryKey: ["ports"], queryFn: listPorts });
  const { data: locations = [] } = useQuery({ queryKey: ["locations"], queryFn: listLocations });
  const { data: preCarriage = [] } = useQuery({ queryKey: ["pre-carriage"], queryFn: listPreCarriageBy });
  const { data: countries = [] } = useQuery({ queryKey: ["countries"], queryFn: listCountries });
  const { data: uoms = [] } = useQuery({ queryKey: ["uoms"], queryFn: listUOMs });

  const { data: ci } = useQuery({
    queryKey: ["commercial-invoice", pl?.ci_id],
    queryFn: () => getCommercialInvoice(pl!.ci_id!),
    enabled: !!pl?.ci_id,
  });

  const [headerForm, setHeaderForm] = useState<Record<string, any>>({});
  const [rateForm, setRateForm] = useState<Record<number, string>>({});
  const [addingItem, setAddingItem] = useState<{ containerId: number } | null>(null);
  const [itemForm, setItemForm] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);

  // Pre-populate once PL loads
  useEffect(() => {
    if (!pl) return;
    setHeaderForm({
      exporter: pl.exporter,
      consignee: pl.consignee,
      buyer: pl.buyer,
      notify_party: pl.notify_party,
      pl_date: pl.pl_date,
      ci_date: pl.ci_date,
      bank: pl.bank_id,
      po_number: pl.po_number,
      po_date: pl.po_date,
      lc_number: pl.lc_number,
      lc_date: pl.lc_date,
      bl_number: pl.bl_number,
      bl_date: pl.bl_date,
      so_number: pl.so_number,
      so_date: pl.so_date,
      other_references: pl.other_references,
      other_references_date: pl.other_references_date,
      additional_description: pl.additional_description,
      pre_carriage_by: pl.pre_carriage_by,
      place_of_receipt: pl.place_of_receipt,
      place_of_receipt_by_pre_carrier: pl.place_of_receipt_by_pre_carrier,
      vessel_flight_no: pl.vessel_flight_no,
      port_of_loading: pl.port_of_loading,
      port_of_discharge: pl.port_of_discharge,
      final_destination: pl.final_destination,
      country_of_origin: pl.country_of_origin,
      country_of_final_destination: pl.country_of_final_destination,
      incoterms: pl.incoterms,
      payment_terms: pl.payment_terms,
      // Incoterm-driven cost fields — clear hidden ones on save via handleSaveAll

      fob_rate: pl.fob_rate || "",
      freight: pl.freight || "",
      insurance: pl.insurance || "",
      lc_details: pl.lc_details,
    });
  }, [pl?.id]);

  async function handleSaveAll() {
    if (!pl) return;
    setSaving(true);
    try {
      // Determine which cost fields are visible based on selected incoterm.
      const selectedCode = incoterms.find((t: any) => t.id === headerForm.incoterms)?.code ?? null;
      const visibleCost: Set<string> = selectedCode
        ? (INCOTERM_PL_FIELDS[selectedCode] ?? new Set(["fob_rate", "freight", "insurance"]))
        : new Set(["fob_rate", "freight", "insurance"]);

      // Save all header + shipping + financial fields in one PATCH.
      // Hidden cost fields are sent as null (FR-14M.8B — "cleared").
      await updatePackingList(pl.id, {
        exporter: headerForm.exporter,
        consignee: headerForm.consignee,
        buyer: headerForm.buyer || null,
        notify_party: headerForm.notify_party || null,
        pl_date: headerForm.pl_date,
        ci_date: headerForm.ci_date,
        bank: headerForm.bank || null,
        po_number: headerForm.po_number || "",
        po_date: headerForm.po_date || null,
        lc_number: headerForm.lc_number || "",
        lc_date: headerForm.lc_date || null,
        bl_number: headerForm.bl_number || "",
        bl_date: headerForm.bl_date || null,
        so_number: headerForm.so_number || "",
        so_date: headerForm.so_date || null,
        other_references: headerForm.other_references || "",
        other_references_date: headerForm.other_references_date || null,
        additional_description: headerForm.additional_description || "",
        pre_carriage_by: headerForm.pre_carriage_by || null,
        place_of_receipt: headerForm.place_of_receipt || null,
        place_of_receipt_by_pre_carrier: headerForm.place_of_receipt_by_pre_carrier || null,
        vessel_flight_no: headerForm.vessel_flight_no || "",
        port_of_loading: headerForm.port_of_loading || null,
        port_of_discharge: headerForm.port_of_discharge || null,
        final_destination: headerForm.final_destination || null,
        country_of_origin: headerForm.country_of_origin || null,
        country_of_final_destination: headerForm.country_of_final_destination || null,
        incoterms: headerForm.incoterms || null,
        payment_terms: headerForm.payment_terms || null,
        fob_rate: visibleCost.has("fob_rate") ? (headerForm.fob_rate || null) : null,
        freight: visibleCost.has("freight") ? (headerForm.freight || null) : null,
        insurance: visibleCost.has("insurance") ? (headerForm.insurance || null) : null,
        lc_details: headerForm.lc_details || "",
      });

      // Save rates
      for (const [idStr, rate] of Object.entries(rateForm)) {
        await updateCILineItem(Number(idStr), { rate_usd: rate });
      }

      queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
      queryClient.invalidateQueries({ queryKey: ["commercial-invoice", pl.ci_id] });
      message.success("Saved.");
      navigate(`/packing-lists/${pl.id}`);
    } catch (err) {
      message.error(extractApiError(err, "Failed to save."));
    } finally {
      setSaving(false);
    }
  }

  async function saveItem() {
    if (!addingItem) return;
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
      queryClient.invalidateQueries({ queryKey: ["packing-list", pl!.id] });
      queryClient.invalidateQueries({ queryKey: ["commercial-invoice", pl!.ci_id] });
      message.success("Item added.");
    } catch (err) {
      message.error(extractApiError(err, "Failed to add item."));
    }
  }

  if (isLoading || !pl) {
    return <div style={{ padding: 32, fontFamily: "var(--font-body)", color: "var(--text-muted)" }}>Loading…</div>;
  }


  return (
    <div style={PAGE}>
      <div style={{ marginBottom: 24 }}>
        <button
          onClick={() => navigate(`/packing-lists/${pl.id}`)}
          style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4, fontFamily: "var(--font-body)", fontSize: 13, padding: 0, marginBottom: 12 }}
        >
          <ChevronLeft size={14} /> Cancel
        </button>
        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
          Edit {pl.pl_number}
        </h1>
      </div>

      {/* Header & Parties */}
      <div style={CARD}>
        <p style={SECTION_TITLE}>Header & Parties</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16 }}>
          <div>
            <label style={LABEL}>Exporter *</label>
            <Select style={{ width: "100%" }} value={headerForm.exporter}
              onChange={(v) => setHeaderForm({ ...headerForm, exporter: v })}
              showSearch optionFilterProp="label" options={exporters.map((o: any) => ({ value: o.id, label: o.name })).sort((a, b) => a.label.localeCompare(b.label))} />
          </div>
          <div>
            <label style={LABEL}>Consignee *</label>
            <Select style={{ width: "100%" }} value={headerForm.consignee}
              onChange={(v) => setHeaderForm({ ...headerForm, consignee: v })}
              showSearch optionFilterProp="label" options={consignees.map((o: any) => ({ value: o.id, label: o.name })).sort((a, b) => a.label.localeCompare(b.label))} />
          </div>
          <div>
            <label style={LABEL}>Buyer</label>
            <Select allowClear style={{ width: "100%" }} value={headerForm.buyer}
              onChange={(v) => setHeaderForm({ ...headerForm, buyer: v })}
              showSearch optionFilterProp="label" options={buyers.map((o: any) => ({ value: o.id, label: o.name })).sort((a, b) => a.label.localeCompare(b.label))} />
          </div>
          <div>
            <label style={LABEL}>Notify Party</label>
            <Select allowClear style={{ width: "100%" }} value={headerForm.notify_party}
              onChange={(v) => setHeaderForm({ ...headerForm, notify_party: v })}
              showSearch optionFilterProp="label" options={notifyParties.map((o: any) => ({ value: o.id, label: o.name })).sort((a, b) => a.label.localeCompare(b.label))} />
          </div>
          <div>
            <label style={LABEL}>Bank (for CI)</label>
            <Select allowClear style={{ width: "100%" }} value={headerForm.bank}
              onChange={(v) => setHeaderForm({ ...headerForm, bank: v })}
              showSearch optionFilterProp="label" options={banks.map((b: any) => ({ value: b.id, label: `${b.bank_name} – ${b.beneficiary_name}` })).sort((a, b) => a.label.localeCompare(b.label))} />
          </div>
          <div>
            <label style={LABEL}>PL Date</label>
            <DatePicker style={{ width: "100%" }} value={headerForm.pl_date ? dayjs(headerForm.pl_date) : null}
              onChange={(d) => setHeaderForm({ ...headerForm, pl_date: d?.format("YYYY-MM-DD") })} />
          </div>
          <div>
            <label style={LABEL}>CI Date</label>
            <DatePicker style={{ width: "100%" }} value={headerForm.ci_date ? dayjs(headerForm.ci_date) : null}
              onChange={(d) => setHeaderForm({ ...headerForm, ci_date: d?.format("YYYY-MM-DD") })} />
          </div>
        </div>
      </div>

      {/* Order References */}
      <div style={CARD}>
        <p style={SECTION_TITLE}>Order References (all optional)</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
          <div>
            <label style={LABEL}>PO Number</label>
            <input style={INPUT} value={headerForm.po_number || ""} onChange={(e) => setHeaderForm({ ...headerForm, po_number: e.target.value })} />
          </div>
          <div>
            <label style={LABEL}>PO Date</label>
            <DatePicker style={{ width: "100%" }} value={headerForm.po_date ? dayjs(headerForm.po_date) : null}
              onChange={(d) => setHeaderForm({ ...headerForm, po_date: d?.format("YYYY-MM-DD") ?? null })} />
          </div>
          <div />
          <div>
            <label style={LABEL}>LC Number</label>
            <input style={INPUT} value={headerForm.lc_number || ""} onChange={(e) => setHeaderForm({ ...headerForm, lc_number: e.target.value })} />
          </div>
          <div>
            <label style={LABEL}>LC Date</label>
            <DatePicker style={{ width: "100%" }} value={headerForm.lc_date ? dayjs(headerForm.lc_date) : null}
              onChange={(d) => setHeaderForm({ ...headerForm, lc_date: d?.format("YYYY-MM-DD") ?? null })} />
          </div>
          <div />
          <div>
            <label style={LABEL}>BL Number</label>
            <input style={INPUT} value={headerForm.bl_number || ""} onChange={(e) => setHeaderForm({ ...headerForm, bl_number: e.target.value })} />
          </div>
          <div>
            <label style={LABEL}>BL Date</label>
            <DatePicker style={{ width: "100%" }} value={headerForm.bl_date ? dayjs(headerForm.bl_date) : null}
              onChange={(d) => setHeaderForm({ ...headerForm, bl_date: d?.format("YYYY-MM-DD") ?? null })} />
          </div>
          <div />
          <div>
            <label style={LABEL}>SO Number</label>
            <input style={INPUT} value={headerForm.so_number || ""} onChange={(e) => setHeaderForm({ ...headerForm, so_number: e.target.value })} />
          </div>
          <div>
            <label style={LABEL}>SO Date</label>
            <DatePicker style={{ width: "100%" }} value={headerForm.so_date ? dayjs(headerForm.so_date) : null}
              onChange={(d) => setHeaderForm({ ...headerForm, so_date: d?.format("YYYY-MM-DD") ?? null })} />
          </div>
          <div />
          <div>
            <label style={LABEL}>Other References</label>
            <input style={INPUT} value={headerForm.other_references || ""} onChange={(e) => setHeaderForm({ ...headerForm, other_references: e.target.value })} />
          </div>
          <div>
            <label style={LABEL}>Other References Date</label>
            <DatePicker style={{ width: "100%" }} value={headerForm.other_references_date ? dayjs(headerForm.other_references_date) : null}
              onChange={(d) => setHeaderForm({ ...headerForm, other_references_date: d?.format("YYYY-MM-DD") ?? null })} />
          </div>
          <div />
        </div>
        <div style={{ marginTop: 8 }}>
          <label style={LABEL}>Additional Description</label>
          <textarea style={{ ...INPUT, minHeight: 72, resize: "vertical" }} value={headerForm.additional_description || ""}
            onChange={(e) => setHeaderForm({ ...headerForm, additional_description: e.target.value })} />
        </div>
      </div>

      {/* Shipping & Logistics */}
      <div style={CARD}>
        <p style={SECTION_TITLE}>Shipping & Logistics</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
          <div>
            <label style={LABEL}>Pre-Carriage By</label>
            <Select allowClear style={{ width: "100%" }} value={headerForm.pre_carriage_by}
              onChange={(v) => setHeaderForm({ ...headerForm, pre_carriage_by: v })}
              showSearch optionFilterProp="label" options={preCarriage.map((p: any) => ({ value: p.id, label: p.name })).sort((a, b) => a.label.localeCompare(b.label))} />
          </div>
          <div>
            <label style={LABEL}>Place of Receipt</label>
            <Select allowClear showSearch style={{ width: "100%" }} value={headerForm.place_of_receipt}
              onChange={(v) => setHeaderForm({ ...headerForm, place_of_receipt: v })}
              options={locations.map((l: any) => ({ value: l.id, label: l.name })).sort((a, b) => a.label.localeCompare(b.label))}
              optionFilterProp="label" />
          </div>
          <div>
            <label style={LABEL}>Place of Receipt by Pre-Carrier</label>
            <Select allowClear showSearch style={{ width: "100%" }} value={headerForm.place_of_receipt_by_pre_carrier}
              onChange={(v) => setHeaderForm({ ...headerForm, place_of_receipt_by_pre_carrier: v })}
              options={locations.map((l: any) => ({ value: l.id, label: l.name })).sort((a, b) => a.label.localeCompare(b.label))}
              optionFilterProp="label" />
          </div>
          <div>
            <label style={LABEL}>Vessel / Flight No</label>
            <input style={INPUT} value={headerForm.vessel_flight_no || ""} onChange={(e) => setHeaderForm({ ...headerForm, vessel_flight_no: e.target.value })} />
          </div>
          <div>
            <label style={LABEL}>Port of Loading</label>
            <Select allowClear showSearch style={{ width: "100%" }} value={headerForm.port_of_loading}
              onChange={(v) => setHeaderForm({ ...headerForm, port_of_loading: v })}
              options={ports.map((p: any) => ({ value: p.id, label: p.name })).sort((a, b) => a.label.localeCompare(b.label))}
              optionFilterProp="label" />
          </div>
          <div>
            <label style={LABEL}>Port of Discharge</label>
            <Select allowClear showSearch style={{ width: "100%" }} value={headerForm.port_of_discharge}
              onChange={(v) => setHeaderForm({ ...headerForm, port_of_discharge: v })}
              options={ports.map((p: any) => ({ value: p.id, label: p.name })).sort((a, b) => a.label.localeCompare(b.label))}
              optionFilterProp="label" />
          </div>
          <div>
            <label style={LABEL}>Final Destination</label>
            <Select allowClear showSearch style={{ width: "100%" }} value={headerForm.final_destination}
              onChange={(v) => setHeaderForm({ ...headerForm, final_destination: v })}
              options={locations.map((l: any) => ({ value: l.id, label: l.name })).sort((a, b) => a.label.localeCompare(b.label))}
              optionFilterProp="label" />
          </div>
          <div>
            <label style={LABEL}>Incoterms</label>
            <Select allowClear style={{ width: "100%" }} value={headerForm.incoterms}
              onChange={(v) => setHeaderForm({ ...headerForm, incoterms: v ?? null })}
              showSearch optionFilterProp="label" options={incoterms.map((t: any) => ({ value: t.id, label: `${t.code} – ${t.full_name}` })).sort((a, b) => a.label.localeCompare(b.label))} />
          </div>
        </div>
      </div>

      {/* Countries */}
      <div style={CARD}>
        <p style={SECTION_TITLE}>Countries</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <label style={LABEL}>Country of Origin of Goods</label>
            <Select allowClear showSearch style={{ width: "100%" }} value={headerForm.country_of_origin}
              onChange={(v) => setHeaderForm({ ...headerForm, country_of_origin: v ?? null })}
              options={countries.map((c: any) => ({ value: c.id, label: c.name })).sort((a, b) => a.label.localeCompare(b.label))}
              optionFilterProp="label" />
          </div>
          <div>
            <label style={LABEL}>Country of Final Destination</label>
            <Select allowClear showSearch style={{ width: "100%" }} value={headerForm.country_of_final_destination}
              onChange={(v) => setHeaderForm({ ...headerForm, country_of_final_destination: v ?? null })}
              options={countries.map((c: any) => ({ value: c.id, label: c.name })).sort((a, b) => a.label.localeCompare(b.label))}
              optionFilterProp="label" />
          </div>
        </div>
      </div>

      {/* Containers & Items */}
      <div style={CARD}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <p style={{ ...SECTION_TITLE, margin: 0 }}>Containers & Items</p>
          <button style={BTN_SECONDARY} onClick={async () => {
            try {
              await createContainer({ packing_list: pl.id, container_ref: "", marks_numbers: "", seal_number: "", tare_weight: "0.000" });
              queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
            } catch (err) {
              message.error(extractApiError(err, "Failed to add container."));
            }
          }}>
            <Plus size={14} /> Add Container
          </button>
        </div>

        {(pl.containers ?? []).map((c, idx) => (
          <div key={c.id} style={{ border: "1px solid var(--border-light)", borderRadius: 10, padding: 16, marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <span style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: 14 }}>Container {idx + 1}</span>
              <div style={{ display: "flex", gap: 8 }}>
                <button style={{ ...BTN_SECONDARY, padding: "6px 12px", fontSize: 12 }} onClick={async () => {
                  try {
                    await copyContainer(c.id);
                    queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
                    queryClient.invalidateQueries({ queryKey: ["commercial-invoice", pl.ci_id] });
                  } catch (err) {
                    message.error(extractApiError(err, "Failed to copy container."));
                  }
                }}><Copy size={12} /> Copy</button>
                <button style={{ ...BTN_SECONDARY, padding: "6px 12px", fontSize: 12, color: "var(--pastel-pink-text)" }} onClick={async () => {
                  try {
                    await deleteContainer(c.id);
                    queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
                    queryClient.invalidateQueries({ queryKey: ["commercial-invoice", pl.ci_id] });
                  } catch (err) {
                    message.error(extractApiError(err, "Failed to delete container."));
                  }
                }}><Trash2 size={12} /></button>
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 12, marginBottom: 12 }}>
              {[["container_ref", "Container Ref *"], ["marks_numbers", "Marks & Numbers *"], ["seal_number", "Seal Number *"], ["tare_weight", "Tare Weight (kg) *"]].map(([field, label]) => (
                <div key={field}>
                  <label style={LABEL}>{label}</label>
                  <input style={INPUT} defaultValue={(c as any)[field]} onBlur={(e) => {
                    updateContainer(c.id, { [field]: e.target.value });
                  }} />
                </div>
              ))}
            </div>
            {(c.items ?? []).length > 0 && (
              <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 12 }}>
                <thead>
                  <tr>
                    {["Item Code", "Desc", "HSN", "Pkgs", "Qty", "UOM", "Net Wt", "Batch No.", ""].map((h) => (
                      <th key={h} style={TH}>{h}</th>
                    ))}
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
                      <td style={TD}>{item.uom_abbr ?? "—"}</td>
                      <td style={TD}>{item.net_weight}</td>
                      <td style={TD}>{item.batch_details || "—"}</td>
                      <td style={TD}>
                        <button style={{ background: "none", border: "none", cursor: "pointer", color: "var(--pastel-pink-text)" }} onClick={async () => {
                          try {
                            await deleteContainerItem(item.id);
                            queryClient.invalidateQueries({ queryKey: ["packing-list", pl.id] });
                            queryClient.invalidateQueries({ queryKey: ["commercial-invoice", pl.ci_id] });
                          } catch (err) {
                            message.error(extractApiError(err, "Failed to delete item."));
                          }
                        }}><Trash2 size={14} /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <button style={{ ...BTN_SECONDARY, padding: "6px 14px", fontSize: 12 }}
              onClick={() => { setAddingItem({ containerId: c.id }); setItemForm({}); }}>
              <Plus size={12} /> Add Item
            </button>
          </div>
        ))}
      </div>

      {/* Payment Terms */}
      <div style={CARD}>
        <p style={SECTION_TITLE}>Payment Terms</p>
        <div style={{ maxWidth: 360 }}>
          <label style={LABEL}>Payment Terms</label>
          <Select allowClear style={{ width: "100%" }} value={headerForm.payment_terms}
            onChange={(v) => setHeaderForm({ ...headerForm, payment_terms: v ?? null })}
            showSearch optionFilterProp="label" options={paymentTerms.map((t: any) => ({ value: t.id, label: t.name })).sort((a, b) => a.label.localeCompare(b.label))} />
        </div>
      </div>

      {/* Final Rates */}
      {ci && ci.line_items.length > 0 && (
        <div style={CARD}>
          <p style={SECTION_TITLE}>Final Rates</p>
          <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 20 }}>
            <thead>
              <tr>
                <th style={TH}>Item Code</th>
                <th style={TH}>Description</th>
                <th style={TH}>No. & Kind of Packages</th>
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
                    <td style={TD}>{li.packages_kind || "—"}</td>
                    <td style={TD}>{li.total_quantity}</td>
                    <td style={TD}>{li.uom_abbr ?? "—"}</td>
                    <td style={TD}>
                      <input type="number" step="0.01" style={{ ...INPUT, width: 120 }} value={rate}
                        onChange={(e) => setRateForm({ ...rateForm, [li.id]: e.target.value })} />
                    </td>
                    <td style={{ ...TD, fontWeight: 600 }}>${amount}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {(() => {
            // Derive visible cost fields from the currently selected Incoterm.
            const code = incoterms.find((t: any) => t.id === headerForm.incoterms)?.code ?? null;
            const visible: Set<string> = code
              ? (INCOTERM_PL_FIELDS[code] ?? new Set(["fob_rate", "freight", "insurance"]))
              : new Set(["fob_rate", "freight", "insurance"]);
            return (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
                {visible.has("fob_rate") && (
                  <div>
                    <label style={LABEL}>FOB Rate (USD per UOM)</label>
                    <input type="number" step="0.01" style={INPUT} value={headerForm.fob_rate || ""}
                      onChange={(e) => setHeaderForm({ ...headerForm, fob_rate: e.target.value })} />
                  </div>
                )}
                {visible.has("freight") && (
                  <div>
                    <label style={LABEL}>Freight (USD)</label>
                    <input type="number" step="0.01" style={INPUT} value={headerForm.freight || ""}
                      onChange={(e) => setHeaderForm({ ...headerForm, freight: e.target.value })} />
                  </div>
                )}
                {visible.has("insurance") && (
                  <div>
                    <label style={LABEL}>Insurance (USD)</label>
                    <input type="number" step="0.01" style={INPUT} value={headerForm.insurance || ""}
                      onChange={(e) => setHeaderForm({ ...headerForm, insurance: e.target.value })} />
                  </div>
                )}
              </div>
            );
          })()}
          <div style={{ marginTop: 12 }}>
            <label style={LABEL}>L/C Details</label>
            <textarea style={{ ...INPUT, minHeight: 80, resize: "vertical" }} value={headerForm.lc_details || ""}
              onChange={(e) => setHeaderForm({ ...headerForm, lc_details: e.target.value })} />
          </div>
        </div>
      )}

      {/* Save button */}
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
        <button style={BTN_SECONDARY} onClick={() => navigate(`/packing-lists/${pl.id}`)}>
          Cancel
        </button>
        <button style={BTN_PRIMARY} onClick={handleSaveAll} disabled={saving}>
          <Check size={14} /> {saving ? "Saving…" : "Save Changes"}
        </button>
      </div>

      {/* Add item modal */}
      <Modal title="Add Item to Container" open={addingItem !== null}
        onOk={saveItem} onCancel={() => { setAddingItem(null); setItemForm({}); }}
        okText="Add Item" width={640}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {[
            ["item_code", "Item Code *", "text"],
            ["packages_kind", "No & Kind of Packages *", "text"],
            ["description", "Description *", "text"],
            ["hsn_code", "HSN Code", "text"],
            ["batch_details", "Batch Number", "text"],
            ["quantity", "Quantity *", "number"],
            ["net_weight", "Net Weight/unit (kg) *", "number"],
            ["inner_packing_weight", "Inner Packing Weight (kg) *", "number"],
          ].map(([field, label, type]) => (
            <div key={field as string} style={field === "description" ? { gridColumn: "1 / -1" } : {}}>
              <label style={LABEL}>{label as string}</label>
              <input style={INPUT} type={type as string} value={itemForm[field as string] || ""}
                onChange={(e) => setItemForm({ ...itemForm, [field as string]: e.target.value })} />
            </div>
          ))}
          <div>
            <label style={LABEL}>UOM *</label>
            <Select style={{ width: "100%" }} value={itemForm.uom}
              onChange={(v) => setItemForm({ ...itemForm, uom: v })}
              showSearch optionFilterProp="label" options={uoms.map((u: any) => ({ value: u.id, label: `${u.name} (${u.abbreviation})` })).sort((a, b) => a.label.localeCompare(b.label))} />
          </div>
        </div>
      </Modal>
    </div>
  );
}
