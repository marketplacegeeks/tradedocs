// All Manual Edits page API calls.
// Constraint #22: no component calls axios directly — only api files do.

import axiosInstance from "./axiosInstance";
import type { ManualEditDocumentType } from "../utils/constants";

export interface ManualEditRow {
  document_type: ManualEditDocumentType;
  document_id: number;
  document_number: string;
  exporter_name: string;
  importer_name: string;
  vendor_name: string;
  first_generated_at: string | null;
  has_manual_edit: boolean;
  edit_comment: string;
  edited_at: string | null;
  edited_by_name: string;
  edited_word_file: string | null;
  edited_pdf_file: string | null;
  download_pdf_path: string | null;
  download_word_path: string | null;
}

export const listManualEdits = () =>
  axiosInstance.get<ManualEditRow[]>("/manual-edits/");

export const uploadManualEdit = (
  documentType: ManualEditDocumentType,
  documentId: number,
  data: { comment: string; wordFile?: File | null; pdfFile?: File | null }
) => {
  const formData = new FormData();
  formData.append("comment", data.comment);
  if (data.wordFile) formData.append("word_file", data.wordFile);
  if (data.pdfFile) formData.append("pdf_file", data.pdfFile);

  return axiosInstance.post<ManualEditRow>(
    `/manual-edits/${documentType}/${documentId}/upload/`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
};

const DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

// download_pdf_path / download_word_path on ManualEditRow are relative API paths
// (e.g. "/proforma-invoices/12/pdf/") — reuse each document type's own PDF/Word
// endpoint rather than duplicating a per-type URL scheme here.
export async function downloadOriginal(path: string, filename: string, kind: "pdf" | "word") {
  const response = await axiosInstance.get(path, { responseType: "blob" });
  const mime = kind === "pdf" ? "application/pdf" : DOCX_MIME;
  const url = URL.createObjectURL(new Blob([response.data], { type: mime }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

// edited_word_file / edited_pdf_file on ManualEditRow are already-absolute media
// URLs (built server-side via request.build_absolute_uri), so they're opened
// directly as links rather than routed through this file.
