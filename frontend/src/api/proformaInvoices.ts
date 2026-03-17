// All Proforma Invoice API calls. Constraint #22: no component calls axios directly.

import axiosInstance from "./axiosInstance";

// ---- Types ------------------------------------------------------------------

export interface ProformaInvoiceLineItem {
  id: number;
  hsn_code: string;
  item_code: string;
  description: string;
  quantity: string;
  uom: number | null;
  rate_usd: string;
  amount_usd: string;
}

export interface ProformaInvoiceCharge {
  id: number;
  description: string;
  amount_usd: string;
}

export interface ProformaInvoice {
  id: number;
  pi_number: string;
  pi_date: string;
  exporter: number;
  exporter_name: string;
  consignee: number;
  consignee_name: string;
  buyer: number | null;
  buyer_name: string | null;
  buyer_order_no: string;
  buyer_order_date: string | null;
  other_references: string;
  country_of_origin: number | null;
  country_of_final_destination: number | null;
  pre_carriage_by: number | null;
  place_of_receipt: number | null;
  vessel_flight_no: string;
  port_of_loading: number | null;
  port_of_discharge: number | null;
  final_destination: number | null;
  payment_terms: number | null;
  payment_terms_name: string | null;
  incoterms: number | null;
  incoterms_code: string | null;
  bank: number | null;
  port_of_loading_name: string | null;
  port_of_discharge_name: string | null;
  validity_for_acceptance: string | null;
  validity_for_shipment: string | null;
  partial_shipment: string;
  transshipment: string;
  tc_template: number | null;
  tc_content: string;
  freight: string | null;
  insurance_amount: string | null;
  import_duty: string | null;
  destination_charges: string | null;
  // Computed totals
  line_items_total: string;
  charges_total: string;
  grand_total: string;
  invoice_total: string;
  line_items: ProformaInvoiceLineItem[];
  charges: ProformaInvoiceCharge[];
  status: string;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  signed_copy_url: string | null;
}

export interface AuditLogEntry {
  id: number;
  action: string;
  from_status: string;
  to_status: string;
  comment: string;
  performed_by_name: string;
  performed_at: string;
}

export type ProformaInvoicePayload = Partial<Omit<ProformaInvoice,
  "id" | "pi_number" | "status" | "created_by" | "created_by_name" | "created_at" | "updated_at"
  | "line_items" | "charges" | "line_items_total" | "charges_total" | "grand_total" | "invoice_total"
  | "incoterms_code"
>>;

// ---- API functions ----------------------------------------------------------

export function listProformaInvoices(params?: Record<string, string>) {
  return axiosInstance.get<ProformaInvoice[]>("/proforma-invoices/", { params }).then(r => r.data);
}

export function getProformaInvoice(id: number) {
  return axiosInstance.get<ProformaInvoice>(`/proforma-invoices/${id}/`).then(r => r.data);
}

export function createProformaInvoice(data: ProformaInvoicePayload) {
  return axiosInstance.post<ProformaInvoice>("/proforma-invoices/", data).then(r => r.data);
}

export function updateProformaInvoice(id: number, data: ProformaInvoicePayload) {
  return axiosInstance.patch<ProformaInvoice>(`/proforma-invoices/${id}/`, data).then(r => r.data);
}

// ---- Line items -------------------------------------------------------------

export function listLineItems(piId: number) {
  return axiosInstance.get<ProformaInvoiceLineItem[]>(`/proforma-invoices/${piId}/line-items/`).then(r => r.data);
}

export function createLineItem(piId: number, data: Omit<ProformaInvoiceLineItem, "id" | "amount_usd">) {
  return axiosInstance.post<ProformaInvoiceLineItem>(`/proforma-invoices/${piId}/line-items/`, data).then(r => r.data);
}

export function updateLineItem(piId: number, lid: number, data: Partial<Omit<ProformaInvoiceLineItem, "id" | "amount_usd">>) {
  return axiosInstance.patch<ProformaInvoiceLineItem>(`/proforma-invoices/${piId}/line-items/${lid}/`, data).then(r => r.data);
}

export function deleteLineItem(piId: number, lid: number) {
  return axiosInstance.delete(`/proforma-invoices/${piId}/line-items/${lid}/`);
}

// ---- Charges ----------------------------------------------------------------

export function listCharges(piId: number) {
  return axiosInstance.get<ProformaInvoiceCharge[]>(`/proforma-invoices/${piId}/charges/`).then(r => r.data);
}

export function createCharge(piId: number, data: Omit<ProformaInvoiceCharge, "id">) {
  return axiosInstance.post<ProformaInvoiceCharge>(`/proforma-invoices/${piId}/charges/`, data).then(r => r.data);
}

export function updateCharge(piId: number, cid: number, data: Partial<Omit<ProformaInvoiceCharge, "id">>) {
  return axiosInstance.patch<ProformaInvoiceCharge>(`/proforma-invoices/${piId}/charges/${cid}/`, data).then(r => r.data);
}

export function deleteCharge(piId: number, cid: number) {
  return axiosInstance.delete(`/proforma-invoices/${piId}/charges/${cid}/`);
}

// ---- Workflow ---------------------------------------------------------------

export function triggerWorkflowAction(piId: number, action: string, comment: string) {
  return axiosInstance.post<{ status: string }>(`/proforma-invoices/${piId}/workflow/`, { action, comment }).then(r => r.data);
}

// ---- Audit log --------------------------------------------------------------

export function getAuditLog(piId: number) {
  return axiosInstance.get<AuditLogEntry[]>(`/proforma-invoices/${piId}/audit-log/`).then(r => r.data);
}

// ---- Signed copy upload (FR-08.4) -------------------------------------------

export function uploadSignedCopy(piId: number, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return axiosInstance
    .post<{ signed_copy_url: string }>(`/proforma-invoices/${piId}/signed-copy/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
}

// ---- PDF download -----------------------------------------------------------

export async function downloadPiPdf(piId: number, filename: string) {
  const response = await axiosInstance.get(`/proforma-invoices/${piId}/pdf/`, {
    responseType: "blob",
  });
  const url = URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
