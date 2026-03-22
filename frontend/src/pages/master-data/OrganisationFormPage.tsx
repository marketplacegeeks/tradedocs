// Organisation create / edit form — design system card layout.
// When opened at /master-data/organisations/new → creates a new organisation.
// When opened at /master-data/organisations/:id/edit → loads and edits an existing one.
//
// Four sections matching FR-04:
//   1. General Information  2. Document Role Tags
//   3. Addresses            4. Tax Codes (optional)

import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import { message, Select } from "antd";

import {
  createOrganisation, getOrganisation, updateOrganisation,
} from "../../api/organisations";
import { listCountries } from "../../api/countries";
import { ADDRESS_TYPES, ADDRESS_TYPE_LABELS, ORG_TAGS, ORG_TAG_LABELS, COUNTRY_DIAL_CODES } from "../../utils/constants";

// ---- Zod schema -----------------------------------------------------------

const addressSchema = z.object({
  id: z.number().optional(),
  address_type: z.enum(["REGISTERED", "FACTORY", "OFFICE"]),
  line1: z.string().min(1, "Address Line 1 is required"),
  line2: z.string().optional().default(""),
  city: z.string().min(1, "City is required"),
  state: z.string().optional().default(""),
  pin: z.string().optional().default(""),
  country: z.number({ required_error: "Country is required" }),
  email: z.string().email("Must be a valid email address").optional().or(z.literal("")).default(""),
  contact_name: z.string().optional().default(""),
  phone_country_code: z.string().optional().default(""),
  phone_number: z.string().optional().default(""),
  iec_code: z.string().max(10).optional().default(""),
  tax_type: z.string().optional().default(""),
  tax_code: z.string().optional().default(""),
});

const formSchema = z.object({
  name: z.string().min(1, "Organisation name is required").max(255),
  tags: z.array(z.string()).min(1, "Select at least one document role tag"),
  addresses: z.array(addressSchema).min(1, "At least one address is required"),
});

type FormValues = z.infer<typeof formSchema>;

// ---- Shared field components (same pattern as BankFormPage) ---------------

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

// White card section with a labelled header
function Section({
  title, subtitle, children,
}: {
  title: string; subtitle?: string; children: React.ReactNode;
}) {
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
          display: "flex",
          alignItems: "baseline",
          gap: 10,
        }}
      >
        <span style={{ fontFamily: "var(--font-heading)", fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
          {title}
        </span>
        {subtitle && (
          <span style={{ fontFamily: "var(--font-body)", fontSize: 12, color: "#F5222D" }}>
            {subtitle}
          </span>
        )}
      </div>
      <div style={{ padding: "20px 24px" }}>{children}</div>
    </div>
  );
}

// Two-column grid row
function Row2({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>{children}</div>;
}

// Three-column grid row
function Row3({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>{children}</div>;
}

// ---- Page -----------------------------------------------------------------

export default function OrganisationFormPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = Boolean(id);
  const queryClient = useQueryClient();

  const { data: countries = [] } = useQuery({
    queryKey: ["countries"],
    queryFn: listCountries,
  });

  const { data: existingOrg, isLoading: orgLoading } = useQuery({
    queryKey: ["organisations", id],
    queryFn: () => getOrganisation(Number(id)),
    enabled: isEditMode,
  });

  const {
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      tags: [],
      addresses: [
        {
          address_type: "REGISTERED",
          line1: "", line2: "", city: "", state: "", pin: "",
          country: undefined as unknown as number,
          email: "", contact_name: "", phone_country_code: "", phone_number: "",
          iec_code: "", tax_type: "", tax_code: "",
        },
      ],
    },
  });

  // Populate form when editing an existing organisation
  useEffect(() => {
    if (existingOrg) {
      reset({
        name: existingOrg.name,
        tags: existingOrg.tags.map((t) => t.tag),
        addresses: existingOrg.addresses.map((a) => ({
          id: a.id,
          address_type: a.address_type as "REGISTERED" | "FACTORY" | "OFFICE",
          line1: a.line1, line2: a.line2 ?? "", city: a.city,
          state: a.state ?? "", pin: a.pin ?? "",
          country: a.country, email: a.email, contact_name: a.contact_name,
          phone_country_code: a.phone_country_code ?? "",
          phone_number: a.phone_number ?? "",
          iec_code: a.iec_code ?? "",
          tax_type: a.tax_type ?? "",
          tax_code: a.tax_code ?? "",
        })),
      });
    }
  }, [existingOrg, reset]);

  const { fields: addressFields, append: addAddress, remove: removeAddress } =
    useFieldArray({ control, name: "addresses" });

  const selectedTags = watch("tags");

  // Recursively flatten a DRF error value into a plain string.
  // Handles: string, string[], object (nested serializer errors), array of objects.
  function flattenDrfError(value: unknown): string {
    if (typeof value === "string") return value;
    if (Array.isArray(value)) {
      return value.map(flattenDrfError).filter(Boolean).join(", ");
    }
    if (value && typeof value === "object") {
      return Object.entries(value as Record<string, unknown>)
        .map(([k, v]) => `${k}: ${flattenDrfError(v)}`)
        .join("; ");
    }
    return String(value ?? "");
  }

  // Extract a human-readable message from DRF error responses.
  // DRF returns either { detail: "..." } for auth/permission errors,
  // or { field: [...], ... } for validation errors (potentially nested).
  function extractApiError(err: unknown): string {
    const data = (err as { response?: { data?: unknown } })?.response?.data;
    if (!data || typeof data !== "object") return "Failed to save organisation.";
    const record = data as Record<string, unknown>;
    if (typeof record.detail === "string") return record.detail;
    const lines = Object.entries(record).map(
      ([field, msgs]) => `${field}: ${flattenDrfError(msgs)}`
    );
    return lines.length > 0 ? lines.join("\n") : "Failed to save organisation.";
  }

  const createMutation = useMutation({
    mutationFn: (values: FormValues) =>
      createOrganisation({
        name: values.name,
        tags: values.tags.map((tag) => ({ tag })),
        addresses: values.addresses,
      }),
    onSuccess: () => {
      message.success("Organisation created.");
      queryClient.invalidateQueries({ queryKey: ["organisations"] });
      navigate("/master-data/organisations");
    },
    onError: (err: unknown) => {
      message.error(extractApiError(err));
    },
  });

  const updateMutation = useMutation({
    mutationFn: (values: FormValues) =>
      updateOrganisation(Number(id), {
        name: values.name,
        tags: values.tags.map((tag) => ({ tag })),
        addresses: values.addresses,
      }),
    onSuccess: () => {
      message.success("Organisation updated.");
      queryClient.invalidateQueries({ queryKey: ["organisations"] });
      queryClient.invalidateQueries({ queryKey: ["organisations", id] });
      navigate("/master-data/organisations");
    },
    onError: (err: unknown) => {
      message.error(extractApiError(err));
    },
  });

  function onSubmit(values: FormValues) {
    if (isEditMode) {
      updateMutation.mutate(values);
    } else {
      createMutation.mutate(values);
    }
  }

  const isPending = isSubmitting || createMutation.isPending || updateMutation.isPending;

  const sort = (arr: { value: any; label: string }[]) =>
    [...arr].sort((a, b) => a.label.localeCompare(b.label));

  const countryOptions = sort(countries.map((c) => ({ value: c.id, label: `${c.name} (${c.iso2})` })));
  const addressTypeOptions = sort(Object.values(ADDRESS_TYPES).map((type) => ({
    value: type,
    label: ADDRESS_TYPE_LABELS[type],
  })));

  if (isEditMode && orgLoading) {
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
          onClick={() => navigate("/master-data/organisations")}
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
            {isEditMode ? "Edit Organisation" : "New Organisation"}
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)" }}>
            {isEditMode ? "Update the organisation details below." : "Fill in the details to register a new organisation."}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>

        {/* ── Section 1: General Information ────────────────────────────── */}
        <Section title="General Information">
          <Field label="Organisation Name" required error={errors.name?.message}>
            <Controller name="name" control={control} render={({ field }) =>
              <input {...field} style={inputStyle(!!errors.name)} placeholder="e.g. Sunrise Exports Pvt Ltd" />
            } />
          </Field>
        </Section>

        {/* ── Section 2: Document Role Tags ─────────────────────────────── */}
        <Section title="Organisation Type" subtitle="* At least one required">
          {errors.tags && (
            <p style={{ color: "#F5222D", fontSize: 12, marginBottom: 12, fontFamily: "var(--font-body)" }}>
              {errors.tags.message}
            </p>
          )}
          <Controller
            name="tags"
            control={control}
            render={({ field }) => (
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                {Object.values(ORG_TAGS).map((tag) => {
                  const checked = field.value.includes(tag);
                  return (
                    <label
                      key={tag}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        padding: "8px 14px",
                        borderRadius: 8,
                        border: `1px solid ${checked ? "var(--primary)" : "var(--border-medium)"}`,
                        background: checked ? "var(--primary-light)" : "var(--bg-input)",
                        cursor: "pointer",
                        fontFamily: "var(--font-body)",
                        fontSize: 13,
                        fontWeight: checked ? 600 : 400,
                        color: checked ? "var(--primary)" : "var(--text-secondary)",
                        transition: "all 0.15s ease",
                        userSelect: "none",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => {
                          const next = e.target.checked
                            ? [...field.value, tag]
                            : field.value.filter((t) => t !== tag);
                          field.onChange(next);
                        }}
                        style={{ display: "none" }}
                      />
                      {ORG_TAG_LABELS[tag]}
                    </label>
                  );
                })}
              </div>
            )}
          />
        </Section>

        {/* ── Section 3: Addresses ──────────────────────────────────────── */}
        <Section title="Addresses" subtitle="* At least one required">
          {errors.addresses?.root && (
            <p style={{ color: "#F5222D", fontSize: 12, marginBottom: 12, fontFamily: "var(--font-body)" }}>
              {errors.addresses.root.message}
            </p>
          )}

          {addressFields.map((field, index) => (
            <div key={field.id}>
              {/* Address block divider (not for the first one) */}
              {index > 0 && (
                <div style={{ borderTop: "1px solid var(--border-light)", margin: "20px 0" }} />
              )}

              {/* Address header row */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                <span style={{ fontFamily: "var(--font-heading)", fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                  Address {index + 1}
                </span>
                {addressFields.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeAddress(index)}
                    style={{
                      display: "inline-flex", alignItems: "center", gap: 4,
                      padding: "4px 10px", background: "transparent",
                      border: "1px solid var(--pastel-pink-text)", borderRadius: 6,
                      fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 500,
                      color: "var(--pastel-pink-text)", cursor: "pointer",
                    }}
                    onMouseEnter={(e) =>
                      ((e.currentTarget as HTMLButtonElement).style.background = "var(--pastel-pink)")
                    }
                    onMouseLeave={(e) =>
                      ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
                    }
                  >
                    <Trash2 size={12} strokeWidth={1.5} />
                    Remove
                  </button>
                )}
              </div>

              <Row2>
                <Field label="Address Type" required error={errors.addresses?.[index]?.address_type?.message}>
                  <Controller name={`addresses.${index}.address_type`} control={control} render={({ field: f }) =>
                    <Select value={f.value} onChange={(v) => f.onChange(v as string)} options={addressTypeOptions} showSearch optionFilterProp="label" style={{ width: "100%" }} status={errors.addresses?.[index]?.address_type ? "error" : undefined} />
                  } />
                </Field>
                <Field label="Address Line 1" required error={errors.addresses?.[index]?.line1?.message}>
                  <Controller name={`addresses.${index}.line1`} control={control} render={({ field: f }) =>
                    <input {...f} style={inputStyle(!!errors.addresses?.[index]?.line1)} />
                  } />
                </Field>
              </Row2>

              <Row2>
                <Field label="Address Line 2" error={errors.addresses?.[index]?.line2?.message}>
                  <Controller name={`addresses.${index}.line2`} control={control} render={({ field: f }) =>
                    <input {...f} value={f.value ?? ""} style={inputStyle()} />
                  } />
                </Field>
                <Field label="City" required error={errors.addresses?.[index]?.city?.message}>
                  <Controller name={`addresses.${index}.city`} control={control} render={({ field: f }) =>
                    <input {...f} style={inputStyle(!!errors.addresses?.[index]?.city)} />
                  } />
                </Field>
              </Row2>

              <Row3>
                <Field label="State / Province">
                  <Controller name={`addresses.${index}.state`} control={control} render={({ field: f }) =>
                    <input {...f} value={f.value ?? ""} style={inputStyle()} />
                  } />
                </Field>
                <Field label="PIN / ZIP">
                  <Controller name={`addresses.${index}.pin`} control={control} render={({ field: f }) =>
                    <input {...f} value={f.value ?? ""} style={inputStyle()} />
                  } />
                </Field>
                <Field label="Country" required error={errors.addresses?.[index]?.country?.message}>
                  <Controller name={`addresses.${index}.country`} control={control} render={({ field: f }) =>
                    <Select
                      value={f.value}
                      onChange={(v) => {
                        f.onChange(v);
                        // Always update the dial code when the country changes.
                        const iso2 = countries.find((c) => c.id === Number(v))?.iso2 ?? "";
                        const dialCode = COUNTRY_DIAL_CODES[iso2] ?? "";
                        setValue(`addresses.${index}.phone_country_code`, dialCode, { shouldValidate: false });
                      }}
                      options={countryOptions}
                      placeholder="Select country"
                      showSearch
                      optionFilterProp="label"
                      style={{ width: "100%" }}
                      status={errors.addresses?.[index]?.country ? "error" : undefined}
                    />
                  } />
                </Field>
              </Row3>

              <Row2>
                <Field label="Email" error={errors.addresses?.[index]?.email?.message}>
                  <Controller name={`addresses.${index}.email`} control={control} render={({ field: f }) =>
                    <input {...f} type="email" style={inputStyle(!!errors.addresses?.[index]?.email)} />
                  } />
                </Field>
                <Field label="Contact Name" error={errors.addresses?.[index]?.contact_name?.message}>
                  <Controller name={`addresses.${index}.contact_name`} control={control} render={({ field: f }) =>
                    <input {...f} style={inputStyle(!!errors.addresses?.[index]?.contact_name)} />
                  } />
                </Field>
              </Row2>

              <Row2>
                <Field label="Phone Dial Code" hint="Optional. e.g. +91">
                  <Controller name={`addresses.${index}.phone_country_code`} control={control} render={({ field: f }) =>
                    <input {...f} value={f.value ?? ""} style={inputStyle()} placeholder="+91" maxLength={5} />
                  } />
                </Field>
                <Field label="Phone Number" hint="Optional.">
                  <Controller name={`addresses.${index}.phone_number`} control={control} render={({ field: f }) =>
                    <input {...f} value={f.value ?? ""} style={inputStyle()} placeholder="9876543210" />
                  } />
                </Field>
              </Row2>

              <Row3>
                <Field label="IEC Code" hint="Optional. e.g. AABCD1234E">
                  <Controller name={`addresses.${index}.iec_code`} control={control} render={({ field: f }) =>
                    <input {...f} value={f.value ?? ""} style={{ ...inputStyle(), textTransform: "uppercase" }} placeholder="AABCD1234E" maxLength={10} />
                  } />
                </Field>
                <Field label="Tax Type" hint="e.g. GSTIN, PAN, VAT">
                  <Controller name={`addresses.${index}.tax_type`} control={control} render={({ field: f }) =>
                    <input {...f} value={f.value ?? ""} style={inputStyle()} placeholder="e.g. GSTIN" />
                  } />
                </Field>
                <Field label="Tax Code">
                  <Controller name={`addresses.${index}.tax_code`} control={control} render={({ field: f }) =>
                    <input {...f} value={f.value ?? ""} style={inputStyle()} placeholder="e.g. 22AAAAA0000A1Z5" />
                  } />
                </Field>
              </Row3>
            </div>
          ))}

          {/* Add address button */}
          <button
            type="button"
            onClick={() =>
              addAddress({
                address_type: "OFFICE",
                line1: "", line2: "", city: "", state: "", pin: "",
                country: undefined as unknown as number,
                email: "", contact_name: "", phone_country_code: "", phone_number: "",
                iec_code: "", tax_type: "", tax_code: "",
              })
            }
            style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              padding: "8px 14px", marginTop: 8,
              background: "transparent",
              border: "1px dashed var(--border-medium)",
              borderRadius: 8, cursor: "pointer",
              fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500,
              color: "var(--text-secondary)",
            }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
            }
          >
            <Plus size={14} strokeWidth={2} />
            Add Another Address
          </button>
        </Section>

        {/* ── Form actions ──────────────────────────────────────────────── */}
        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="submit"
            disabled={isPending}
            style={{
              padding: "10px 20px",
              background: isPending ? "var(--border-medium)" : "var(--primary)",
              color: "#fff", border: "none", borderRadius: 8,
              fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500,
              cursor: isPending ? "not-allowed" : "pointer",
            }}
          >
            {isPending ? "Saving…" : isEditMode ? "Save Changes" : "Create Organisation"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/master-data/organisations")}
            style={{
              padding: "10px 20px", background: "transparent",
              color: "var(--text-secondary)", border: "1px solid var(--border-medium)",
              borderRadius: 8, fontFamily: "var(--font-body)", fontSize: 14,
              fontWeight: 500, cursor: "pointer",
            }}
          >
            Cancel
          </button>
        </div>

      </form>
    </div>
  );
}
