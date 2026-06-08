// COA create / edit form.
// When :id is in the URL we are in edit mode; without :id we are creating.

import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Select, message, Modal } from "antd";
import { Plus, Trash2 } from "lucide-react";

import {
  getCOA,
  createCOA,
  updateCOA,
  submitCOA,
  listProducts,
  listTestParameters,
  listTestMethods,
  getProductGradeTemplate,
} from "../../api/coa";
import type { COAParameter, COAPayload } from "../../api/coa";
import { listOrganisations } from "../../api/organisations";
import { listPackingLists, getPackingList } from "../../api/packingLists";
import { listUOMs, listTypeOfPackages } from "../../api/referenceData";
import { extractApiError } from "../../utils/apiErrors";
import { SPEC_TYPES } from "../../utils/constants";

// ---- Shared field label helper ---------------------------------------------

function FieldLabel({ text, required }: { text: string; required?: boolean }) {
  return (
    <div
      style={{
        fontFamily: "var(--font-body)",
        fontSize: 13,
        fontWeight: 500,
        color: "var(--text-secondary)",
        marginBottom: 4,
      }}
    >
      {text}
      {required && <span style={{ color: "var(--pastel-pink-text)", marginLeft: 2 }}>*</span>}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "8px 12px",
  borderRadius: 8,
  border: "1px solid var(--border-medium)",
  fontFamily: "var(--font-body)",
  fontSize: 14,
  color: "var(--text-primary)",
  background: "var(--bg-surface)",
  boxSizing: "border-box",
  outline: "none",
};

// ---- A blank parameter row -------------------------------------------------

function blankRow(sNo: number): COAParameter {
  return {
    s_no: sNo,
    parameter: null,
    unit: null,
    spec_type: SPEC_TYPES.QUANTITATIVE,
    spec_min: "",
    spec_max: "",
    spec_description: "",
    result_value: "",
    result_text: "",
    test_method: null,
  };
}

// ---- Main page -------------------------------------------------------------

export default function COAFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  // ---- Header form state --------------------------------------------------
  const [packingListId, setPackingListId] = useState<number | null>(null);
  const [productId, setProductId] = useState<number | null>(null);
  const [productGradeId, setProductGradeId] = useState<number | null>(null);
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [footerOrgId, setFooterOrgId] = useState<number | null>(null);
  const [batchNumber, setBatchNumber] = useState("");
  const [packageCount, setPackageCount] = useState("");
  const [packageVolume, setPackageVolume] = useState("");
  const [packageUomId, setPackageUomId] = useState<number | null>(null);
  const [packageTypeId, setPackageTypeId] = useState<number | null>(null);
  const [dateOfManufacture, setDateOfManufacture] = useState("");
  const [dateOfRetest, setDateOfRetest] = useState("");
  const [dateOfDespatch, setDateOfDespatch] = useState("");
  const [dateTimeOfSampling, setDateTimeOfSampling] = useState("");
  const [dateTimeOfAnalysis, setDateTimeOfAnalysis] = useState("");
  const [analystName, setAnalystName] = useState("");
  const [qcInchargeName, setQcInchargeName] = useState("");

  // ---- Test parameters table state ----------------------------------------
  const [rows, setRows] = useState<COAParameter[]>([blankRow(1)]);

  // ---- Template load state ------------------------------------------------
  const [templateBanner, setTemplateBanner] = useState<string | null>(null);
  const [confirmGradeChange, setConfirmGradeChange] = useState<{
    newProductId: number | null;
    newGradeId: number | null;
  } | null>(null);

  // ---- Submission state ---------------------------------------------------
  const [saving, setSaving] = useState(false);

  // ---- Master data queries ------------------------------------------------

  const { data: products = [] } = useQuery({
    queryKey: ["products"],
    queryFn: () => listProducts().then((r) => r.data),
  });

  const { data: testParameters = [] } = useQuery({
    queryKey: ["test-parameters"],
    queryFn: () => listTestParameters().then((r) => r.data),
  });

  const { data: testMethods = [] } = useQuery({
    queryKey: ["test-methods"],
    queryFn: () => listTestMethods().then((r) => r.data),
  });

  // Load all organisations — filter client-side for customer (CONSIGNEE/BUYER)
  // and footer org (EXPORTER/CONSIGNEE)
  const { data: allOrgs = [] } = useQuery({
    queryKey: ["organisations"],
    queryFn: () => listOrganisations(),
  });

  const { data: uoms = [] } = useQuery({
    queryKey: ["uoms"],
    queryFn: listUOMs,
  });

  const { data: packageTypes = [] } = useQuery({
    queryKey: ["type-of-packages"],
    queryFn: listTypeOfPackages,
  });

  // Fetch only approved packing lists for the PL dropdown
  const { data: approvedPLs = [] } = useQuery({
    queryKey: ["packing-lists", "APPROVED"],
    queryFn: () => listPackingLists({ status: "APPROVED" }),
  });

  // When a PL is selected, auto-fill customer from buyer (or consignee as fallback)
  async function handlePackingListChange(plId: number | null) {
    setPackingListId(plId);
    if (!plId) return;
    try {
      const pl = await getPackingList(plId);
      const customerOrgId = pl.buyer ?? pl.consignee;
      if (customerOrgId) setCustomerId(customerOrgId);
    } catch {
      // Non-blocking — user can still set customer manually
    }
  }

  // ---- Edit mode: load existing COA data -----------------------------------

  const { data: existingCOA } = useQuery({
    queryKey: ["coa", id],
    queryFn: () => getCOA(Number(id)).then((r) => r.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (!existingCOA) return;
    // Find product from product_grade
    const product = products.find((p) =>
      p.grades.some((g) => g.id === existingCOA.product_grade)
    );
    if (product) {
      setProductId(product.id);
    }
    setPackingListId(existingCOA.packing_list ?? null);
    setProductGradeId(existingCOA.product_grade);
    setCustomerId(existingCOA.customer);
    setFooterOrgId(existingCOA.footer_organisation);
    setBatchNumber(existingCOA.batch_number);
    setPackageCount(String(existingCOA.package_count));
    setPackageVolume(existingCOA.package_volume);
    setPackageUomId(existingCOA.package_uom);
    setPackageTypeId(existingCOA.package_type);
    setDateOfManufacture(existingCOA.date_of_manufacture);
    setDateOfRetest(existingCOA.date_of_retest);
    setDateOfDespatch(existingCOA.date_of_despatch ?? "");
    // datetime-local inputs need "YYYY-MM-DDTHH:MM" format — strip seconds if present
    setDateTimeOfSampling(existingCOA.date_time_of_sampling?.slice(0, 16) ?? "");
    setDateTimeOfAnalysis(existingCOA.date_time_of_analysis?.slice(0, 16) ?? "");
    setAnalystName(existingCOA.analyst_name);
    setQcInchargeName(existingCOA.qc_incharge_name);
    if (existingCOA.parameters.length > 0) {
      setRows(existingCOA.parameters);
    }
  }, [existingCOA, products]);

  // ---- Auto-suggest retest date = manufacture + 1 year --------------------

  function handleManufactureDateChange(val: string) {
    setDateOfManufacture(val);
    if (val && !dateOfRetest) {
      const d = new Date(val);
      d.setFullYear(d.getFullYear() + 1);
      setDateOfRetest(d.toISOString().split("T")[0]);
    }
  }

  // ---- Grade options from selected product ---------------------------------

  const selectedProduct = products.find((p) => p.id === productId) ?? null;
  const gradeOptions = (selectedProduct?.grades ?? []).filter((g) => g.is_active);

  // ---- Template loading ---------------------------------------------------

  async function loadTemplate(gradeId: number) {
    try {
      const res = await getProductGradeTemplate(gradeId);
      const templateRows: COAParameter[] = res.data?.rows ?? [];
      if (templateRows.length > 0) {
        setRows(templateRows.map((r, i) => ({ ...r, s_no: i + 1 })));
        const grade = gradeOptions.find((g) => g.id === gradeId);
        const productName = selectedProduct?.name ?? "";
        setTemplateBanner(
          `${templateRows.length} test parameter${templateRows.length !== 1 ? "s" : ""} loaded from ${productName} — ${grade?.grade ?? ""} template. You can edit, add, or remove rows.`
        );
      } else {
        setTemplateBanner(null);
      }
    } catch {
      // Template not found is fine — just start with a blank row
      setTemplateBanner(null);
    }
  }

  function handleProductChange(newProductId: number | null) {
    const hasUserRows = rows.some((r) => r.parameter !== null);
    if (hasUserRows && newProductId !== productId) {
      setConfirmGradeChange({ newProductId, newGradeId: null });
    } else {
      applyProductChange(newProductId, null);
    }
  }

  function handleGradeChange(newGradeId: number | null) {
    const hasUserRows = rows.some((r) => r.parameter !== null);
    if (hasUserRows && newGradeId !== productGradeId) {
      setConfirmGradeChange({ newProductId: productId, newGradeId });
    } else {
      applyGradeChange(newGradeId);
    }
  }

  function applyProductChange(newProductId: number | null, newGradeId: number | null) {
    setProductId(newProductId);
    setProductGradeId(null);
    setRows([blankRow(1)]);
    setTemplateBanner(null);
    // If a grade was pre-specified (from confirm dialog) apply it
    if (newGradeId) {
      setProductGradeId(newGradeId);
      loadTemplate(newGradeId);
    }
  }

  function applyGradeChange(newGradeId: number | null) {
    setProductGradeId(newGradeId);
    setRows([blankRow(1)]);
    setTemplateBanner(null);
    if (newGradeId) {
      loadTemplate(newGradeId);
    }
  }

  function confirmGradeChangeAndProceed() {
    if (!confirmGradeChange) return;
    const { newProductId, newGradeId } = confirmGradeChange;
    setConfirmGradeChange(null);
    if (newProductId !== productId) {
      applyProductChange(newProductId, newGradeId);
    } else {
      applyGradeChange(newGradeId);
    }
  }

  // ---- Row operations -----------------------------------------------------

  function updateRow(index: number, patch: Partial<COAParameter>) {
    setRows((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...patch };
      return next;
    });
  }

  function addRow() {
    setRows((prev) => [...prev, blankRow(prev.length + 1)]);
  }

  function removeRow(index: number) {
    if (rows.length <= 1) return;
    setRows((prev) => prev.filter((_, i) => i !== index).map((r, i) => ({ ...r, s_no: i + 1 })));
  }

  // When a test parameter FK is selected, auto-fill label, default unit, and default test method
  function handleParameterSelect(index: number, paramId: number | null) {
    if (!paramId) {
      updateRow(index, { parameter: null, parameter_name: null });
      return;
    }
    const param = testParameters.find((p) => p.id === paramId);
    if (!param) return;
    const patch: Partial<COAParameter> = {
      parameter: paramId,
      parameter_name: param.name,
    };
    if (param.default_unit) {
      patch.unit = param.default_unit;
    }
    if (param.default_test_method) {
      patch.test_method = param.default_test_method;
      patch.test_method_code = param.default_test_method_code ?? null;
    }
    updateRow(index, patch);
  }

  // ---- Build payload -------------------------------------------------------

  function buildPayload(): COAPayload | null {
    if (!productGradeId || !customerId || !footerOrgId || !packageUomId || !packageTypeId) {
      message.error("Please fill in all required fields.");
      return null;
    }
    if (!batchNumber.trim()) {
      message.error("Batch number is required.");
      return null;
    }
    if (!dateOfManufacture || !dateOfRetest || !dateTimeOfSampling || !dateTimeOfAnalysis) {
      message.error("Please fill in all date fields.");
      return null;
    }
    const invalidRow = rows.find((r) => !r.parameter);
    if (invalidRow) {
      message.error("Every test parameter row must have a parameter selected.");
      return null;
    }

    return {
      packing_list: packingListId,
      product_grade: productGradeId,
      customer: customerId,
      footer_organisation: footerOrgId,
      batch_number: batchNumber,
      package_count: Number(packageCount),
      package_volume: packageVolume,
      package_uom: packageUomId,
      package_type: packageTypeId,
      date_of_manufacture: dateOfManufacture,
      date_of_retest: dateOfRetest,
      date_of_despatch: dateOfDespatch || null,
      date_time_of_sampling: dateTimeOfSampling,
      date_time_of_analysis: dateTimeOfAnalysis,
      analyst_name: analystName,
      qc_incharge_name: qcInchargeName,
      parameters: rows,
    };
  }

  // ---- Submit handlers ----------------------------------------------------

  async function handleSaveDraft() {
    const payload = buildPayload();
    if (!payload) return;
    setSaving(true);
    try {
      let savedId: number;
      if (isEdit && id) {
        const res = await updateCOA(Number(id), payload);
        savedId = res.data.id;
      } else {
        const res = await createCOA(payload);
        savedId = res.data.id;
      }
      message.success("COA saved as draft.");
      navigate(`/coas/${savedId}`);
    } catch (err) {
      message.error(extractApiError(err, "Failed to save COA."));
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmit() {
    const payload = buildPayload();
    if (!payload) return;
    setSaving(true);
    try {
      let savedId: number;
      if (isEdit && id) {
        const res = await updateCOA(Number(id), payload);
        savedId = res.data.id;
      } else {
        const res = await createCOA(payload);
        savedId = res.data.id;
      }
      await submitCOA(savedId);
      message.success("COA submitted for approval.");
      navigate(`/coas/${savedId}`);
    } catch (err) {
      message.error(extractApiError(err, "Failed to submit COA."));
    } finally {
      setSaving(false);
    }
  }

  // ---- Dropdown options ---------------------------------------------------

  const customerOptions = allOrgs
    .filter((o) => (o.tags as unknown as Array<{ tag: string }>).some((t) => t.tag === "CONSIGNEE" || t.tag === "BUYER"))
    .map((o) => ({ value: o.id, label: o.name }));

  const footerOrgOptions = allOrgs
    .filter((o) => (o.tags as unknown as Array<{ tag: string }>).some((t) => t.tag === "EXPORTER" || t.tag === "CONSIGNEE"))
    .map((o) => ({ value: o.id, label: o.name }));

  const productOptions = products
    .filter((p) => p.is_active)
    .map((p) => ({ value: p.id, label: p.name }));

  const gradeSelectOptions = gradeOptions.map((g) => ({ value: g.id, label: g.grade }));

  const uomOptions = uoms
    .filter((u) => u.is_active)
    .map((u) => ({ value: u.id, label: `${u.name} (${u.abbreviation})` }));

  const packageTypeOptions = packageTypes
    .filter((pt) => pt.is_active)
    .map((pt) => ({ value: pt.id, label: pt.name }));

  const testParamOptions = testParameters
    .filter((p) => p.is_active)
    .map((p) => ({ value: p.id, label: p.name }));

  const testMethodOptions = testMethods
    .filter((m) => m.is_active)
    .map((m) => ({ value: m.id, label: `${m.code} — ${m.description}` }));

  // ---- Render ------------------------------------------------------------

  return (
    <div>
      {/* Page title */}
      <div style={{ marginBottom: 24 }}>
        <h1
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: 22,
            fontWeight: 700,
            color: "var(--text-primary)",
            marginBottom: 4,
          }}
        >
          {isEdit ? "Edit Certificate of Analysis" : "New Certificate of Analysis"}
        </h1>
        <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
          {isEdit ? "Update the COA details below." : "Fill in the details to create a new COA."}
        </p>
      </div>

      {/* Header section card */}
      <div
        style={{
          background: "var(--bg-surface)",
          borderRadius: 14,
          border: "1px solid var(--border-light)",
          boxShadow: "var(--shadow-card)",
          padding: 24,
          marginBottom: 20,
        }}
      >
        <h2
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: 15,
            fontWeight: 600,
            color: "var(--text-primary)",
            marginBottom: 20,
          }}
        >
          Product &amp; Customer Details
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {/* Packing List — full-width row */}
          <div style={{ gridColumn: "1 / -1" }}>
            <FieldLabel text="Packing List (optional)" />
            <Select
              value={packingListId ?? undefined}
              onChange={handlePackingListChange}
              allowClear
              showSearch
              filterOption={(input, opt) =>
                (opt?.label ?? "").toLowerCase().includes(input.toLowerCase())
              }
              placeholder="Select an approved packing list"
              style={{ width: "100%" }}
              options={approvedPLs.map((pl) => ({
                value: pl.id,
                label: pl.ci_number
                  ? `${pl.pl_number} / CI: ${pl.ci_number}`
                  : pl.pl_number,
              }))}
            />
          </div>

          {/* Product */}
          <div>
            <FieldLabel text="Product" required />
            <Select
              value={productId ?? undefined}
              onChange={handleProductChange}
              showSearch
              filterOption={(input, opt) =>
                (opt?.label ?? "").toLowerCase().includes(input.toLowerCase())
              }
              placeholder="Select product"
              style={{ width: "100%" }}
              options={productOptions}
            />
          </div>

          {/* Grade */}
          <div>
            <FieldLabel text="Grade" required />
            <Select
              value={productGradeId ?? undefined}
              onChange={handleGradeChange}
              disabled={!productId}
              placeholder={productId ? "Select grade" : "Select product first"}
              style={{ width: "100%" }}
              options={gradeSelectOptions}
            />
          </div>

          {/* Customer */}
          <div>
            <FieldLabel text="Customer" required />
            <Select
              value={customerId ?? undefined}
              onChange={(v) => setCustomerId(v)}
              showSearch
              filterOption={(input, opt) =>
                (opt?.label ?? "").toLowerCase().includes(input.toLowerCase())
              }
              placeholder="Select customer"
              style={{ width: "100%" }}
              options={customerOptions}
            />
          </div>

          {/* Footer Organisation */}
          <div>
            <FieldLabel text="Footer Company" required />
            <Select
              value={footerOrgId ?? undefined}
              onChange={(v) => setFooterOrgId(v)}
              showSearch
              filterOption={(input, opt) =>
                (opt?.label ?? "").toLowerCase().includes(input.toLowerCase())
              }
              placeholder="Select footer company"
              style={{ width: "100%" }}
              options={footerOrgOptions}
            />
          </div>

          {/* Batch Number */}
          <div>
            <FieldLabel text="Batch Number" required />
            <input
              type="text"
              value={batchNumber}
              onChange={(e) => setBatchNumber(e.target.value)}
              placeholder="e.g. BCH-2026-001"
              style={inputStyle}
            />
          </div>

          {/* Package Count */}
          <div>
            <FieldLabel text="Package Count" required />
            <input
              type="number"
              min={1}
              step={1}
              value={packageCount}
              onChange={(e) => setPackageCount(e.target.value)}
              placeholder="e.g. 20"
              style={inputStyle}
            />
          </div>

          {/* Package Volume */}
          <div>
            <FieldLabel text="Package Volume" required />
            <input
              type="number"
              step="0.001"
              value={packageVolume}
              onChange={(e) => setPackageVolume(e.target.value)}
              placeholder="e.g. 50.000"
              style={inputStyle}
            />
          </div>

          {/* Package UOM */}
          <div>
            <FieldLabel text="Package UOM" required />
            <Select
              value={packageUomId ?? undefined}
              onChange={(v) => setPackageUomId(v)}
              placeholder="Select unit"
              style={{ width: "100%" }}
              options={uomOptions}
            />
          </div>

          {/* Package Type */}
          <div>
            <FieldLabel text="Package Type" required />
            <Select
              value={packageTypeId ?? undefined}
              onChange={(v) => setPackageTypeId(v)}
              placeholder="Select package type"
              style={{ width: "100%" }}
              options={packageTypeOptions}
            />
          </div>

          {/* Date of Despatch */}
          <div>
            <FieldLabel text="Date of Despatch (optional)" />
            <input
              type="date"
              value={dateOfDespatch}
              onChange={(e) => setDateOfDespatch(e.target.value)}
              style={inputStyle}
            />
          </div>

          {/* Date of Manufacture */}
          <div>
            <FieldLabel text="Date of Manufacture" required />
            <input
              type="date"
              value={dateOfManufacture}
              onChange={(e) => handleManufactureDateChange(e.target.value)}
              style={inputStyle}
            />
          </div>

          {/* Date of Retest */}
          <div>
            <FieldLabel text="Date of Retest" required />
            <input
              type="date"
              value={dateOfRetest}
              onChange={(e) => setDateOfRetest(e.target.value)}
              style={inputStyle}
            />
          </div>

          {/* Date & Time of Sampling */}
          <div>
            <FieldLabel text="Date & Time of Sampling" required />
            <input
              type="datetime-local"
              value={dateTimeOfSampling}
              onChange={(e) => setDateTimeOfSampling(e.target.value)}
              style={inputStyle}
            />
          </div>

          {/* Date & Time of Analysis */}
          <div>
            <FieldLabel text="Date & Time of Analysis" required />
            <input
              type="datetime-local"
              value={dateTimeOfAnalysis}
              onChange={(e) => setDateTimeOfAnalysis(e.target.value)}
              style={inputStyle}
            />
          </div>

          {/* Analyst Name */}
          <div>
            <FieldLabel text="Analyst Name" required />
            <input
              type="text"
              value={analystName}
              onChange={(e) => setAnalystName(e.target.value)}
              placeholder="Full name"
              style={inputStyle}
            />
          </div>

          {/* QC Incharge Name */}
          <div>
            <FieldLabel text="QC Incharge Name" required />
            <input
              type="text"
              value={qcInchargeName}
              onChange={(e) => setQcInchargeName(e.target.value)}
              placeholder="Full name"
              style={inputStyle}
            />
          </div>
        </div>
      </div>

      {/* Test parameters card */}
      <div
        style={{
          background: "var(--bg-surface)",
          borderRadius: 14,
          border: "1px solid var(--border-light)",
          boxShadow: "var(--shadow-card)",
          padding: 24,
          marginBottom: 20,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 16,
          }}
        >
          <h2
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: 15,
              fontWeight: 600,
              color: "var(--text-primary)",
              margin: 0,
            }}
          >
            Test Parameters
          </h2>
          <button
            onClick={addRow}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              padding: "7px 14px",
              background: "var(--primary)",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontFamily: "var(--font-body)",
              fontSize: 13,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            <Plus size={14} strokeWidth={2} />
            Add Row
          </button>
        </div>

        {/* Template banner */}
        {templateBanner && (
          <div
            style={{
              background: "var(--pastel-blue)",
              color: "var(--pastel-blue-text)",
              borderRadius: 8,
              padding: "10px 14px",
              fontFamily: "var(--font-body)",
              fontSize: 13,
              marginBottom: 16,
            }}
          >
            {templateBanner}
          </div>
        )}

        {/* Table */}
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 900 }}>
            <thead>
              <tr style={{ background: "var(--bg-base)" }}>
                {[
                  "S.No",
                  "Characteristic",
                  "Unit",
                  "Spec Type",
                  "Spec (Min / Max / Description)",
                  "Result",
                  "Test Method",
                  "",
                ].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "10px 12px",
                      textAlign: "left",
                      fontFamily: "var(--font-body)",
                      fontSize: 11,
                      fontWeight: 600,
                      color: "var(--text-muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                      borderBottom: "1px solid var(--border-light)",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <ParameterRow
                  key={idx}
                  row={row}
                  index={idx}
                  canDelete={rows.length > 1}
                  testParamOptions={testParamOptions}
                  uomOptions={uomOptions}
                  testMethodOptions={testMethodOptions}
                  onParameterSelect={(paramId) => handleParameterSelect(idx, paramId)}
                  onUpdate={(patch) => updateRow(idx, patch)}
                  onDelete={() => removeRow(idx)}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action buttons */}
      <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
        <button
          onClick={() => navigate(-1)}
          disabled={saving}
          style={{
            padding: "9px 20px",
            background: "transparent",
            border: "1px solid var(--border-medium)",
            borderRadius: 8,
            fontFamily: "var(--font-body)",
            fontSize: 14,
            color: "var(--text-secondary)",
            cursor: saving ? "not-allowed" : "pointer",
            opacity: saving ? 0.6 : 1,
          }}
        >
          Cancel
        </button>
        <button
          onClick={handleSaveDraft}
          disabled={saving}
          style={{
            padding: "9px 20px",
            background: "var(--bg-hover)",
            border: "1px solid var(--border-medium)",
            borderRadius: 8,
            fontFamily: "var(--font-body)",
            fontSize: 14,
            fontWeight: 500,
            color: "var(--text-primary)",
            cursor: saving ? "not-allowed" : "pointer",
            opacity: saving ? 0.6 : 1,
          }}
        >
          {saving ? "Saving…" : "Save as Draft"}
        </button>
        <button
          onClick={handleSubmit}
          disabled={saving}
          style={{
            padding: "9px 20px",
            background: "var(--primary)",
            border: "none",
            borderRadius: 8,
            fontFamily: "var(--font-body)",
            fontSize: 14,
            fontWeight: 500,
            color: "#fff",
            cursor: saving ? "not-allowed" : "pointer",
            opacity: saving ? 0.6 : 1,
          }}
        >
          {saving ? "Submitting…" : "Submit for Approval"}
        </button>
      </div>

      {/* Grade-change confirmation dialog */}
      <Modal
        title="Replace test parameters?"
        open={confirmGradeChange !== null}
        onOk={confirmGradeChangeAndProceed}
        onCancel={() => setConfirmGradeChange(null)}
        okText="Yes, replace rows"
        okButtonProps={{ danger: true }}
        cancelText="Keep current rows"
      >
        <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-secondary)" }}>
          You have already added test parameter rows. Changing the product or grade will replace
          them with the template for the new selection (if one exists). Do you want to continue?
        </p>
      </Modal>
    </div>
  );
}

// ---- Parameter table row ---------------------------------------------------

interface RowProps {
  row: COAParameter;
  index: number;
  canDelete: boolean;
  testParamOptions: { value: number; label: string }[];
  uomOptions: { value: number; label: string }[];
  testMethodOptions: { value: number; label: string }[];
  onParameterSelect: (paramId: number | null) => void;
  onUpdate: (patch: Partial<COAParameter>) => void;
  onDelete: () => void;
}

function ParameterRow({
  row,
  canDelete,
  testParamOptions,
  uomOptions,
  testMethodOptions,
  onParameterSelect,
  onUpdate,
  onDelete,
}: RowProps) {
  const isQuantitative = row.spec_type === SPEC_TYPES.QUANTITATIVE;

  const cellStyle: React.CSSProperties = {
    padding: "8px 10px",
    borderBottom: "1px solid var(--border-light)",
    verticalAlign: "top",
  };

  const smallInput: React.CSSProperties = {
    width: "100%",
    padding: "6px 10px",
    borderRadius: 6,
    border: "1px solid var(--border-medium)",
    fontFamily: "var(--font-body)",
    fontSize: 13,
    color: "var(--text-primary)",
    background: "var(--bg-surface)",
    boxSizing: "border-box",
    outline: "none",
  };

  return (
    <tr>
      {/* S.No */}
      <td style={{ ...cellStyle, width: 40, color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-body)" }}>
        {row.s_no}
      </td>

      {/* Characteristic: FK select */}
      <td style={{ ...cellStyle, minWidth: 180 }}>
        <Select
          value={row.parameter ?? undefined}
          onChange={(v) => onParameterSelect(v ?? null)}
          showSearch
          allowClear
          filterOption={(input, opt) =>
            (opt?.label ?? "").toLowerCase().includes(input.toLowerCase())
          }
          placeholder="Select parameter"
          style={{ width: "100%" }}
          options={testParamOptions}
          size="small"
        />
      </td>

      {/* Unit */}
      <td style={{ ...cellStyle, minWidth: 120 }}>
        <Select
          value={row.unit ?? undefined}
          onChange={(v) => onUpdate({ unit: v ?? null })}
          allowClear
          placeholder="Unit"
          style={{ width: "100%" }}
          options={uomOptions}
          size="small"
        />
      </td>

      {/* Spec type toggle */}
      <td style={{ ...cellStyle, minWidth: 130 }}>
        <div style={{ display: "flex", gap: 4 }}>
          {[SPEC_TYPES.QUANTITATIVE, SPEC_TYPES.QUALITATIVE].map((t) => (
            <button
              key={t}
              onClick={() =>
                onUpdate({
                  spec_type: t,
                  spec_min: "",
                  spec_max: "",
                  spec_description: "",
                  result_value: "",
                  result_text: "",
                })
              }
              style={{
                flex: 1,
                padding: "4px 6px",
                border: "1px solid var(--border-medium)",
                borderRadius: 5,
                fontFamily: "var(--font-body)",
                fontSize: 11,
                cursor: "pointer",
                background:
                  row.spec_type === t ? "var(--primary)" : "transparent",
                color: row.spec_type === t ? "#fff" : "var(--text-secondary)",
              }}
            >
              {t === SPEC_TYPES.QUANTITATIVE ? "Qty" : "Qual"}
            </button>
          ))}
        </div>
      </td>

      {/* Spec values */}
      <td style={{ ...cellStyle, minWidth: 200 }}>
        {isQuantitative ? (
          <div style={{ display: "flex", gap: 6 }}>
            <input
              type="text"
              value={row.spec_min ?? ""}
              onChange={(e) => onUpdate({ spec_min: e.target.value })}
              placeholder="Min"
              style={{ ...smallInput, flex: 1 }}
            />
            <input
              type="text"
              value={row.spec_max ?? ""}
              onChange={(e) => onUpdate({ spec_max: e.target.value })}
              placeholder="Max"
              style={{ ...smallInput, flex: 1 }}
            />
          </div>
        ) : (
          <input
            type="text"
            value={row.spec_description ?? ""}
            onChange={(e) => onUpdate({ spec_description: e.target.value })}
            placeholder="e.g. White crystalline powder"
            style={smallInput}
          />
        )}
      </td>

      {/* Result */}
      <td style={{ ...cellStyle, minWidth: 120 }}>
        {isQuantitative ? (
          <input
            type="text"
            value={row.result_value ?? ""}
            onChange={(e) => onUpdate({ result_value: e.target.value })}
            placeholder="Result"
            style={smallInput}
          />
        ) : (
          <input
            type="text"
            value={row.result_text ?? "Complies"}
            onChange={(e) => onUpdate({ result_text: e.target.value })}
            placeholder="Complies"
            style={smallInput}
          />
        )}
      </td>

      {/* Test method: FK + free-text */}
      <td style={{ ...cellStyle, minWidth: 180 }}>
        <Select
          value={row.test_method ?? undefined}
          onChange={(v) => {
            const method = testMethodOptions.find((m) => m.value === v);
            onUpdate({
              test_method: v ?? null,
              test_method_code: method?.label.split(" — ")[0] ?? null,
            });
          }}
          showSearch
          allowClear
          filterOption={(input, opt) =>
            (opt?.label ?? "").toLowerCase().includes(input.toLowerCase())
          }
          placeholder="Select or type below"
          style={{ width: "100%", marginBottom: 4 }}
          options={testMethodOptions}
          size="small"
        />
      </td>

      {/* Delete */}
      <td style={{ ...cellStyle, textAlign: "center", width: 36 }}>
        <button
          onClick={onDelete}
          disabled={!canDelete}
          title="Remove row"
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: 28,
            height: 28,
            borderRadius: 6,
            border: "none",
            background: "transparent",
            cursor: canDelete ? "pointer" : "not-allowed",
            opacity: canDelete ? 1 : 0.3,
            color: "var(--pastel-pink-text)",
          }}
        >
          <Trash2 size={14} strokeWidth={1.5} />
        </button>
      </td>
    </tr>
  );
}
