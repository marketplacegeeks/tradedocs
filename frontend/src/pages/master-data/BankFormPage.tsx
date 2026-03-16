// Bank create / edit form.
// When opened at /master-data/banks/new → creates a new bank account.
// When opened at /master-data/banks/:id/edit → loads and edits an existing one.

import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Button, Card, Col, Form, Input, Row, Select, Typography, message, Spin,
} from "antd";

import { createBank, getBank, updateBank } from "../../api/banks";
import { listCountries } from "../../api/countries";
import { listCurrencies } from "../../api/currencies";
import { ACCOUNT_TYPES, ACCOUNT_TYPE_LABELS } from "../../utils/constants";
import type { AccountType } from "../../utils/constants";

const { Title } = Typography;

// ---- Zod schema -----------------------------------------------------------
// Mirrors FR-05 and Section 13.1.2 validation rules.

const bankSchema = z.object({
  nickname: z.string().min(1, "Nickname is required").max(255),
  beneficiary_name: z.string().min(1, "Beneficiary name is required").max(255),
  bank_name: z.string().min(1, "Bank name is required").max(255),
  bank_country: z.number({ required_error: "Bank country is required" }),
  branch_name: z.string().min(1, "Branch name is required").max(255),
  branch_address: z.string().optional().default(""),
  account_number: z.string().min(1, "Account number is required").max(50),
  account_type: z.enum(["CURRENT", "SAVINGS", "CHECKING"], {
    required_error: "Account type is required",
  }),
  currency: z.number({ required_error: "Currency is required" }),
  // SWIFT is optional but must be 8 or 11 uppercase alphanumeric chars if provided.
  swift_code: z
    .string()
    .optional()
    .refine(
      (val) => !val || /^[A-Z0-9]{8}$|^[A-Z0-9]{11}$/.test(val),
      { message: "SWIFT code must be 8 or 11 uppercase letters/digits (ISO 9362)" }
    )
    .default(""),
  // IBAN is optional but must match ISO 7064 format if provided.
  iban: z
    .string()
    .optional()
    .refine(
      (val) => !val || /^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$/.test(val),
      { message: "IBAN must start with 2-letter country code, 2 check digits, then up to 30 alphanumeric chars" }
    )
    .default(""),
  routing_number: z.string().optional().default(""),
});

type BankFormValues = z.infer<typeof bankSchema>;

// ---- Component ------------------------------------------------------------

export default function BankFormPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const isEditing = Boolean(id);

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<BankFormValues>({
    resolver: zodResolver(bankSchema),
    defaultValues: {
      nickname: "",
      beneficiary_name: "",
      bank_name: "",
      branch_name: "",
      branch_address: "",
      account_number: "",
      account_type: undefined,
      swift_code: "",
      iban: "",
      routing_number: "",
    },
  });

  // Load countries for the bank country dropdown.
  const { data: countries = [] } = useQuery({
    queryKey: ["countries"],
    queryFn: listCountries,
  });

  // Load currencies for the currency dropdown.
  const { data: currencies = [] } = useQuery({
    queryKey: ["currencies"],
    queryFn: listCurrencies,
  });

  // When editing, fetch the existing bank and populate the form.
  const { data: existingBank, isLoading: loadingBank } = useQuery({
    queryKey: ["banks", Number(id)],
    queryFn: () => getBank(Number(id)),
    enabled: isEditing,
  });

  useEffect(() => {
    if (existingBank) {
      reset({
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
      });
    }
  }, [existingBank, reset]);

  const saveMutation = useMutation({
    mutationFn: (values: BankFormValues) =>
      isEditing
        ? updateBank(Number(id), values)
        : createBank(values),
    onSuccess: () => {
      message.success(isEditing ? "Bank account updated." : "Bank account created.");
      // Invalidate the list so it refreshes when the user navigates back.
      queryClient.invalidateQueries({ queryKey: ["banks"] });
      navigate("/master-data/banks");
    },
    onError: () => {
      message.error("Failed to save bank account. Check the form for errors.");
    },
  });

  if (isEditing && loadingBank) {
    return <Spin style={{ display: "block", margin: "80px auto" }} />;
  }

  const countryOptions = countries.map((c) => ({
    value: c.id,
    label: `${c.name} (${c.iso2})`,
  }));

  const currencyOptions = currencies.map((c) => ({
    value: c.id,
    label: `${c.code} – ${c.name}`,
  }));

  const accountTypeOptions = Object.entries(ACCOUNT_TYPE_LABELS).map(
    ([value, label]) => ({ value: value as AccountType, label })
  );

  return (
    <div style={{ padding: 24 }}>
      <Title level={3} style={{ marginBottom: 24 }}>
        {isEditing ? "Edit Bank Account" : "New Bank Account"}
      </Title>

      <Form layout="vertical" onFinish={handleSubmit((v) => saveMutation.mutate(v))}>
        <Card title="Account Details" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Nickname"
                required
                validateStatus={errors.nickname ? "error" : ""}
                help={errors.nickname?.message}
              >
                <Controller
                  name="nickname"
                  control={control}
                  render={({ field }) => (
                    <Input {...field} placeholder="e.g. USD Operating Account" />
                  )}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Beneficiary Name"
                required
                validateStatus={errors.beneficiary_name ? "error" : ""}
                help={errors.beneficiary_name?.message}
              >
                <Controller
                  name="beneficiary_name"
                  control={control}
                  render={({ field }) => (
                    <Input {...field} placeholder="Name as on wire instructions" />
                  )}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Bank Name"
                required
                validateStatus={errors.bank_name ? "error" : ""}
                help={errors.bank_name?.message}
              >
                <Controller
                  name="bank_name"
                  control={control}
                  render={({ field }) => <Input {...field} placeholder="e.g. HDFC Bank" />}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Bank Country"
                required
                validateStatus={errors.bank_country ? "error" : ""}
                help={errors.bank_country?.message}
              >
                <Controller
                  name="bank_country"
                  control={control}
                  render={({ field }) => (
                    <Select
                      {...field}
                      showSearch
                      optionFilterProp="label"
                      options={countryOptions}
                      placeholder="Select country"
                    />
                  )}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Branch Name"
                required
                validateStatus={errors.branch_name ? "error" : ""}
                help={errors.branch_name?.message}
              >
                <Controller
                  name="branch_name"
                  control={control}
                  render={({ field }) => <Input {...field} placeholder="e.g. Fort Branch" />}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Branch Address"
                validateStatus={errors.branch_address ? "error" : ""}
                help={errors.branch_address?.message}
              >
                <Controller
                  name="branch_address"
                  control={control}
                  render={({ field }) => <Input.TextArea {...field} rows={2} />}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Account Number"
                required
                validateStatus={errors.account_number ? "error" : ""}
                help={errors.account_number?.message}
              >
                <Controller
                  name="account_number"
                  control={control}
                  render={({ field }) => <Input {...field} />}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Account Type"
                required
                validateStatus={errors.account_type ? "error" : ""}
                help={errors.account_type?.message}
              >
                <Controller
                  name="account_type"
                  control={control}
                  render={({ field }) => (
                    <Select {...field} options={accountTypeOptions} placeholder="Select type" />
                  )}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Currency"
                required
                validateStatus={errors.currency ? "error" : ""}
                help={errors.currency?.message}
              >
                <Controller
                  name="currency"
                  control={control}
                  render={({ field }) => (
                    <Select
                      {...field}
                      showSearch
                      optionFilterProp="label"
                      options={currencyOptions}
                      placeholder="Select currency"
                    />
                  )}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card title="Routing & Identification Codes" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="SWIFT / BIC Code"
                validateStatus={errors.swift_code ? "error" : ""}
                help={errors.swift_code?.message ?? "Optional. 8 or 11 characters (ISO 9362)."}
              >
                <Controller
                  name="swift_code"
                  control={control}
                  render={({ field }) => (
                    <Input {...field} placeholder="e.g. HDFCINBB" maxLength={11} />
                  )}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="IBAN"
                validateStatus={errors.iban ? "error" : ""}
                help={errors.iban?.message ?? "Optional. Required for European/Middle-East transfers."}
              >
                <Controller
                  name="iban"
                  control={control}
                  render={({ field }) => (
                    <Input {...field} placeholder="e.g. GB29NWBK60161331926819" maxLength={34} />
                  )}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="IFSC / Routing / Sort Code"
                validateStatus={errors.routing_number ? "error" : ""}
                help={errors.routing_number?.message ?? "Optional. India: IFSC, USA: ACH routing, UK: sort code."}
              >
                <Controller
                  name="routing_number"
                  control={control}
                  render={({ field }) => <Input {...field} />}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={saveMutation.isPending}
            style={{ marginRight: 8 }}
          >
            {isEditing ? "Save Changes" : "Create Bank Account"}
          </Button>
          <Button onClick={() => navigate("/master-data/banks")}>Cancel</Button>
        </Form.Item>
      </Form>
    </div>
  );
}
