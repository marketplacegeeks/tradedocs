// Bank create / edit form — design system card layout.

import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft } from "lucide-react";

import { createBank, getBank, updateBank } from "../../api/banks";
import { listCountries } from "../../api/countries";
import { listCurrencies } from "../../api/currencies";
import { listOrganisations } from "../../api/organisations";
import { ACCOUNT_TYPES, ACCOUNT_TYPE_LABELS } from "../../utils/constants";
import type { AccountType } from "../../utils/constants";

// ---- Schema ---------------------------------------------------------------

const bankSchema = z
  .object({
    organisation: z.number({ required_error: "Required" }),
    nickname: z.string().min(1, "Required").max(255),
    beneficiary_name: z.string().min(1, "Required").max(255),
    bank_name: z.string().min(1, "Required").max(255),
    bank_country: z.number({ required_error: "Required" }),
    branch_name: z.string().min(1, "Required").max(255),
    branch_address: z.string().optional().default(""),
    account_number: z.string().min(1, "Required").max(50),
    account_type: z.enum(["CURRENT", "SAVINGS", "CHECKING"], { required_error: "Required" }),
    currency: z.number({ required_error: "Required" }),
    swift_code: z
      .string().optional()
      .refine((v) => !v || /^[A-Z0-9]{8}$|^[A-Z0-9]{11}$/.test(v), {
        message: "Must be 8 or 11 uppercase letters/digits",
      })
      .default(""),
    iban: z
      .string().optional()
      .refine((v) => !v || /^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$/.test(v), {
        message: "2-letter country code + 2 digits + up to 30 alphanumeric",
      })
      .default(""),
    routing_number: z.string().optional().default(""),
    ad_code: z.string().optional().default(""),
    // Intermediary institution — optional, but all-or-nothing
    intermediary_bank_name: z.string().optional().default(""),
    intermediary_account_number: z.string().optional().default(""),
    intermediary_swift_code: z
      .string().optional()
      .refine((v) => !v || /^[A-Z0-9]{8}$|^[A-Z0-9]{11}$/.test(v), {
        message: "Must be 8 or 11 uppercase letters/digits",
      })
      .default(""),
    intermediary_currency: z.number().nullable().optional(),
  })
  .superRefine((data, ctx) => {
    const fields = [
      data.intermediary_bank_name,
      data.intermediary_account_number,
      data.intermediary_swift_code,
      data.intermediary_currency,
    ];
    const filled = fields.filter(Boolean);
    if (filled.length > 0 && filled.length < 4) {
      if (!data.intermediary_bank_name)
        ctx.addIssue({ code: "custom", path: ["intermediary_bank_name"], message: "Required when any intermediary field is entered" });
      if (!data.intermediary_account_number)
        ctx.addIssue({ code: "custom", path: ["intermediary_account_number"], message: "Required when any intermediary field is entered" });
      if (!data.intermediary_swift_code)
        ctx.addIssue({ code: "custom", path: ["intermediary_swift_code"], message: "Required when any intermediary field is entered" });
      if (!data.intermediary_currency)
        ctx.addIssue({ code: "custom", path: ["intermediary_currency"], message: "Required when any intermediary field is entered" });
    }
  });

type BankFormValues = z.infer<typeof bankSchema>;

// ---- Field components -----------------------------------------------------

function Field({
  label, required, error, hint, children,
}: {
  label: string; required?: boolean; error?: string; hint?: string; children: React.ReactNode;
}) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label
        style={{
          display: "block",
          fontFamily: "var(--font-body)",
          fontSize: 13,
          fontWeight: 500,
          color: "var(--text-primary)",
          marginBottom: 6,
        }}
      >
        {label}
        {required && <span style={{ color: "#F5222D", marginLeft: 3 }}>*</span>}
      </label>
      {children}
      {error && (
        <p style={{ color: "#F5222D", fontSize: 12, marginTop: 4, fontFamily: "var(--font-body)" }}>{error}</p>
      )}
      {!error && hint && (
        <p style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 4, fontFamily: "var(--font-body)" }}>{hint}</p>
      )}
    </div>
  );
}

const inputStyle = (hasError?: boolean): React.CSSProperties => ({
  width: "100%",
  padding: "9px 12px",
  background: "var(--bg-input)",
  border: `1px solid ${hasError ? "#F5222D" : "var(--border-medium)"}`,
  borderRadius: 8,
  fontFamily: "var(--font-body)",
  fontSize: 14,
  color: "var(--text-primary)",
  outline: "none",
  boxSizing: "border-box",
});

function StyledSelect({
  value, onChange, options, placeholder, hasError,
}: {
  value: string | number | undefined | null;
  onChange: (v: number | string) => void;
  options: { value: string | number; label: string }[];
  placeholder?: string;
  hasError?: boolean;
}) {
  return (
    <select
      value={value ?? ""}
      onChange={(e) => {
        const raw = e.target.value;
        onChange(isNaN(Number(raw)) ? raw : Number(raw));
      }}
      style={{ ...inputStyle(hasError), appearance: "auto" }}
    >
      <option value="">{placeholder ?? "Select…"}</option>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

// ---- Section card ---------------------------------------------------------

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-light)",
        borderRadius: 14,
        boxShadow: "var(--shadow-card)",
        marginBottom: 16,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          padding: "14px 24px",
          borderBottom: "1px solid var(--border-light)",
        }}
      >
        <div style={{ fontFamily: "var(--font-heading)", fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
          {title}
        </div>
        {description && (
          <div style={{ fontFamily: "var(--font-body)", fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
            {description}
          </div>
        )}
      </div>
      <div style={{ padding: "20px 24px" }}>{children}</div>
    </div>
  );
}

// ---- Grid helpers ---------------------------------------------------------

function Row2({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>{children}</div>;
}
function Row3({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>{children}</div>;
}

// ---- Page -----------------------------------------------------------------

export default function BankFormPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const isEditing = Boolean(id);

  const { control, handleSubmit, reset, formState: { errors } } = useForm<BankFormValues>({
    resolver: zodResolver(bankSchema),
    defaultValues: {
      organisation: undefined,
      nickname: "", beneficiary_name: "", bank_name: "",
      branch_name: "", branch_address: "", account_number: "",
      account_type: undefined, swift_code: "", iban: "", routing_number: "", ad_code: "",
      intermediary_bank_name: "", intermediary_account_number: "",
      intermediary_swift_code: "", intermediary_currency: null,
    },
  });

  const { data: countries = [] } = useQuery({ queryKey: ["countries"], queryFn: listCountries });
  const { data: currencies = [] } = useQuery({ queryKey: ["currencies"], queryFn: listCurrencies });
  const { data: exporters = [] } = useQuery({
    queryKey: ["organisations", "EXPORTER"],
    queryFn: () => listOrganisations("EXPORTER"),
  });
  const { data: existingBank, isLoading } = useQuery({
    queryKey: ["banks", Number(id)],
    queryFn: () => getBank(Number(id)),
    enabled: isEditing,
  });

  useEffect(() => {
    if (existingBank) {
      reset({
        organisation: existingBank.organisation,
        nickname: existingBank.nickname,
        beneficiary_name: existingBank.beneficiary_name,
        bank_name: existingBank.bank_name,
        bank_country: existingBank.bank_country,
        branch_name: existingBank.branch_name,
        branch_address: existingBank.branch_address,
        account_number: existingBank.account_number,
        account_type: existingBank.account_type as "CURRENT" | "SAVINGS" | "CHECKING",
        currency: existingBank.currency,
        swift_code: existingBank.swift_code,
        iban: existingBank.iban,
        routing_number: existingBank.routing_number,
        ad_code: existingBank.ad_code,
        intermediary_bank_name: existingBank.intermediary_bank_name,
        intermediary_account_number: existingBank.intermediary_account_number,
        intermediary_swift_code: existingBank.intermediary_swift_code,
        intermediary_currency: existingBank.intermediary_currency,
      });
    }
  }, [existingBank, reset]);

  const saveMutation = useMutation({
    mutationFn: (values: BankFormValues) =>
      isEditing ? updateBank(Number(id), values) : createBank(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["banks"] });
      navigate("/master-data/banks");
    },
  });

  const countryOptions = countries.map((c) => ({ value: c.id, label: `${c.name} (${c.iso2})` }));
  const currencyOptions = currencies.map((c) => ({ value: c.id, label: `${c.code} – ${c.name}` }));
  const exporterOptions = exporters.map((o) => ({ value: o.id, label: o.name }));
  const accountTypeOptions = Object.entries(ACCOUNT_TYPE_LABELS).map(
    ([value, label]) => ({ value: value as AccountType, label })
  );

  if (isEditing && isLoading) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-body)" }}>
        Loading…
      </div>
    );
  }

  return (
    <div>
      {/* Page header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <button
          onClick={() => navigate("/master-data/banks")}
          style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            width: 32, height: 32, borderRadius: 8, border: "1px solid var(--border-medium)",
            background: "var(--bg-surface)", cursor: "pointer", color: "var(--text-secondary)",
          }}
        >
          <ArrowLeft size={16} strokeWidth={1.5} />
        </button>
        <div>
          <h1 style={{ fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700, color: "var(--text-primary)", marginBottom: 2 }}>
            {isEditing ? "Edit Bank Account" : "New Bank Account"}
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)" }}>
            {isEditing ? "Update the bank account details below." : "Fill in the details to add a new bank account."}
          </p>
        </div>
      </div>

      {saveMutation.isError && (
        <div style={{ background: "var(--pastel-pink)", color: "var(--pastel-pink-text)", borderRadius: 8, padding: "10px 16px", marginBottom: 16, fontFamily: "var(--font-body)", fontSize: 13 }}>
          Failed to save. Please check the form for errors.
        </div>
      )}

      <form onSubmit={handleSubmit((v) => saveMutation.mutate(v))}>
        <Section title="Account Details">
          {/* Exporter Organisation — full width */}
          <Field label="Exporter Organisation" required error={errors.organisation?.message}>
            <Controller name="organisation" control={control} render={({ field }) =>
              <StyledSelect
                value={field.value}
                onChange={(v) => field.onChange(v as number)}
                options={exporterOptions}
                placeholder="Select exporter…"
                hasError={!!errors.organisation}
              />
            } />
          </Field>
          <Row2>
            <Field label="Nickname" required error={errors.nickname?.message}>
              <Controller name="nickname" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.nickname)} placeholder="e.g. USD Operating Account" />
              } />
            </Field>
            <Field label="Beneficiary Name" required error={errors.beneficiary_name?.message}>
              <Controller name="beneficiary_name" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.beneficiary_name)} placeholder="Name as on wire instructions" />
              } />
            </Field>
          </Row2>
          <Row2>
            <Field label="Bank Name" required error={errors.bank_name?.message}>
              <Controller name="bank_name" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.bank_name)} placeholder="e.g. State Bank of India" />
              } />
            </Field>
            <Field label="Bank Country" required error={errors.bank_country?.message}>
              <Controller name="bank_country" control={control} render={({ field }) =>
                <StyledSelect value={field.value} onChange={field.onChange} options={countryOptions} placeholder="Select country" hasError={!!errors.bank_country} />
              } />
            </Field>
          </Row2>
          <Row2>
            <Field label="Branch Name" required error={errors.branch_name?.message}>
              <Controller name="branch_name" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.branch_name)} placeholder="e.g. Commercial Client Group" />
              } />
            </Field>
            <Field label="Branch Address" error={errors.branch_address?.message}>
              <Controller name="branch_address" control={control} render={({ field }) =>
                <textarea {...field} rows={2} style={{ ...inputStyle(), resize: "vertical" }} />
              } />
            </Field>
          </Row2>
          <Row3>
            <Field label="Account Number" required error={errors.account_number?.message}>
              <Controller name="account_number" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.account_number)} />
              } />
            </Field>
            <Field label="Account Type" required error={errors.account_type?.message}>
              <Controller name="account_type" control={control} render={({ field }) =>
                <StyledSelect value={field.value} onChange={(v) => field.onChange(v as string)} options={accountTypeOptions} placeholder="Select type" hasError={!!errors.account_type} />
              } />
            </Field>
            <Field label="Currency" required error={errors.currency?.message}>
              <Controller name="currency" control={control} render={({ field }) =>
                <StyledSelect value={field.value} onChange={field.onChange} options={currencyOptions} placeholder="Select currency" hasError={!!errors.currency} />
              } />
            </Field>
          </Row3>
        </Section>

        <Section title="Routing & Identification Codes">
          <Row3>
            <Field label="SWIFT / BIC Code" error={errors.swift_code?.message} hint="Optional. 8 or 11 characters.">
              <Controller name="swift_code" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.swift_code)} placeholder="e.g. SBININBB659" maxLength={11} />
              } />
            </Field>
            <Field label="IBAN" error={errors.iban?.message} hint="Optional. Required for EU/Middle East.">
              <Controller name="iban" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.iban)} placeholder="e.g. GB29NWBK…" maxLength={34} />
              } />
            </Field>
            <Field label="IFSC / Routing / Sort Code" error={errors.routing_number?.message} hint="Optional. India: IFSC, USA: ACH, UK: Sort.">
              <Controller name="routing_number" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.routing_number)} placeholder="e.g. SBIN0013039" />
              } />
            </Field>
          </Row3>
          <Row2>
            <Field label="AD Code" error={errors.ad_code?.message} hint="Optional. Authorised Dealer Code issued by the bank for customs/DGFT use.">
              <Controller name="ad_code" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.ad_code)} placeholder="e.g. 12345678901234" />
              } />
            </Field>
          </Row2>
        </Section>

        <Section
          title="Intermediary Institution"
          description="Optional. Fill all four fields if your bank requires a correspondent bank for a specific currency (e.g. USD payments via a US correspondent)."
        >
          <Row2>
            <Field label="Intermediary Bank Name" error={errors.intermediary_bank_name?.message}>
              <Controller name="intermediary_bank_name" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.intermediary_bank_name)} placeholder="e.g. THE BANK OF SBI NEW YORK" />
              } />
            </Field>
            <Field label="Intermediary Account Number" error={errors.intermediary_account_number?.message}>
              <Controller name="intermediary_account_number" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.intermediary_account_number)} placeholder="e.g. 77600125220002" />
              } />
            </Field>
          </Row2>
          <Row2>
            <Field label="Intermediary SWIFT Code" error={errors.intermediary_swift_code?.message} hint="8 or 11 uppercase letters/digits.">
              <Controller name="intermediary_swift_code" control={control} render={({ field }) =>
                <input {...field} style={inputStyle(!!errors.intermediary_swift_code)} placeholder="e.g. SBINUS33" maxLength={11} />
              } />
            </Field>
            <Field label="Routing Currency" error={errors.intermediary_currency?.message} hint="Currency for which this intermediary is used.">
              <Controller name="intermediary_currency" control={control} render={({ field }) =>
                <StyledSelect
                  value={field.value ?? undefined}
                  onChange={(v) => field.onChange(v === "" ? null : Number(v))}
                  options={currencyOptions}
                  placeholder="Select currency…"
                  hasError={!!errors.intermediary_currency}
                />
              } />
            </Field>
          </Row2>
        </Section>

        {/* Actions */}
        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="submit"
            disabled={saveMutation.isPending}
            style={{
              padding: "10px 20px", background: saveMutation.isPending ? "var(--border-medium)" : "var(--primary)",
              color: "#fff", border: "none", borderRadius: 8, fontFamily: "var(--font-body)",
              fontSize: 14, fontWeight: 500, cursor: saveMutation.isPending ? "not-allowed" : "pointer",
            }}
          >
            {saveMutation.isPending ? "Saving…" : isEditing ? "Save Changes" : "Create Bank Account"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/master-data/banks")}
            style={{
              padding: "10px 20px", background: "transparent", color: "var(--text-secondary)",
              border: "1px solid var(--border-medium)", borderRadius: 8, fontFamily: "var(--font-body)",
              fontSize: 14, fontWeight: 500, cursor: "pointer",
            }}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
