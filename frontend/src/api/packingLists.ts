// All Packing List + Commercial Invoice API calls.
// Constraint #22: no component calls axios directly.

import axiosInstance from "./axiosInstance";

// ---- Types ------------------------------------------------------------------

export interface ContainerItem {
  id: number;
  container: number;
  hsn_code: string;
  item_code: string;
  packages_kind: string;
  description: string;
  batch_details: string;
  uom: number | null;
  uom_abbr: string | null;
  quantity: string;
  net_weight: string;
  inner_packing_weight: string;
  item_gross_weight: string;
}

export interface Container {
  id: number;
  packing_list: number;
  container_ref: string;
  marks_numbers: string;
  seal_number: string;
  tare_weight: string;
  gross_weight: string;
  items: ContainerItem[];
}

export interface PackingList {
  id: number;
  pl_number: string;
  pl_date: string;
  status: string;
  proforma_invoice: number;
  pi_number_display: string | null;
  exporter: number;
  exporter_name: string | null;
  consignee: number;
  consignee_name: string | null;
  buyer: number | null;
  buyer_name: string | null;
  notify_party: number | null;
  notify_party_name: string | null;
  po_number: string;
  po_date: string | null;
  lc_number: string;
  lc_date: string | null;
  bl_number: string;
  bl_date: string | null;
  so_number: string;
  so_date: string | null;
  other_references: string;
  other_references_date: string | null;
  additional_description: string;
  pre_carriage_by: number | null;
  pre_carriage_by_name: string | null;
  place_of_receipt: number | null;
  place_of_receipt_name: string | null;
  place_of_receipt_by_pre_carrier: number | null;
  place_of_receipt_by_pre_carrier_name: string | null;
  vessel_flight_no: string;
  port_of_loading: number | null;
  port_of_loading_name: string | null;
  port_of_discharge: number | null;
  port_of_discharge_name: string | null;
  final_destination: number | null;
  final_destination_name: string | null;
  country_of_origin: number | null;
  country_of_origin_name: string | null;
  country_of_final_destination: number | null;
  country_of_final_destination_name: string | null;
  incoterms: number | null;
  incoterms_display: string | null;
  payment_terms: number | null;
  payment_terms_display: string | null;
  // CI fields
  ci_id: number | null;
  ci_number: string | null;
  ci_status: string | null;
  ci_date: string | null;
  bank_id: number | null;
  bank_display: string | null;
  fob_rate: string | null;
  freight: string | null;
  insurance: string | null;
  lc_details: string;
  // Meta
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  // Signed copy (FR-08.4)
  signed_copy_url: string | null;
  containers: Container[];
}

export interface CILineItem {
  id: number;
  ci: number;
  item_code: string;
  description: string;
  hsn_code: string;
  packages_kind: string;
  uom: number | null;
  uom_abbr: string | null;
  total_quantity: string;
  rate_usd: string;
  amount_usd: string;
}

export interface CommercialInvoice {
  id: number;
  ci_number: string;
  ci_date: string;
  status: string;
  packing_list: number;
  pl_number_display: string | null;
  bank: number | null;
  bank_display: string | null;
  bank_details: BankDetails | null;
  fob_rate: string | null;
  freight: string | null;
  insurance: string | null;
  lc_details: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  // Signed copy (FR-08.4)
  signed_copy_url: string | null;
  line_items: CILineItem[];
}

export interface BankDetails {
  beneficiary_name: string;
  bank_name: string;
  branch_name: string;
  branch_address: string;
  account_number: string;
  routing_number: string;
  swift_code: string;
  iban: string;
  intermediary_bank_name: string;
  intermediary_account_number: string;
  intermediary_swift_code: string;
  intermediary_currency: string | null;
}

// Shape matches apps/workflow/serializers.py AuditLogSerializer.
export interface AuditEntry {
  id: number;
  action: string;
  from_status: string;
  to_status: string;
  comment: string;
  performed_by_name: string;
  performed_at: string;
}

// ---- Packing List endpoints -------------------------------------------------

export function listPackingLists(params?: Record<string, string>) {
  return axiosInstance
    .get<PackingList[]>("/packing-lists/", { params })
    .then((r) => r.data);
}

export function getPackingList(id: number) {
  return axiosInstance
    .get<PackingList>(`/packing-lists/${id}/`)
    .then((r) => r.data);
}

export function createPackingList(data: Record<string, unknown>) {
  return axiosInstance
    .post<PackingList>("/packing-lists/", data)
    .then((r) => r.data);
}

export function updatePackingList(id: number, data: Record<string, unknown>) {
  return axiosInstance
    .patch<PackingList>(`/packing-lists/${id}/`, data)
    .then((r) => r.data);
}

export function deletePackingList(id: number) {
  return axiosInstance.delete(`/packing-lists/${id}/`).then((r) => r.data);
}

export function packingListWorkflow(id: number, action: string, comment = "") {
  return axiosInstance
    .post<{ status: string }>(`/packing-lists/${id}/workflow/`, { action, comment })
    .then((r) => r.data);
}

export function getPlAuditLog(id: number) {
  return axiosInstance
    .get<AuditEntry[]>(`/packing-lists/${id}/audit-log/`)
    .then((r) => r.data);
}

// Downloads the combined PL+CI PDF and triggers a browser save-as dialog.
export async function downloadPackingListPDF(id: number, filename: string) {
  const response = await axiosInstance.get(`/packing-lists/${id}/pdf/`, {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

// ---- Container endpoints ----------------------------------------------------

export function listContainers(packingListId: number) {
  return axiosInstance
    .get<Container[]>("/containers/", { params: { packing_list: packingListId } })
    .then((r) => r.data);
}

export function createContainer(data: Record<string, unknown>) {
  return axiosInstance.post<Container>("/containers/", data).then((r) => r.data);
}

export function updateContainer(id: number, data: Record<string, unknown>) {
  return axiosInstance
    .patch<Container>(`/containers/${id}/`, data)
    .then((r) => r.data);
}

export function deleteContainer(id: number) {
  return axiosInstance.delete(`/containers/${id}/`).then((r) => r.data);
}

export function copyContainer(id: number) {
  return axiosInstance.post<Container>(`/containers/${id}/copy/`).then((r) => r.data);
}

// ---- ContainerItem endpoints ------------------------------------------------

export function createContainerItem(data: Record<string, unknown>) {
  return axiosInstance
    .post<ContainerItem>("/container-items/", data)
    .then((r) => r.data);
}

export function updateContainerItem(id: number, data: Record<string, unknown>) {
  return axiosInstance
    .patch<ContainerItem>(`/container-items/${id}/`, data)
    .then((r) => r.data);
}

export function deleteContainerItem(id: number) {
  return axiosInstance.delete(`/container-items/${id}/`).then((r) => r.data);
}

// ---- Commercial Invoice endpoints -------------------------------------------

export function getCommercialInvoice(id: number) {
  return axiosInstance
    .get<CommercialInvoice>(`/commercial-invoices/${id}/`)
    .then((r) => r.data);
}

export function listCommercialInvoices(params?: Record<string, string>) {
  return axiosInstance
    .get<CommercialInvoice[]>("/commercial-invoices/", { params })
    .then((r) => r.data);
}

export function updateCILineItem(id: number, data: { rate_usd?: string; packages_kind?: string }) {
  return axiosInstance
    .patch<CILineItem>(`/ci-line-items/${id}/`, data)
    .then((r) => r.data);
}

// ---- Signed copy uploads (FR-08.4) ------------------------------------------

export function uploadPlSignedCopy(plId: number, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return axiosInstance
    .post<{ signed_copy_url: string }>(`/packing-lists/${plId}/signed-copy/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
}

export function uploadCiSignedCopy(ciId: number, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return axiosInstance
    .post<{ signed_copy_url: string }>(`/commercial-invoices/${ciId}/signed-copy/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
}
