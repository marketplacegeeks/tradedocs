// Dedicated page to configure the test template (parameters + spec limits) for one product grade.
// Route: /master-data/products/:productId/grades/:gradeId/template

import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Select, message } from "antd";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";

import {
  listProducts,
  listTestParameters,
  listTestMethods,
  getProductGradeTemplate,
  saveProductGradeTemplate,
} from "../../api/coa";
import { listUOMs } from "../../api/referenceData";
import { extractApiError } from "../../utils/apiErrors";

// ---- Row type for the template editor --------------------------------------

interface TemplateRow {
  id?: number;
  s_no: number;
  parameter: number | null;
  parameter_label: string;
  unit: number | null;
  spec_type: "QUANTITATIVE" | "QUALITATIVE";
  spec_min: string;
  spec_max: string;
  spec_description: string;
  test_method: number | null;
  test_method_label: string;
}

function blankRow(sNo: number): TemplateRow {
  return {
    s_no: sNo,
    parameter: null,
    parameter_label: "",
    unit: null,
    spec_type: "QUANTITATIVE",
    spec_min: "",
    spec_max: "",
    spec_description: "",
    test_method: null,
    test_method_label: "",
  };
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "7px 10px",
  borderRadius: 7,
  border: "1px solid var(--border-medium)",
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-primary)",
  background: "var(--bg-input)",
  outline: "none",
  boxSizing: "border-box",
};

// ---- Main page -------------------------------------------------------------

export default function ProductTestTemplatePage() {
  const { productId, gradeId } = useParams<{ productId: string; gradeId: string }>();
  const navigate = useNavigate();

  const [rows, setRows] = useState<TemplateRow[]>([blankRow(1)]);
  const [saving, setSaving] = useState(false);

  // ---- Master data queries -------------------------------------------------

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

  const { data: uoms = [] } = useQuery({
    queryKey: ["uoms"],
    queryFn: listUOMs,
  });

  // ---- Derive product + grade names from URL params -----------------------

  const product = products.find((p) => p.id === Number(productId)) ?? null;
  const grade = product?.grades.find((g) => g.id === Number(gradeId)) ?? null;

  // ---- Load existing template on mount ------------------------------------

  const { data: templateData } = useQuery({
    queryKey: ["product-grade-template", gradeId],
    queryFn: () => getProductGradeTemplate(Number(gradeId)).then((r) => r.data),
    enabled: Boolean(gradeId),
  });

  useEffect(() => {
    if (!templateData) return;
    const existingRows: TemplateRow[] = templateData.rows ?? [];
    if (existingRows.length > 0) {
      setRows(existingRows.map((r: TemplateRow, i: number) => ({ ...r, s_no: i + 1 })));
    }
  }, [templateData]);

  // ---- Row operations ------------------------------------------------------

  function updateRow(index: number, patch: Partial<TemplateRow>) {
    setRows((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...patch };
      return next;
    });
  }

  function addRow() {
    setRows((prev) => [...prev, blankRow(prev.length + 1)]);
  }

  // Remove a row and re-number s_no so they stay sequential
  function deleteRow(index: number) {
    setRows((prev) =>
      prev.filter((_, i) => i !== index).map((r, i) => ({ ...r, s_no: i + 1 }))
    );
  }

  // When a parameter is selected, auto-fill the label and unit if not yet set
  function handleParameterSelect(index: number, paramId: number | null) {
    const param = testParameters.find((p) => p.id === paramId) ?? null;
    const current = rows[index];
    updateRow(index, {
      parameter: paramId,
      parameter_label: current.parameter_label || (param?.name ?? ""),
      unit: current.unit ?? param?.default_unit ?? null,
    });
  }

  // When a test method is selected, auto-fill the method label if not yet set
  function handleMethodSelect(index: number, methodId: number | null) {
    const method = testMethods.find((m) => m.id === methodId) ?? null;
    const current = rows[index];
    updateRow(index, {
      test_method: methodId,
      test_method_label: current.test_method_label || (method?.code ?? ""),
    });
  }

  // ---- Save ----------------------------------------------------------------

  async function handleSave() {
    const invalid = rows.some((r) => !r.parameter_label.trim());
    if (invalid) {
      message.error("Each row must have a parameter label.");
      return;
    }
    setSaving(true);
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await saveProductGradeTemplate(Number(gradeId), rows as any);
      message.success("Template saved.");
    } catch (err: unknown) {
      message.error(extractApiError(err, "Failed to save template."));
    } finally {
      setSaving(false);
    }
  }

  // ---- Select option lists -------------------------------------------------

  const paramOptions = testParameters.map((p) => ({ value: p.id, label: p.name }));
  const methodOptions = testMethods.map((m) => ({ value: m.id, label: m.code }));
  const uomOptions = uoms.map((u) => ({ value: u.id, label: u.abbreviation }));

  // ---- Render ---------------------------------------------------------------

  return (
    <div style={{ padding: 32, background: "var(--bg-base)", minHeight: "100vh" }}>

      {/* Page header */}
      <div
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: 28, flexWrap: "wrap", gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <button
            onClick={() => navigate("/master-data/reference-data")}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "8px 14px", background: "transparent",
              border: "1px solid var(--border-medium)", borderRadius: 8,
              fontFamily: "var(--font-body)", fontSize: 13,
              color: "var(--text-secondary)", cursor: "pointer",
            }}
          >
            <ArrowLeft size={15} strokeWidth={1.5} />
            Back
          </button>
          <div>
            <h1
              style={{
                fontFamily: "var(--font-display)", fontSize: 22,
                fontWeight: 700, color: "var(--text-primary)", margin: 0,
              }}
            >
              Test Template
            </h1>
            {product && grade && (
              <div
                style={{
                  fontFamily: "var(--font-body)", fontSize: 13,
                  color: "var(--text-muted)", marginTop: 3,
                }}
              >
                {product.name}
                <span style={{ margin: "0 6px", color: "var(--border-medium)" }}>—</span>
                {grade.grade}
              </div>
            )}
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            padding: "9px 20px", background: "var(--primary)", color: "#fff",
            border: "none", borderRadius: 8, fontFamily: "var(--font-body)",
            fontSize: 14, fontWeight: 500, cursor: saving ? "not-allowed" : "pointer",
            opacity: saving ? 0.6 : 1,
          }}
        >
          {saving ? "Saving…" : "Save Template"}
        </button>
      </div>

      {/* Template table card */}
      <div
        style={{
          background: "var(--bg-surface)", border: "1px solid var(--border-light)",
          borderRadius: 14, boxShadow: "var(--shadow-card)", overflow: "hidden",
        }}
      >
        <div style={{ overflowX: "auto", WebkitOverflowScrolling: "touch" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 1200 }}>
            <thead>
              <tr style={{ background: "var(--bg-base)" }}>
                {["#", "Parameter", "Label *", "Unit", "Type", "Min", "Max", "Description", "Test Method", "Method Label", ""].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "10px 12px", textAlign: "left",
                      fontFamily: "var(--font-body)", fontSize: 11,
                      fontWeight: 600, color: "var(--text-muted)",
                      textTransform: "uppercase", letterSpacing: "0.05em",
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
                <tr
                  key={idx}
                  style={{ borderBottom: "1px solid var(--border-light)", transition: "background 0.1s" }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-hover)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  {/* Row number */}
                  <td style={{ padding: "8px 12px", width: 36 }}>
                    <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)" }}>
                      {row.s_no}
                    </span>
                  </td>

                  {/* Parameter dropdown */}
                  <td style={{ padding: "6px 8px", minWidth: 190 }}>
                    <Select
                      style={{ width: "100%" }}
                      placeholder="Select…"
                      allowClear
                      showSearch
                      optionFilterProp="label"
                      options={paramOptions}
                      value={row.parameter ?? undefined}
                      onChange={(val) => handleParameterSelect(idx, val ?? null)}
                      size="small"
                    />
                  </td>

                  {/* Label (required) */}
                  <td style={{ padding: "6px 8px", minWidth: 160 }}>
                    <input
                      style={inputStyle}
                      value={row.parameter_label}
                      onChange={(e) => updateRow(idx, { parameter_label: e.target.value })}
                      placeholder="Display label"
                    />
                  </td>

                  {/* Unit */}
                  <td style={{ padding: "6px 8px", minWidth: 110 }}>
                    <Select
                      style={{ width: "100%" }}
                      placeholder="Unit"
                      allowClear
                      showSearch
                      optionFilterProp="label"
                      options={uomOptions}
                      value={row.unit ?? undefined}
                      onChange={(val) => updateRow(idx, { unit: val ?? null })}
                      size="small"
                    />
                  </td>

                  {/* Spec type */}
                  <td style={{ padding: "6px 8px", minWidth: 145 }}>
                    <Select
                      style={{ width: "100%" }}
                      options={[
                        { value: "QUANTITATIVE", label: "Quantitative" },
                        { value: "QUALITATIVE", label: "Qualitative" },
                      ]}
                      value={row.spec_type}
                      onChange={(val) => updateRow(idx, { spec_type: val })}
                      size="small"
                    />
                  </td>

                  {/* Min — only for quantitative */}
                  <td style={{ padding: "6px 8px", minWidth: 90 }}>
                    {row.spec_type === "QUANTITATIVE" ? (
                      <input
                        style={inputStyle}
                        type="number"
                        value={row.spec_min}
                        onChange={(e) => updateRow(idx, { spec_min: e.target.value })}
                        placeholder="Min"
                      />
                    ) : (
                      <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--border-medium)", paddingLeft: 4 }}>—</span>
                    )}
                  </td>

                  {/* Max — only for quantitative */}
                  <td style={{ padding: "6px 8px", minWidth: 90 }}>
                    {row.spec_type === "QUANTITATIVE" ? (
                      <input
                        style={inputStyle}
                        type="number"
                        value={row.spec_max}
                        onChange={(e) => updateRow(idx, { spec_max: e.target.value })}
                        placeholder="Max"
                      />
                    ) : (
                      <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--border-medium)", paddingLeft: 4 }}>—</span>
                    )}
                  </td>

                  {/* Description */}
                  <td style={{ padding: "6px 8px", minWidth: 170 }}>
                    <input
                      style={inputStyle}
                      value={row.spec_description}
                      onChange={(e) => updateRow(idx, { spec_description: e.target.value })}
                      placeholder={row.spec_type === "QUALITATIVE" ? "e.g. Clear, colourless" : "Optional note"}
                    />
                  </td>

                  {/* Test method dropdown */}
                  <td style={{ padding: "6px 8px", minWidth: 210 }}>
                    <Select
                      style={{ width: "100%" }}
                      placeholder="Select…"
                      allowClear
                      showSearch
                      optionFilterProp="label"
                      options={methodOptions}
                      value={row.test_method ?? undefined}
                      onChange={(val) => handleMethodSelect(idx, val ?? null)}
                      size="small"
                    />
                  </td>

                  {/* Method label */}
                  <td style={{ padding: "6px 8px", minWidth: 150 }}>
                    <input
                      style={inputStyle}
                      value={row.test_method_label}
                      onChange={(e) => updateRow(idx, { test_method_label: e.target.value })}
                      placeholder="Method label"
                    />
                  </td>

                  {/* Delete row */}
                  <td style={{ padding: "6px 12px", width: 44, textAlign: "center" }}>
                    <button
                      onClick={() => deleteRow(idx)}
                      title="Remove row"
                      style={{
                        display: "inline-flex", alignItems: "center", justifyContent: "center",
                        width: 28, height: 28, borderRadius: 6,
                        background: "transparent", border: "1px solid var(--border-medium)",
                        cursor: "pointer", color: "var(--pastel-pink-text)",
                      }}
                    >
                      <Trash2 size={13} strokeWidth={1.5} />
                    </button>
                  </td>
                </tr>
              ))}

              {rows.length === 0 && (
                <tr>
                  <td
                    colSpan={11}
                    style={{
                      padding: 40, textAlign: "center",
                      fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)",
                    }}
                  >
                    No rows yet. Click "Add Row" to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Add row */}
        <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border-light)" }}>
          <button
            onClick={addRow}
            style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              padding: "7px 14px", background: "transparent",
              border: "1px solid var(--border-medium)", borderRadius: 7,
              fontFamily: "var(--font-body)", fontSize: 13,
              color: "var(--text-secondary)", cursor: "pointer",
            }}
          >
            <Plus size={14} strokeWidth={1.5} />
            Add Row
          </button>
        </div>
      </div>
    </div>
  );
}
