// Proforma Invoice create form — FR-09.1 through FR-09.4.
// Four sections: Header, Shipping & Logistics, Payment & Terms, T&C.
// On save → navigates to detail page where line items are added.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { message, Select, DatePicker } from "antd";
import { ArrowLeft } from "lucide-react";
import dayjs from "dayjs";

import { createProformaInvoice } from "../../api/proformaInvoices";
import { listOrganisations } from "../../api/organisations";
import { listCountries } from "../../api/countries";
import {
  listPorts, listLocations, listPreCarriageBy,
  listPaymentTerms, listIncoterms,
} from "../../api/referenceData";
import { listBanks } from "../../api/banks";
import { listTCTemplates, getTCTemplate } from "../../api/tcTemplates";
import { SHIPMENT_OPTIONS, SHIPMENT_OPTION_LABELS } from "../../utils/constants";

// ---- Zod schema ------------------------------------------------------------

const schema = z.object({
  exporter: z.number({ required_error: "Exporter is required" }),
  consignee: z.number({ required_error: "Consignee is required" }),
  buyer: z.number().nullable().optional(),
  pi_date: z.string().optional(),
  buyer_order_no: z.string().optional().default(""),
  buyer_order_date: z.string().nullable().optional(),
  other_references: z.string().optional().default(""),
  country_of_origin: z.number().nullable().optional(),
  country_of_final_destination: z.number().nullable().optional(),
  // Shipping
  pre_carriage_by: z.number().nullable().optional(),
  place_of_receipt: z.number().nullable().optional(),
  vessel_flight_no: z.string().optional().default(""),
  port_of_loading: z.number().nullable().optional(),
  port_of_discharge: z.number().nullable().optional(),
  final_destination: z.number().nullable().optional(),
  // Payment & Terms
  payment_terms: z.number({ required_error: "Payment Terms is required" }),
  incoterms: z.number({ required_error: "Incoterms is required" }),
  bank: z.number().nullable().optional(),
  validity_for_acceptance: z.string().nullable().optional(),
  validity_for_shipment: z.string().nullable().optional(),
  partial_shipment: z.string().optional().default(""),
  transshipment: z.string().optional().default(""),
  // T&C
  tc_template: z.number().nullable().optional(),
  tc_content: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

// ---- Helpers ---------------------------------------------------------------

const CARD_STYLE: React.CSSProperties = {
  background: "var(--bg-surface)",
  borderRadius: 14,
  border: "1px solid var(--border-light)",
  boxShadow: "var(--shadow-card)",
  padding: "24px 28px",
  marginBottom: 20,
};

const SECTION_TITLE_STYLE: React.CSSProperties = {
  fontFamily: "var(--font-heading)",
  fontSize: 16,
  fontWeight: 600,
  color: "var(--text-primary)",
  marginBottom: 20,
};

const LABEL_STYLE: React.CSSProperties = {
  display: "block",
  fontFamily: "var(--font-body)",
  fontSize: 12,
  fontWeight: 500,
  color: "var(--text-muted)",
  marginBottom: 6,
};

const INPUT_STYLE: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-input)",
  border: "1px solid var(--border-medium)",
  borderRadius: 8,
  padding: "9px 14px",
  fontFamily: "var(--font-body)",
  fontSize: 14,
  color: "var(--text-primary)",
  outline: "none",
};

const GRID2: React.CSSProperties = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 };
const GRID3: React.CSSProperties = { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 };

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null;
  return <p style={{ color: "#e53e3e", fontFamily: "var(--font-body)", fontSize: 12, marginTop: 4 }}>{msg}</p>;
}

// ---- Page ------------------------------------------------------------------

export default function ProformaInvoiceCreatePage() {
  const navigate = useNavigate();
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);

  const { data: exporters = [] } = useQuery({
    queryKey: ["organisations", "EXPORTER"],
    queryFn: () => listOrganisations("EXPORTER"),
  });
  const { data: consignees = [] } = useQuery({
    queryKey: ["organisations", "CONSIGNEE"],
    queryFn: () => listOrganisations("CONSIGNEE"),
  });
  const { data: buyers = [] } = useQuery({
    queryKey: ["organisations", "BUYER"],
    queryFn: () => listOrganisations("BUYER"),
  });
  const { data: countries = [] } = useQuery({
    queryKey: ["countries"],
    queryFn: listCountries,
  });
  const { data: ports = [] } = useQuery({
    queryKey: ["ports"],
    queryFn: listPorts,
  });
  const { data: locations = [] } = useQuery({
    queryKey: ["locations"],
    queryFn: listLocations,
  });
  const { data: preCarriageOptions = [] } = useQuery({
    queryKey: ["pre-carriage"],
    queryFn: listPreCarriageBy,
  });
  const { data: paymentTerms = [] } = useQuery({
    queryKey: ["payment-terms"],
    queryFn: listPaymentTerms,
  });
  const { data: incoterms = [] } = useQuery({
    queryKey: ["incoterms"],
    queryFn: listIncoterms,
  });
  const { data: banks = [] } = useQuery({
    queryKey: ["banks"],
    queryFn: listBanks,
  });
  const { data: tcTemplates = [] } = useQuery({
    queryKey: ["tc-templates"],
    queryFn: listTCTemplates,
  });

  const {
    control,
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { pi_date: dayjs().format("YYYY-MM-DD") },
  });

  // Auto-populate TC content when a template is selected
  const { data: selectedTemplate } = useQuery({
    queryKey: ["tc-templates", selectedTemplateId],
    queryFn: () => getTCTemplate(selectedTemplateId!),
    enabled: selectedTemplateId !== null,
  });
  useEffect(() => {
    if (selectedTemplate) {
      setValue("tc_content", selectedTemplate.body);
    }
  }, [selectedTemplate, setValue]);

  const createMutation = useMutation({
    mutationFn: createProformaInvoice,
    onSuccess: (pi) => {
      message.success(`${pi.pi_number} created. Add line items now.`);
      navigate(`/proforma-invoices/${pi.id}`);
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || "Failed to create Proforma Invoice.";
      message.error(detail);
    },
  });

  function onSubmit(values: FormValues) {
    // Clean up nullish optional fields
    const payload: Record<string, unknown> = { ...values };
    Object.keys(payload).forEach((k) => {
      if (payload[k] === undefined || payload[k] === "") payload[k] = null;
    });
    // Always send exporter and consignee as non-null
    createMutation.mutate(payload as any);
  }

  return (
    <div style={{ maxWidth: 880 }}>
      {/* Back */}
      <button
        onClick={() => navigate("/proforma-invoices")}
        style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          background: "transparent", border: "none", cursor: "pointer",
          fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)",
          marginBottom: 20, padding: 0,
        }}
      >
        <ArrowLeft size={15} strokeWidth={1.5} /> Back to Proforma Invoices
      </button>

      <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", marginBottom: 24 }}>
        New Proforma Invoice
      </h1>

      <form onSubmit={handleSubmit(onSubmit)}>

        {/* Section 1 — Invoice Header (FR-09.1) */}
        <div style={CARD_STYLE}>
          <h2 style={SECTION_TITLE_STYLE}>Invoice Header</h2>
          <div style={{ ...GRID2, marginBottom: 16 }}>
            <div>
              <label style={LABEL_STYLE}>Exporter <span style={{ color: "#e53e3e" }}>*</span></label>
              <Controller
                name="exporter"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    placeholder="Select exporter"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    options={exporters.map((o: any) => ({ value: o.id, label: o.name }))}
                  />
                )}
              />
              <FieldError msg={errors.exporter?.message} />
            </div>
            <div>
              <label style={LABEL_STYLE}>Consignee <span style={{ color: "#e53e3e" }}>*</span></label>
              <Controller
                name="consignee"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    placeholder="Select consignee"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    options={consignees.map((o: any) => ({ value: o.id, label: o.name }))}
                  />
                )}
              />
              <FieldError msg={errors.consignee?.message} />
            </div>
          </div>

          <div style={{ ...GRID2, marginBottom: 16 }}>
            <div>
              <label style={LABEL_STYLE}>Buyer (if other than Consignee)</label>
              <Controller
                name="buyer"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    placeholder="Select buyer"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    options={buyers.map((o: any) => ({ value: o.id, label: o.name }))}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL_STYLE}>Proforma Invoice Date</label>
              <Controller
                name="pi_date"
                control={control}
                render={({ field }) => (
                  <DatePicker
                    value={field.value ? dayjs(field.value) : dayjs()}
                    onChange={(d) => field.onChange(d ? d.format("YYYY-MM-DD") : null)}
                    style={{ width: "100%" }}
                  />
                )}
              />
            </div>
          </div>

          <div style={{ ...GRID2, marginBottom: 16 }}>
            <div>
              <label style={LABEL_STYLE}>Buyer Order No</label>
              <input {...register("buyer_order_no")} style={INPUT_STYLE} placeholder="e.g. PO-2026-001" />
            </div>
            <div>
              <label style={LABEL_STYLE}>Buyer Order Date</label>
              <Controller
                name="buyer_order_date"
                control={control}
                render={({ field }) => (
                  <DatePicker
                    value={field.value ? dayjs(field.value) : null}
                    onChange={(d) => field.onChange(d ? d.format("YYYY-MM-DD") : null)}
                    style={{ width: "100%" }}
                  />
                )}
              />
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={LABEL_STYLE}>Other References</label>
            <textarea {...register("other_references")} style={{ ...INPUT_STYLE, resize: "vertical", minHeight: 72 }} placeholder="Any additional references or notes" />
          </div>

          <div style={GRID2}>
            <div>
              <label style={LABEL_STYLE}>Country of Origin of Goods</label>
              <Controller
                name="country_of_origin"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    placeholder="Select country"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    options={countries.map((c: any) => ({ value: c.id, label: c.name }))}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL_STYLE}>Country of Final Destination</label>
              <Controller
                name="country_of_final_destination"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    placeholder="Select country"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    options={countries.map((c: any) => ({ value: c.id, label: c.name }))}
                  />
                )}
              />
            </div>
          </div>
        </div>

        {/* Section 2 — Shipping & Logistics (FR-09.2) */}
        <div style={CARD_STYLE}>
          <h2 style={SECTION_TITLE_STYLE}>Shipping &amp; Logistics</h2>

          <div style={{ ...GRID3, marginBottom: 16 }}>
            <div>
              <label style={LABEL_STYLE}>Pre-Carriage By</label>
              <Controller
                name="pre_carriage_by"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    placeholder="Select"
                    style={{ width: "100%" }}
                    options={preCarriageOptions.map((p: any) => ({ value: p.id, label: p.name }))}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL_STYLE}>Place of Receipt by Pre-Carrier</label>
              <Controller
                name="place_of_receipt"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    placeholder="Select location"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    options={locations.map((l: any) => ({ value: l.id, label: l.name }))}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL_STYLE}>Vessel / Flight No</label>
              <input {...register("vessel_flight_no")} style={INPUT_STYLE} placeholder="e.g. MV Pacific Star" />
            </div>
          </div>

          <div style={{ ...GRID3, marginBottom: 16 }}>
            <div>
              <label style={LABEL_STYLE}>Port of Loading</label>
              <Controller
                name="port_of_loading"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    placeholder="Select port"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    options={ports.map((p: any) => ({ value: p.id, label: `${p.name} (${p.code})` }))}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL_STYLE}>Port of Discharge</label>
              <Controller
                name="port_of_discharge"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    placeholder="Select port"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    options={ports.map((p: any) => ({ value: p.id, label: `${p.name} (${p.code})` }))}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL_STYLE}>Final Destination</label>
              <Controller
                name="final_destination"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    placeholder="Select location"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    options={locations.map((l: any) => ({ value: l.id, label: l.name }))}
                  />
                )}
              />
            </div>
          </div>
        </div>

        {/* Section 3 — Payment & Terms (FR-09.3) */}
        <div style={CARD_STYLE}>
          <h2 style={SECTION_TITLE_STYLE}>Payment &amp; Terms</h2>

          <div style={{ ...GRID2, marginBottom: 16 }}>
            <div>
              <label style={LABEL_STYLE}>Payment Terms <span style={{ color: "#e53e3e" }}>*</span></label>
              <Controller
                name="payment_terms"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    placeholder="Select payment terms"
                    style={{ width: "100%" }}
                    options={paymentTerms.map((pt: any) => ({ value: pt.id, label: pt.name }))}
                  />
                )}
              />
              <FieldError msg={errors.payment_terms?.message} />
            </div>
            <div>
              <label style={LABEL_STYLE}>Incoterms <span style={{ color: "#e53e3e" }}>*</span></label>
              <Controller
                name="incoterms"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    placeholder="Select incoterms"
                    style={{ width: "100%" }}
                    showSearch
                    optionFilterProp="label"
                    options={incoterms.map((i: any) => ({ value: i.id, label: `${i.code} – ${i.full_name}` }))}
                  />
                )}
              />
              <FieldError msg={errors.incoterms?.message} />
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={LABEL_STYLE}>Bank (for payment details on PDF)</label>
            <Controller
              name="bank"
              control={control}
              render={({ field }) => (
                <Select
                  {...field}
                  allowClear
                  placeholder="Select bank"
                  style={{ width: "100%" }}
                  showSearch
                  optionFilterProp="label"
                  options={banks.map((b: any) => ({ value: b.id, label: `${b.bank_name} – ${b.beneficiary_name}` }))}
                />
              )}
            />
          </div>

          <div style={{ ...GRID2, marginBottom: 16 }}>
            <div>
              <label style={LABEL_STYLE}>Validity for Acceptance</label>
              <Controller
                name="validity_for_acceptance"
                control={control}
                render={({ field }) => (
                  <DatePicker
                    value={field.value ? dayjs(field.value) : null}
                    onChange={(d) => field.onChange(d ? d.format("YYYY-MM-DD") : null)}
                    style={{ width: "100%" }}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL_STYLE}>Validity for Shipment</label>
              <Controller
                name="validity_for_shipment"
                control={control}
                render={({ field }) => (
                  <DatePicker
                    value={field.value ? dayjs(field.value) : null}
                    onChange={(d) => field.onChange(d ? d.format("YYYY-MM-DD") : null)}
                    style={{ width: "100%" }}
                  />
                )}
              />
            </div>
          </div>

          <div style={GRID2}>
            <div>
              <label style={LABEL_STYLE}>Partial Shipment</label>
              <Controller
                name="partial_shipment"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    placeholder="Select"
                    style={{ width: "100%" }}
                    options={Object.entries(SHIPMENT_OPTION_LABELS).map(([v, l]) => ({ value: v, label: l }))}
                  />
                )}
              />
            </div>
            <div>
              <label style={LABEL_STYLE}>Transshipment</label>
              <Controller
                name="transshipment"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    allowClear
                    placeholder="Select"
                    style={{ width: "100%" }}
                    options={Object.entries(SHIPMENT_OPTION_LABELS).map(([v, l]) => ({ value: v, label: l }))}
                  />
                )}
              />
            </div>
          </div>
        </div>

        {/* Section 4 — Terms & Conditions (FR-09.4) */}
        <div style={CARD_STYLE}>
          <h2 style={SECTION_TITLE_STYLE}>Terms &amp; Conditions</h2>
          <div style={{ marginBottom: 16 }}>
            <label style={LABEL_STYLE}>T&amp;C Template</label>
            <Controller
              name="tc_template"
              control={control}
              render={({ field }) => (
                <Select
                  {...field}
                  allowClear
                  placeholder="Select template (optional)"
                  style={{ width: "100%" }}
                  onChange={(val) => {
                    field.onChange(val ?? null);
                    setSelectedTemplateId(val ?? null);
                  }}
                  options={tcTemplates.map((t: any) => ({ value: t.id, label: t.name }))}
                />
              )}
            />
          </div>
          {selectedTemplate && (
            <div
              style={{
                background: "var(--bg-base)",
                border: "1px solid var(--border-light)",
                borderRadius: 8,
                padding: "14px 16px",
                fontFamily: "var(--font-body)",
                fontSize: 13,
                color: "var(--text-secondary)",
                maxHeight: 200,
                overflowY: "auto",
              }}
              dangerouslySetInnerHTML={{ __html: selectedTemplate.body }}
            />
          )}
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
          <button
            type="button"
            onClick={() => navigate("/proforma-invoices")}
            style={{
              background: "transparent",
              color: "var(--text-secondary)",
              border: "1px solid var(--border-medium)",
              borderRadius: 8,
              padding: "9px 20px",
              fontFamily: "var(--font-body)",
              fontSize: 14,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            style={{
              background: "var(--primary)",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "9px 24px",
              fontFamily: "var(--font-body)",
              fontSize: 14,
              fontWeight: 500,
              cursor: createMutation.isPending ? "not-allowed" : "pointer",
              opacity: createMutation.isPending ? 0.7 : 1,
            }}
          >
            {createMutation.isPending ? "Saving…" : "Save Invoice"}
          </button>
        </div>
      </form>
    </div>
  );
}
