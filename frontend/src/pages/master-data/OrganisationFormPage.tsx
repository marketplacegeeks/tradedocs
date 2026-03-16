// Organisation create / edit form.
// When opened at /master-data/organisations/new → creates a new organisation.
// When opened at /master-data/organisations/:id/edit → loads and edits an existing one.
//
// The form has four sections matching FR-04:
//   1. General Information (name, IEC code)
//   2. Tax Codes (add/remove rows)
//   3. Addresses (add/remove rows, each row is a full address form)
//   4. Document Role Tags (multi-select checkboxes)

import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Button, Card, Checkbox, Col, Divider, Form, Input, Row, Select, Space,
  Typography, message, Spin,
} from "antd";
import { MinusCircleOutlined, PlusOutlined } from "@ant-design/icons";

import {
  createOrganisation, getOrganisation, updateOrganisation,
} from "../../api/organisations";
import { listCountries } from "../../api/countries";
import { ADDRESS_TYPES, ADDRESS_TYPE_LABELS, ORG_TAGS, ORG_TAG_LABELS } from "../../utils/constants";

const { Title } = Typography;

// ---- Zod schema -----------------------------------------------------------
// Mirrors FR-04 and the backend serializer validation rules.

const addressSchema = z.object({
  id: z.number().optional(),
  address_type: z.enum(["REGISTERED", "FACTORY", "OFFICE"]),
  line1: z.string().min(1, "Address Line 1 is required"),
  line2: z.string().optional().default(""),
  city: z.string().min(1, "City is required"),
  state: z.string().optional().default(""),
  pin: z.string().optional().default(""),
  country: z.number({ required_error: "Country is required" }),
  email: z.string().email("Must be a valid email address"),
  contact_name: z.string().min(1, "Contact name is required"),
  phone_country_code: z.string().optional().default(""),
  phone_number: z.string().optional().default(""),
});

const taxCodeSchema = z.object({
  id: z.number().optional(),
  tax_type: z.string().min(1, "Tax type is required"),
  tax_code: z.string().min(1, "Tax code is required"),
});

const formSchema = z.object({
  name: z.string().min(1, "Organisation name is required").max(255),
  iec_code: z.string().max(10).optional().nullable(),
  tags: z.array(z.string()).min(1, "Select at least one document role tag"),
  addresses: z.array(addressSchema).min(1, "At least one address is required"),
  tax_codes: z.array(taxCodeSchema).optional().default([]),
});

type FormValues = z.infer<typeof formSchema>;

// ---- Component ------------------------------------------------------------

export default function OrganisationFormPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = Boolean(id);
  const queryClient = useQueryClient();

  // Fetch countries for the address country dropdowns.
  const { data: countries = [] } = useQuery({
    queryKey: ["countries"],
    queryFn: listCountries,
  });

  // In edit mode, load the existing organisation.
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
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      iec_code: null,
      tags: [],
      addresses: [
        {
          address_type: "REGISTERED",
          line1: "",
          line2: "",
          city: "",
          state: "",
          pin: "",
          country: undefined as unknown as number,
          email: "",
          contact_name: "",
          phone_country_code: "",
          phone_number: "",
        },
      ],
      tax_codes: [],
    },
  });

  // When editing, populate the form with the existing data once it loads.
  useEffect(() => {
    if (existingOrg) {
      reset({
        name: existingOrg.name,
        iec_code: existingOrg.iec_code ?? null,
        tags: existingOrg.tags.map((t) => t.tag),
        addresses: existingOrg.addresses.map((a) => ({
          id: a.id,
          address_type: a.address_type as "REGISTERED" | "FACTORY" | "OFFICE",
          line1: a.line1,
          line2: a.line2 ?? "",
          city: a.city,
          state: a.state ?? "",
          pin: a.pin ?? "",
          country: a.country,
          email: a.email,
          contact_name: a.contact_name,
          phone_country_code: a.phone_country_code ?? "",
          phone_number: a.phone_number ?? "",
        })),
        tax_codes: existingOrg.tax_codes.map((tc) => ({
          id: tc.id,
          tax_type: tc.tax_type,
          tax_code: tc.tax_code,
        })),
      });
    }
  }, [existingOrg, reset]);

  const { fields: addressFields, append: addAddress, remove: removeAddress } =
    useFieldArray({ control, name: "addresses" });

  const { fields: taxCodeFields, append: addTaxCode, remove: removeTaxCode } =
    useFieldArray({ control, name: "tax_codes" });

  const selectedTags = watch("tags");

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (values: FormValues) =>
      createOrganisation({
        name: values.name,
        iec_code: values.iec_code || null,
        tags: values.tags.map((tag) => ({ tag })),
        addresses: values.addresses,
        tax_codes: values.tax_codes,
      }),
    onSuccess: () => {
      message.success("Organisation created.");
      queryClient.invalidateQueries({ queryKey: ["organisations"] });
      navigate("/master-data/organisations");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? "Failed to save organisation.";
      message.error(msg);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (values: FormValues) =>
      updateOrganisation(Number(id), {
        name: values.name,
        iec_code: values.iec_code || null,
        tags: values.tags.map((tag) => ({ tag })),
        addresses: values.addresses,
        tax_codes: values.tax_codes,
      }),
    onSuccess: () => {
      message.success("Organisation updated.");
      queryClient.invalidateQueries({ queryKey: ["organisations"] });
      queryClient.invalidateQueries({ queryKey: ["organisations", id] });
      navigate("/master-data/organisations");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? "Failed to save organisation.";
      message.error(msg);
    },
  });

  function onSubmit(values: FormValues) {
    if (isEditMode) {
      updateMutation.mutate(values);
    } else {
      createMutation.mutate(values);
    }
  }

  if (isEditMode && orgLoading) {
    return <Spin style={{ margin: 48 }} />;
  }

  return (
    <div style={{ padding: 24, maxWidth: 900 }}>
      <Title level={3}>
        {isEditMode ? "Edit Organisation" : "New Organisation"}
      </Title>

      <form onSubmit={handleSubmit(onSubmit)}>

        {/* ── Section 1: General Information ─────────────────────────────── */}
        <Card title="General Information" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={14}>
              <Form.Item
                label="Organisation Name"
                required
                validateStatus={errors.name ? "error" : ""}
                help={errors.name?.message}
              >
                <Controller
                  name="name"
                  control={control}
                  render={({ field }) => <Input {...field} placeholder="e.g. Sunrise Exports Pvt Ltd" />}
                />
              </Form.Item>
            </Col>
            <Col span={10}>
              <Form.Item
                label="IEC Code"
                tooltip="Required if this organisation is tagged as Exporter"
                validateStatus={errors.iec_code ? "error" : ""}
                help={errors.iec_code?.message}
              >
                <Controller
                  name="iec_code"
                  control={control}
                  render={({ field }) => (
                    <Input
                      {...field}
                      value={field.value ?? ""}
                      placeholder="e.g. AABCD1234E"
                      maxLength={10}
                      style={{ textTransform: "uppercase" }}
                    />
                  )}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* ── Section 4: Document Role Tags ──────────────────────────────── */}
        <Card
          title="Document Role Tags"
          style={{ marginBottom: 16 }}
          extra={<span style={{ color: "#ff4d4f" }}>* At least one required</span>}
        >
          <Form.Item
            validateStatus={errors.tags ? "error" : ""}
            help={errors.tags?.message}
          >
            <Controller
              name="tags"
              control={control}
              render={({ field }) => (
                <Checkbox.Group
                  value={field.value}
                  onChange={field.onChange}
                  options={Object.values(ORG_TAGS).map((tag) => ({
                    label: ORG_TAG_LABELS[tag],
                    value: tag,
                  }))}
                />
              )}
            />
          </Form.Item>
        </Card>

        {/* ── Section 3: Addresses ───────────────────────────────────────── */}
        <Card
          title="Addresses"
          style={{ marginBottom: 16 }}
          extra={<span style={{ color: "#ff4d4f" }}>* At least one required</span>}
        >
          {errors.addresses?.root && (
            <p style={{ color: "#ff4d4f" }}>{errors.addresses.root.message}</p>
          )}

          {addressFields.map((field, index) => (
            <div key={field.id}>
              {index > 0 && <Divider />}
              <Row gutter={16} align="middle">
                <Col flex="auto">
                  <Title level={5} style={{ margin: "0 0 12px" }}>
                    Address {index + 1}
                  </Title>
                </Col>
                {addressFields.length > 1 && (
                  <Col>
                    <Button
                      danger
                      type="text"
                      icon={<MinusCircleOutlined />}
                      onClick={() => removeAddress(index)}
                    >
                      Remove
                    </Button>
                  </Col>
                )}
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    label="Address Type"
                    required
                    validateStatus={errors.addresses?.[index]?.address_type ? "error" : ""}
                    help={errors.addresses?.[index]?.address_type?.message}
                  >
                    <Controller
                      name={`addresses.${index}.address_type`}
                      control={control}
                      render={({ field }) => (
                        <Select {...field}>
                          {Object.values(ADDRESS_TYPES).map((type) => (
                            <Select.Option key={type} value={type}>
                              {ADDRESS_TYPE_LABELS[type]}
                            </Select.Option>
                          ))}
                        </Select>
                      )}
                    />
                  </Form.Item>
                </Col>
                <Col span={16}>
                  <Form.Item
                    label="Address Line 1"
                    required
                    validateStatus={errors.addresses?.[index]?.line1 ? "error" : ""}
                    help={errors.addresses?.[index]?.line1?.message}
                  >
                    <Controller
                      name={`addresses.${index}.line1`}
                      control={control}
                      render={({ field }) => <Input {...field} />}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={16}>
                  <Form.Item label="Address Line 2 (optional)">
                    <Controller
                      name={`addresses.${index}.line2`}
                      control={control}
                      render={({ field }) => <Input {...field} value={field.value ?? ""} />}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="City"
                    required
                    validateStatus={errors.addresses?.[index]?.city ? "error" : ""}
                    help={errors.addresses?.[index]?.city?.message}
                  >
                    <Controller
                      name={`addresses.${index}.city`}
                      control={control}
                      render={({ field }) => <Input {...field} />}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="State / Province">
                    <Controller
                      name={`addresses.${index}.state`}
                      control={control}
                      render={({ field }) => <Input {...field} value={field.value ?? ""} />}
                    />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label="PIN / ZIP">
                    <Controller
                      name={`addresses.${index}.pin`}
                      control={control}
                      render={({ field }) => <Input {...field} value={field.value ?? ""} />}
                    />
                  </Form.Item>
                </Col>
                <Col span={10}>
                  <Form.Item
                    label="Country"
                    required
                    validateStatus={errors.addresses?.[index]?.country ? "error" : ""}
                    help={errors.addresses?.[index]?.country?.message}
                  >
                    <Controller
                      name={`addresses.${index}.country`}
                      control={control}
                      render={({ field }) => (
                        <Select
                          showSearch
                          placeholder="Select country"
                          optionFilterProp="label"
                          {...field}
                          options={countries.map((c) => ({
                            value: c.id,
                            label: `${c.name} (${c.iso2})`,
                          }))}
                        />
                      )}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Email"
                    required
                    validateStatus={errors.addresses?.[index]?.email ? "error" : ""}
                    help={errors.addresses?.[index]?.email?.message}
                  >
                    <Controller
                      name={`addresses.${index}.email`}
                      control={control}
                      render={({ field }) => <Input {...field} type="email" />}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Contact Name"
                    required
                    validateStatus={errors.addresses?.[index]?.contact_name ? "error" : ""}
                    help={errors.addresses?.[index]?.contact_name?.message}
                  >
                    <Controller
                      name={`addresses.${index}.contact_name`}
                      control={control}
                      render={({ field }) => <Input {...field} />}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="Phone Dial Code (optional)" tooltip="e.g. +91">
                    <Controller
                      name={`addresses.${index}.phone_country_code`}
                      control={control}
                      render={({ field }) => (
                        <Input {...field} value={field.value ?? ""} placeholder="+91" maxLength={5} />
                      )}
                    />
                  </Form.Item>
                </Col>
                <Col span={16}>
                  <Form.Item label="Phone Number (optional)">
                    <Controller
                      name={`addresses.${index}.phone_number`}
                      control={control}
                      render={({ field }) => (
                        <Input {...field} value={field.value ?? ""} placeholder="9876543210" />
                      )}
                    />
                  </Form.Item>
                </Col>
              </Row>
            </div>
          ))}

          <Button
            type="dashed"
            icon={<PlusOutlined />}
            onClick={() =>
              addAddress({
                address_type: "OFFICE",
                line1: "",
                line2: "",
                city: "",
                state: "",
                pin: "",
                country: undefined as unknown as number,
                email: "",
                contact_name: "",
                phone_country_code: "",
                phone_number: "",
              })
            }
            style={{ marginTop: 8 }}
          >
            Add Another Address
          </Button>
        </Card>

        {/* ── Section 2: Tax Codes ───────────────────────────────────────── */}
        <Card title="Tax Codes (optional)" style={{ marginBottom: 16 }}>
          {taxCodeFields.map((field, index) => (
            <Row key={field.id} gutter={16} align="middle">
              <Col span={10}>
                <Form.Item
                  label={index === 0 ? "Tax Type" : undefined}
                  validateStatus={errors.tax_codes?.[index]?.tax_type ? "error" : ""}
                  help={errors.tax_codes?.[index]?.tax_type?.message}
                >
                  <Controller
                    name={`tax_codes.${index}.tax_type`}
                    control={control}
                    render={({ field }) => (
                      <Input {...field} placeholder="e.g. GSTIN, PAN, VAT" />
                    )}
                  />
                </Form.Item>
              </Col>
              <Col span={10}>
                <Form.Item
                  label={index === 0 ? "Tax Code" : undefined}
                  validateStatus={errors.tax_codes?.[index]?.tax_code ? "error" : ""}
                  help={errors.tax_codes?.[index]?.tax_code?.message}
                >
                  <Controller
                    name={`tax_codes.${index}.tax_code`}
                    control={control}
                    render={({ field }) => <Input {...field} />}
                  />
                </Form.Item>
              </Col>
              <Col span={4}>
                <Button
                  danger
                  type="text"
                  icon={<MinusCircleOutlined />}
                  onClick={() => removeTaxCode(index)}
                  style={{ marginTop: index === 0 ? 4 : 0 }}
                />
              </Col>
            </Row>
          ))}
          <Button
            type="dashed"
            icon={<PlusOutlined />}
            onClick={() => addTaxCode({ tax_type: "", tax_code: "" })}
          >
            Add Tax Code
          </Button>
        </Card>

        {/* ── Form actions ───────────────────────────────────────────────── */}
        <Space>
          <Button
            type="primary"
            htmlType="submit"
            loading={isSubmitting || createMutation.isPending || updateMutation.isPending}
          >
            {isEditMode ? "Save Changes" : "Create Organisation"}
          </Button>
          <Button onClick={() => navigate("/master-data/organisations")}>
            Cancel
          </Button>
        </Space>
      </form>
    </div>
  );
}
