// COA detail page — read-only view with workflow actions, PDF download, and audit log.

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Modal, Input, message, Spin } from "antd";
import { Download, History, Pencil } from "lucide-react";
import dayjs from "dayjs";

import {
  getCOA,
  getCOAPdf,
  getCOAAuditLog,
  submitCOA,
  approveCOA,
  rejectCOA,
  reworkCOA,
} from "../../api/coa";
import { useAuth } from "../../store/AuthContext";
import {
  ROLES,
  DOCUMENT_STATUS,
  DOCUMENT_STATUS_LABELS,
  DOCUMENT_STATUS_CHIP,
  SPEC_TYPES,
} from "../../utils/constants";
import { extractApiError } from "../../utils/apiErrors";
import AuditLogDrawer from "../../components/AuditLogDrawer";
import type { AuditLogEntry } from "../../components/AuditLogDrawer";

// ---- Decimal string normalisation -----------------------------------------
// Still used for package_volume (DecimalField). Strips Django's trailing zeros
// so "1000.000" displays as "1000".

function normalizeDecimalStr(val: string | number | null | undefined): string | null {
  if (val === null || val === undefined || val === "") return null;
  const num = parseFloat(String(val));
  if (isNaN(num)) return String(val);
  return String(num);
}

// ---- OOS detection (mirrors COAFormPage logic) -----------------------------

function extractSpecNumber(raw: string | null | undefined): number | null {
  if (!raw) return null;
  const trimmed = raw.trim();
  if (trimmed === "*") return null;
  const numeric = trimmed.replace(/^[<>≤≥=*]?\s*(NMT|NLT|APPROX)?\s*/i, "").trim();
  const n = parseFloat(numeric);
  return isNaN(n) ? null : n;
}

function isParamOutOfSpec(param: { spec_type: string; spec_min?: string | null; spec_max?: string | null; result_value?: string | null }): boolean {
  if (param.spec_type !== "QUANTITATIVE") return false;
  const rawResult = (param.result_value ?? "").trim();
  if (!rawResult) return false;
  const resultNum = parseFloat(rawResult.replace(/^[<>≤≥]\s*/, ""));
  if (isNaN(resultNum)) return false;
  const specMinRaw = String(param.spec_min ?? "").trim();
  const specMaxRaw = String(param.spec_max ?? "").trim();
  if (specMinRaw && specMinRaw !== "*") {
    const minNum = extractSpecNumber(specMinRaw);
    if (minNum !== null && resultNum < minNum) return true;
  }
  if (specMaxRaw && specMaxRaw !== "*") {
    const maxNum = extractSpecNumber(specMaxRaw);
    if (maxNum !== null && resultNum > maxNum) return true;
  }
  return false;
}

// ---- Read-only field display helper ----------------------------------------

function InfoField({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div>
      <div
        style={{
          fontFamily: "var(--font-body)",
          fontSize: 11,
          fontWeight: 600,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: "var(--font-body)",
          fontSize: 14,
          color: value ? "var(--text-primary)" : "var(--text-muted)",
        }}
      >
        {value ?? "—"}
      </div>
    </div>
  );
}

// ---- Page ------------------------------------------------------------------

export default function COADetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Audit log drawer state
  const [auditOpen, setAuditOpen] = useState(false);

  // Comment modal state for reject / rework actions
  const [commentModal, setCommentModal] = useState<"reject" | "rework" | null>(null);
  const [comment, setComment] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const [pdfLoading, setPdfLoading] = useState(false);

  // ---- Queries ------------------------------------------------------------

  const { data: coa, isLoading } = useQuery({
    queryKey: ["coa", id],
    queryFn: () => getCOA(Number(id)).then((r) => r.data),
    enabled: Boolean(id),
  });

  const { data: auditEntries = [], isLoading: auditLoading } = useQuery({
    queryKey: ["coa-audit", id],
    queryFn: () => getCOAAuditLog(Number(id)).then((r) => r.data as AuditLogEntry[]),
    enabled: auditOpen && Boolean(id),
  });

  // ---- Workflow helpers ----------------------------------------------------

  const isMakerOrAdmin =
    user?.role === ROLES.MAKER ||
    user?.role === ROLES.COMPANY_ADMIN ||
    user?.role === ROLES.SUPER_ADMIN;

  const isCheckerOrAdmin =
    user?.role === ROLES.CHECKER ||
    user?.role === ROLES.COMPANY_ADMIN ||
    user?.role === ROLES.SUPER_ADMIN;

  function invalidateCOA() {
    queryClient.invalidateQueries({ queryKey: ["coa", id] });
    queryClient.invalidateQueries({ queryKey: ["coas"] });
  }

  async function handleSubmit() {
    if (!id) return;
    setActionLoading(true);
    try {
      await submitCOA(Number(id));
      message.success("COA submitted for approval.");
      invalidateCOA();
    } catch (err) {
      message.error(extractApiError(err, "Failed to submit."));
    } finally {
      setActionLoading(false);
    }
  }

  async function handleApprove() {
    if (!id) return;
    setActionLoading(true);
    try {
      await approveCOA(Number(id));
      message.success("COA approved.");
      invalidateCOA();
    } catch (err) {
      message.error(extractApiError(err, "Failed to approve."));
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCommentAction() {
    if (!id || !commentModal) return;
    if (!comment.trim()) {
      message.error("A comment is required.");
      return;
    }
    setActionLoading(true);
    try {
      if (commentModal === "reject") {
        await rejectCOA(Number(id), comment);
        message.success("COA permanently rejected.");
      } else {
        await reworkCOA(Number(id), comment);
        message.success("COA sent for rework.");
      }
      setCommentModal(null);
      setComment("");
      invalidateCOA();
    } catch (err) {
      message.error(extractApiError(err, "Action failed."));
    } finally {
      setActionLoading(false);
    }
  }

  async function handleDownloadPdf() {
    if (!coa) return;
    setPdfLoading(true);
    try {
      const res = await getCOAPdf(coa.id);
      const url = URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${coa.coa_number}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      message.error("Failed to download PDF.");
    } finally {
      setPdfLoading(false);
    }
  }

  // ---- Loading state ------------------------------------------------------

  if (isLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!coa) {
    return (
      <div
        style={{ padding: 48, textAlign: "center", fontFamily: "var(--font-body)", color: "var(--text-muted)" }}
      >
        COA not found.
      </div>
    );
  }

  // ---- Determine visible actions ------------------------------------------

  const status = coa.status as string;
  const canEdit =
    (status === DOCUMENT_STATUS.DRAFT || status === DOCUMENT_STATUS.REWORK) && isMakerOrAdmin;

  const showSubmit =
    (status === DOCUMENT_STATUS.DRAFT || status === DOCUMENT_STATUS.REWORK) && isMakerOrAdmin;

  const showApprove = status === DOCUMENT_STATUS.PENDING_APPROVAL && isCheckerOrAdmin;
  const showRejectRework = status === DOCUMENT_STATUS.PENDING_APPROVAL && isCheckerOrAdmin;

  // Browser timezone abbreviation (e.g. "IST", "PST")
  const tzAbbr =
    Intl.DateTimeFormat(undefined, { timeZoneName: "short" })
      .formatToParts(new Date())
      .find((p) => p.type === "timeZoneName")?.value ?? "";

  const tdStyle: React.CSSProperties = {
    padding: "12px 14px",
    borderBottom: "1px solid var(--border-light)",
    fontFamily: "var(--font-body)",
    fontSize: 13,
    color: "var(--text-secondary)",
    verticalAlign: "top",
  };

  return (
    <div>
      {/* Top bar: COA number + status + actions */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 24,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
            <h1
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: 22,
                fontWeight: 700,
                color: "var(--text-primary)",
                margin: 0,
              }}
            >
              {coa.coa_number}
            </h1>
            <span className={DOCUMENT_STATUS_CHIP[coa.status] ?? "chip-blue"}>
              {DOCUMENT_STATUS_LABELS[coa.status] ?? coa.status}
            </span>
          </div>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
            Created by {coa.created_by_name} · {dayjs(coa.created_at).format("DD MMM YYYY")}
          </p>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          {/* Audit log button */}
          <button
            onClick={() => setAuditOpen(true)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              padding: "8px 14px",
              background: "transparent",
              border: "1px solid var(--border-medium)",
              borderRadius: 8,
              fontFamily: "var(--font-body)",
              fontSize: 13,
              color: "var(--text-secondary)",
              cursor: "pointer",
            }}
          >
            <History size={14} strokeWidth={1.5} />
            Audit Log
          </button>

          {/* Download PDF */}
          <button
            onClick={handleDownloadPdf}
            disabled={pdfLoading}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              padding: "8px 14px",
              background: "transparent",
              border: "1px solid var(--border-medium)",
              borderRadius: 8,
              fontFamily: "var(--font-body)",
              fontSize: 13,
              color: "var(--text-secondary)",
              cursor: pdfLoading ? "not-allowed" : "pointer",
              opacity: pdfLoading ? 0.6 : 1,
            }}
          >
            <Download size={14} strokeWidth={1.5} />
            {pdfLoading ? "Downloading…" : "Download PDF"}
          </button>

          {/* Edit button (DRAFT / REWORK) */}
          {canEdit && (
            <button
              onClick={() => navigate(`/coas/${coa.id}/edit`)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                padding: "8px 14px",
                background: "transparent",
                border: "1px solid var(--border-medium)",
                borderRadius: 8,
                fontFamily: "var(--font-body)",
                fontSize: 13,
                color: "var(--text-secondary)",
                cursor: "pointer",
              }}
            >
              <Pencil size={14} strokeWidth={1.5} />
              Edit
            </button>
          )}

          {/* Submit */}
          {showSubmit && (
            <button
              onClick={handleSubmit}
              disabled={actionLoading}
              style={{
                padding: "8px 16px",
                background: "var(--primary)",
                border: "none",
                borderRadius: 8,
                fontFamily: "var(--font-body)",
                fontSize: 13,
                fontWeight: 500,
                color: "#fff",
                cursor: actionLoading ? "not-allowed" : "pointer",
                opacity: actionLoading ? 0.6 : 1,
              }}
            >
              Submit for Approval
            </button>
          )}

          {/* Approve */}
          {showApprove && (
            <button
              onClick={handleApprove}
              disabled={actionLoading}
              style={{
                padding: "8px 16px",
                background: "var(--pastel-green)",
                border: "none",
                borderRadius: 8,
                fontFamily: "var(--font-body)",
                fontSize: 13,
                fontWeight: 500,
                color: "var(--pastel-green-text)",
                cursor: actionLoading ? "not-allowed" : "pointer",
                opacity: actionLoading ? 0.6 : 1,
              }}
            >
              Approve
            </button>
          )}

          {/* Rework */}
          {showRejectRework && (
            <button
              onClick={() => { setCommentModal("rework"); setComment(""); }}
              disabled={actionLoading}
              style={{
                padding: "8px 16px",
                background: "var(--pastel-yellow)",
                border: "none",
                borderRadius: 8,
                fontFamily: "var(--font-body)",
                fontSize: 13,
                fontWeight: 500,
                color: "var(--pastel-yellow-text)",
                cursor: actionLoading ? "not-allowed" : "pointer",
                opacity: actionLoading ? 0.6 : 1,
              }}
            >
              Send for Rework
            </button>
          )}

          {/* Reject */}
          {showRejectRework && (
            <button
              onClick={() => { setCommentModal("reject"); setComment(""); }}
              disabled={actionLoading}
              style={{
                padding: "8px 16px",
                background: "var(--pastel-pink)",
                border: "none",
                borderRadius: 8,
                fontFamily: "var(--font-body)",
                fontSize: 13,
                fontWeight: 500,
                color: "var(--pastel-pink-text)",
                cursor: actionLoading ? "not-allowed" : "pointer",
                opacity: actionLoading ? 0.6 : 1,
              }}
            >
              Reject
            </button>
          )}
        </div>
      </div>

      {/* Header info card */}
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
          COA Details
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <InfoField label="Product" value={`${coa.product_name} — ${coa.grade}`} />
          <InfoField label="Customer" value={coa.customer_name} />
          <InfoField label="Batch Number" value={coa.batch_number} />
          <InfoField label="Footer Company" value={coa.footer_organisation_name} />
          <InfoField label="Package Count" value={coa.package_count} />
          <InfoField
            label="Package Volume"
            value={`${normalizeDecimalStr(coa.package_volume)} ${coa.package_uom_abbreviation}`}
          />
          <InfoField label="Package Type" value={coa.package_type_name} />
          <InfoField label="Date of Manufacture" value={dayjs(coa.date_of_manufacture).format("DD MMM YYYY")} />
          <InfoField label="Date & Time of Sampling" value={coa.date_time_of_sampling ? `${dayjs(coa.date_time_of_sampling).format("DD MMM YYYY hh:mm A")} ${tzAbbr}` : "—"} />
          <InfoField label="Date & Time of Analysis" value={coa.date_time_of_analysis ? `${dayjs(coa.date_time_of_analysis).format("DD MMM YYYY hh:mm A")} ${tzAbbr}` : "—"} />
          <InfoField label="Date of Retest" value={dayjs(coa.date_of_retest).format("DD MMM YYYY")} />
          <InfoField label="Date of Despatch" value={coa.date_of_despatch ? dayjs(coa.date_of_despatch).format("DD MMM YYYY") : "—"} />
        </div>
      </div>

      {/* Test parameters table */}
      <div
        style={{
          background: "var(--bg-surface)",
          borderRadius: 14,
          border: "1px solid var(--border-light)",
          boxShadow: "var(--shadow-card)",
          overflow: "hidden",
          marginBottom: 20,
        }}
      >
        <div style={{ padding: "18px 24px", borderBottom: "1px solid var(--border-light)" }}>
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
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
            <thead>
              <tr style={{ background: "var(--bg-base)" }}>
                {[
                  "S.No",
                  "Characteristic",
                  "Unit",
                  "Spec Type",
                  "Specification",
                  "Result",
                  "Test Method",
                ].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "11px 14px",
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
              {coa.parameters.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    style={{
                      padding: "32px 14px",
                      textAlign: "center",
                      fontFamily: "var(--font-body)",
                      fontSize: 13,
                      color: "var(--text-muted)",
                    }}
                  >
                    No test parameters recorded.
                  </td>
                </tr>
              ) : (
                coa.parameters.map((param) => {
                  const oos = isParamOutOfSpec(param);
                  return (
                    <tr
                      key={param.id ?? param.s_no}
                      onMouseEnter={(e) =>
                        ((e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)")
                      }
                      onMouseLeave={(e) =>
                        ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")
                      }
                    >
                      <td style={tdStyle}>{param.s_no}</td>
                      <td style={tdStyle}>{param.parameter_name ?? "—"}</td>
                      <td style={tdStyle}>{param.unit_abbreviation ?? "—"}</td>
                      <td style={tdStyle}>
                        <span
                          className={
                            param.spec_type === SPEC_TYPES.QUANTITATIVE ? "chip-blue" : "chip-purple"
                          }
                          style={{ fontSize: 11 }}
                        >
                          {param.spec_type === SPEC_TYPES.QUANTITATIVE ? "Quantitative" : "Qualitative"}
                        </span>
                      </td>
                      <td style={tdStyle}>
                        {param.spec_type === SPEC_TYPES.QUANTITATIVE
                          ? [param.spec_min, param.spec_max].filter(Boolean).join(" – ") || "—"
                          : param.spec_description || "—"}
                      </td>
                      <td
                        style={{
                          ...tdStyle,
                          ...(oos && {
                            background: "var(--pastel-pink)",
                            color: "var(--pastel-pink-text)",
                            fontWeight: 600,
                          }),
                        }}
                        title={oos ? "Out of specification" : undefined}
                      >
                        {param.spec_type === SPEC_TYPES.QUANTITATIVE
                          ? param.result_value || "—"
                          : param.result_text || "—"}
                      </td>
                      <td style={tdStyle}>
                        {param.test_method_code || "—"}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit log drawer */}
      <AuditLogDrawer
        open={auditOpen}
        onClose={() => setAuditOpen(false)}
        entries={auditEntries}
        loading={auditLoading}
        title="COA Audit Trail"
      />

      {/* Comment modal — Reject / Rework */}
      <Modal
        title={commentModal === "reject" ? "Permanently Reject" : "Send for Rework"}
        open={commentModal !== null}
        onOk={handleCommentAction}
        onCancel={() => { setCommentModal(null); setComment(""); }}
        okText="Confirm"
        okButtonProps={{ loading: actionLoading, danger: commentModal === "reject" }}
        cancelText="Cancel"
        destroyOnClose
      >
        <p
          style={{
            marginBottom: 12,
            fontFamily: "var(--font-body)",
            fontSize: 14,
            color: "var(--text-secondary)",
          }}
        >
          {commentModal === "reject"
            ? "Please provide a reason for permanently rejecting this COA (required)."
            : "Please provide a reason for sending this COA back for rework (required)."}
        </p>
        <Input.TextArea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={4}
          placeholder="Enter your comment…"
          autoFocus
        />
      </Modal>
    </div>
  );
}
