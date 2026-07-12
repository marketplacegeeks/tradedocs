// Manual Edits page — lists every document generated in the system with its
// first-generation date and lets any role download the original PDF/Word or
// upload a manually-edited replacement with a mandatory reason.

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Modal, Select, message } from "antd";
import { FileEdit, Download, Search, Upload as UploadIcon } from "lucide-react";
import dayjs from "dayjs";

import { listManualEdits, uploadManualEdit, downloadOriginal } from "../../api/manualEdits";
import type { ManualEditRow } from "../../api/manualEdits";
import {
  DOCUMENT_TYPE_LABELS,
  DOCUMENT_TYPE_SHORT_LABELS,
  DOCUMENT_TYPE_CHIP,
  MANUAL_EDIT_DOCUMENT_TYPES,
} from "../../utils/constants";
import { extractApiError } from "../../utils/apiErrors";

const TYPE_FILTER_OPTIONS = [
  { value: "", label: "All document types" },
  ...Object.values(MANUAL_EDIT_DOCUMENT_TYPES).map((type) => ({
    value: type,
    label: DOCUMENT_TYPE_LABELS[type],
  })),
];

function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return dayjs(iso).format("DD MMM YYYY, HH:mm");
}

export default function ManualEditsPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [uploadTarget, setUploadTarget] = useState<ManualEditRow | null>(null);
  const [downloadingKey, setDownloadingKey] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["manual-edits"],
    queryFn: () => listManualEdits().then((r) => r.data),
  });

  const rows = data ?? [];

  const displayed = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return rows.filter((row) => {
      if (typeFilter && row.document_type !== typeFilter) return false;
      if (!q) return true;
      return (
        row.document_number.toLowerCase().includes(q) ||
        row.exporter_name.toLowerCase().includes(q) ||
        row.importer_name.toLowerCase().includes(q) ||
        row.vendor_name.toLowerCase().includes(q)
      );
    });
  }, [rows, searchQuery, typeFilter]);

  async function handleDownloadOriginal(row: ManualEditRow, kind: "pdf" | "word") {
    const path = kind === "pdf" ? row.download_pdf_path : row.download_word_path;
    if (!path) return;
    const key = `${row.document_type}-${row.document_id}-${kind}`;
    setDownloadingKey(key);
    try {
      const ext = kind === "pdf" ? "pdf" : "docx";
      await downloadOriginal(path, `${row.document_number}.${ext}`, kind);
    } catch {
      message.error(`Failed to download ${kind === "pdf" ? "PDF" : "Word document"}.`);
    } finally {
      setDownloadingKey(null);
    }
  }

  function closeUploadModal() {
    setUploadTarget(null);
  }

  function handleUploadSuccess() {
    message.success("Manual edit saved.");
    queryClient.invalidateQueries({ queryKey: ["manual-edits"] });
    closeUploadModal();
  }

  return (
    <div>
      {/* Page header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 24,
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: 22,
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: 4,
            }}
          >
            Manual Edits
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            {rows.length} document{rows.length !== 1 ? "s" : ""} across all document types
          </p>
        </div>
      </div>

      {/* Filters row */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 16, alignItems: "center" }}>
        <div style={{ position: "relative", flex: "1 1 240px", maxWidth: 320 }}>
          <Search
            size={15}
            strokeWidth={1.8}
            style={{
              position: "absolute",
              left: 11,
              top: "50%",
              transform: "translateY(-50%)",
              color: "var(--text-muted)",
              pointerEvents: "none",
            }}
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by document number or party…"
            style={{
              width: "100%",
              background: "var(--bg-surface)",
              border: "1px solid var(--border-medium)",
              borderRadius: 8,
              padding: "8px 12px 8px 34px",
              fontFamily: "var(--font-body)",
              fontSize: 13,
              color: "var(--text-primary)",
              outline: "none",
              boxSizing: "border-box",
            }}
          />
        </div>

        <Select
          value={typeFilter}
          onChange={setTypeFilter}
          style={{ width: 220, fontFamily: "var(--font-body)", fontSize: 13 }}
          options={TYPE_FILTER_OPTIONS}
        />
      </div>

      {/* Table */}
      <div
        style={{
          background: "var(--bg-surface)",
          borderRadius: 14,
          border: "1px solid var(--border-light)",
          boxShadow: "var(--shadow-card)",
          overflow: "hidden",
        }}
      >
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 900 }}>
            <thead>
              <tr style={{ background: "var(--bg-base)" }}>
                {[
                  "Document Number",
                  "Type",
                  "First Generated",
                  "Exporter",
                  "Importer",
                  "Vendor",
                  "Manual Edit",
                  "",
                ].map((label) => (
                  <th
                    key={label}
                    style={{
                      padding: "12px 16px",
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
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={8} style={{ padding: "48px 16px", textAlign: "center", fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
                    Loading…
                  </td>
                </tr>
              ) : displayed.length === 0 ? (
                <tr>
                  <td colSpan={8}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "48px 16px", gap: 12 }}>
                      <div
                        style={{
                          width: 48,
                          height: 48,
                          borderRadius: 12,
                          background: "var(--pastel-purple)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        <FileEdit size={22} color="var(--pastel-purple-text)" strokeWidth={1.5} />
                      </div>
                      <p style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                        No documents found
                      </p>
                      <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                        {searchQuery || typeFilter ? "No documents match your filters." : "Documents will appear here once they're created."}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                displayed.map((row) => (
                  <ManualEditRowItem
                    key={`${row.document_type}-${row.document_id}`}
                    row={row}
                    downloadingKey={downloadingKey}
                    onDownload={handleDownloadOriginal}
                    onUpload={() => setUploadTarget(row)}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {uploadTarget && (
        <UploadModal row={uploadTarget} onClose={closeUploadModal} onSuccess={handleUploadSuccess} />
      )}
    </div>
  );
}

// ---- Table row ----------------------------------------------------------------

const tdStyle: React.CSSProperties = {
  padding: "14px 16px",
  borderBottom: "1px solid var(--border-light)",
};

function ManualEditRowItem({
  row,
  downloadingKey,
  onDownload,
  onUpload,
}: {
  row: ManualEditRow;
  downloadingKey: string | null;
  onDownload: (row: ManualEditRow, kind: "pdf" | "word") => void;
  onUpload: () => void;
}) {
  return (
    <tr
      style={{ transition: "background 0.12s ease" }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)")}
      onMouseLeave={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")}
    >
      <td style={{ ...tdStyle, fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: 13, color: "var(--text-primary)" }}>
        {row.document_number}
      </td>
      <td style={tdStyle}>
        <span className={DOCUMENT_TYPE_CHIP[row.document_type]}>
          {DOCUMENT_TYPE_SHORT_LABELS[row.document_type]}
        </span>
      </td>
      <td style={{ ...tdStyle, fontFamily: "var(--font-body)", fontSize: 13, color: row.first_generated_at ? "var(--text-secondary)" : "var(--text-muted)" }}>
        {row.first_generated_at ? formatDateTime(row.first_generated_at) : "Not yet generated"}
      </td>
      <td style={{ ...tdStyle, fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
        {row.exporter_name || "—"}
      </td>
      <td style={{ ...tdStyle, fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
        {row.importer_name || "—"}
      </td>
      <td style={{ ...tdStyle, fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)" }}>
        {row.vendor_name || "—"}
      </td>
      <td style={tdStyle}>
        {row.has_manual_edit ? (
          <span className="chip-yellow">Manually Edited</span>
        ) : (
          <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)" }}>—</span>
        )}
      </td>
      <td style={{ ...tdStyle, textAlign: "right" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 12 }}>
          {row.download_pdf_path && (
            <button
              onClick={() => onDownload(row, "pdf")}
              disabled={downloadingKey === `${row.document_type}-${row.document_id}-pdf`}
              style={linkButtonStyle}
              title="Download original PDF"
            >
              <Download size={14} strokeWidth={1.8} /> PDF
            </button>
          )}
          {row.download_word_path && (
            <button
              onClick={() => onDownload(row, "word")}
              disabled={downloadingKey === `${row.document_type}-${row.document_id}-word`}
              style={linkButtonStyle}
              title="Download original Word document"
            >
              <Download size={14} strokeWidth={1.8} /> Word
            </button>
          )}
          <button onClick={onUpload} style={{ ...linkButtonStyle, color: "var(--primary)" }}>
            <UploadIcon size={14} strokeWidth={1.8} /> Upload Edit
          </button>
        </div>
      </td>
    </tr>
  );
}

const linkButtonStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 4,
  background: "none",
  border: "none",
  padding: 0,
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-secondary)",
  cursor: "pointer",
};

// ---- Upload modal ---------------------------------------------------------------

function UploadModal({
  row,
  onClose,
  onSuccess,
}: {
  row: ManualEditRow;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [comment, setComment] = useState("");
  const [wordFile, setWordFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    if (!comment.trim()) {
      message.error("A comment explaining why this file was manually edited is required.");
      return;
    }
    if (!wordFile && !pdfFile) {
      message.error("Upload at least a Word file or a PDF file.");
      return;
    }
    setSubmitting(true);
    try {
      await uploadManualEdit(row.document_type, row.document_id, {
        comment: comment.trim(),
        wordFile,
        pdfFile,
      });
      onSuccess();
    } catch (err) {
      message.error(extractApiError(err, "Failed to save the manual edit."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal
      title={`Upload Manual Edit — ${row.document_number}`}
      open
      onCancel={onClose}
      onOk={handleSubmit}
      confirmLoading={submitting}
      okText="Save Manual Edit"
    >
      {row.has_manual_edit && (
        <div
          style={{
            background: "var(--bg-input)",
            border: "1px solid var(--border-light)",
            borderRadius: 8,
            padding: "10px 12px",
            marginBottom: 16,
            fontFamily: "var(--font-body)",
            fontSize: 12.5,
            color: "var(--text-secondary)",
          }}
        >
          A manual edit already exists for this document — uploaded by{" "}
          <strong>{row.edited_by_name || "Unknown"}</strong> on {formatDateTime(row.edited_at)}.
          <br />
          Reason: {row.edit_comment}
          <br />
          Uploading a new file below will replace it.
        </div>
      )}

      <label style={labelStyle}>
        Word file (.docx)
        <input
          type="file"
          accept=".docx"
          onChange={(e) => setWordFile(e.target.files?.[0] ?? null)}
          style={fileInputStyle}
        />
      </label>

      <label style={labelStyle}>
        PDF file (.pdf)
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)}
          style={fileInputStyle}
        />
      </label>

      <label style={labelStyle}>
        Why was this file manually edited? <span style={{ color: "var(--pastel-pink-text)" }}>*</span>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={4}
          placeholder="Describe the specific correction made and why the auto-generated document needed it…"
          style={{
            width: "100%",
            background: "var(--bg-input)",
            border: "1px solid var(--border-medium)",
            borderRadius: 8,
            padding: "9px 12px",
            fontFamily: "var(--font-body)",
            fontSize: 14,
            color: "var(--text-primary)",
            outline: "none",
            boxSizing: "border-box",
            resize: "vertical",
          }}
        />
      </label>
    </Modal>
  );
}

const labelStyle: React.CSSProperties = {
  display: "block",
  fontFamily: "var(--font-body)",
  fontSize: 12,
  fontWeight: 500,
  color: "var(--text-muted)",
  marginBottom: 16,
};

const fileInputStyle: React.CSSProperties = {
  display: "block",
  width: "100%",
  marginTop: 6,
  fontFamily: "var(--font-body)",
  fontSize: 13,
  color: "var(--text-secondary)",
};
