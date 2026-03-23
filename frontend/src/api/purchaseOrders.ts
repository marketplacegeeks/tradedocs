// All API calls for the Purchase Order resource.
// Constraint #22: no component calls axios directly — only this file does.

import api from "./axiosInstance";

// ---- Types ------------------------------------------------------------------

export interface PurchaseOrderLineItem {
  id: number;
  description: string;
  item_code: string;
  hsn_code: string;
  manufacturer: string;
  uom: number;
  quantity: string;
  packaging_description: string;
  unit_price: string;
  taxable_amount: string;
  igst_percent: string | null;
  igst_amount: string | null;
  cgst_percent: string | null;
  cgst_amount: string | null;
  sgst_percent: string | null;
  sgst_amount: string | null;
  total_tax: string;
  total: string;
  sort_order: number;
}

export interface PurchaseOrder {
  id: number;
  po_number: string;
  po_date: string;
  customer_no: string;
  vendor: number;
  vendor_name: string;
  buyer: number | null;
  buyer_name: string | null;
  internal_contact: number;
  internal_contact_name: string;
  internal_contact_email: string;
  internal_contact_phone: string;
  delivery_address: number;
  bank: number | null;
  currency: number;
  currency_code: string;
  payment_terms: number | null;
  country_of_origin: number | null;
  transaction_type: string;
  time_of_delivery: string;
  tc_template: number | null;
  tc_content: string;
  line_item_remarks: string;
  remarks: string;
  status: string;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  line_items: PurchaseOrderLineItem[];
  total: string;
  payment_terms_name: string | null;
  country_of_origin_name: string | null;
  bank_name: string | null;
  delivery_address_detail: string;
  // Report aggregate fields (R-06)
  line_item_count: number;
  total_taxable: string;
  total_igst: string;
  total_cgst: string;
  total_sgst: string;
  total_tax_amount: string;
  delivery_city_country: string;
}

export interface PurchaseOrderCreatePayload {
  po_date: string;
  customer_no?: string;
  vendor: number;
  buyer?: number | null;
  internal_contact: number;
  delivery_address: number;
  bank?: number | null;
  currency: number;
  payment_terms?: number | null;
  country_of_origin?: number | null;
  transaction_type: string;
  time_of_delivery?: string;
  tc_template?: number | null;
  tc_content?: string;
  line_item_remarks?: string;
  remarks?: string;
}

export interface PurchaseOrderUpdatePayload extends Partial<PurchaseOrderCreatePayload> {}

export interface LineItemPayload {
  description: string;
  item_code?: string;
  hsn_code?: string;
  manufacturer?: string;
  uom: number;
  quantity: string;
  packaging_description?: string;
  unit_price: string;
  igst_percent?: string | null;
  cgst_percent?: string | null;
  sgst_percent?: string | null;
  sort_order?: number;
}

export interface PurchaseOrderFilters {
  status?: string;
  created_by?: number;
  vendor?: number;
  buyer?: number;
  currency?: number;
  transaction_type?: string;
  internal_contact?: number;
  country_of_origin?: number;
  po_number?: string;
  po_date_after?: string;
  po_date_before?: string;
}

// ---- API functions ----------------------------------------------------------

/** Fetch all purchase orders, optionally filtered. */
export async function listPurchaseOrders(filters: PurchaseOrderFilters = {}): Promise<PurchaseOrder[]> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.created_by) params.set("created_by", String(filters.created_by));
  if (filters.vendor) params.set("vendor", String(filters.vendor));
  if (filters.po_number) params.set("po_number", filters.po_number);
  const { data } = await api.get<PurchaseOrder[]>(`/purchase-orders/?${params.toString()}`);
  return data;
}

/** Fetch purchase orders for R-06 report with full filter support. */
export async function listPurchaseOrdersReport(filters: PurchaseOrderFilters = {}): Promise<PurchaseOrder[]> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.vendor) params.set("vendor", String(filters.vendor));
  if (filters.buyer) params.set("buyer", String(filters.buyer));
  if (filters.currency) params.set("currency", String(filters.currency));
  if (filters.transaction_type) params.set("transaction_type", filters.transaction_type);
  if (filters.internal_contact) params.set("internal_contact", String(filters.internal_contact));
  if (filters.country_of_origin) params.set("country_of_origin", String(filters.country_of_origin));
  if (filters.po_date_after) params.set("po_date_after", filters.po_date_after);
  if (filters.po_date_before) params.set("po_date_before", filters.po_date_before);
  const { data } = await api.get<PurchaseOrder[]>(`/purchase-orders/?${params.toString()}`);
  return data;
}

/** Fetch a single PO with full detail including nested line items. */
export async function getPurchaseOrder(id: number): Promise<PurchaseOrder> {
  const { data } = await api.get<PurchaseOrder>(`/purchase-orders/${id}/`);
  return data;
}

/** Create a new Purchase Order. Returns the created record with auto-generated po_number. */
export async function createPurchaseOrder(payload: PurchaseOrderCreatePayload): Promise<PurchaseOrder> {
  const { data } = await api.post<PurchaseOrder>("/purchase-orders/", payload);
  return data;
}

/** Update header fields of an existing PO (only in DRAFT or REWORK). */
export async function updatePurchaseOrder(id: number, payload: PurchaseOrderUpdatePayload): Promise<PurchaseOrder> {
  const { data } = await api.patch<PurchaseOrder>(`/purchase-orders/${id}/`, payload);
  return data;
}

/** Perform a workflow action (SUBMIT, APPROVE, REWORK, PERMANENTLY_REJECT). */
export async function workflowPurchaseOrder(
  id: number,
  action: string,
  comment = ""
): Promise<{ status: string }> {
  const { data } = await api.post<{ status: string }>(`/purchase-orders/${id}/workflow/`, { action, comment });
  return data;
}

/** Fetch the audit log for a PO. */
export async function getPurchaseOrderAuditLog(id: number): Promise<unknown[]> {
  const { data } = await api.get<unknown[]>(`/purchase-orders/${id}/audit-log/`);
  return data;
}

/** Stream the PO as a PDF. Returns a blob URL. */
export function getPurchaseOrderPdfUrl(id: number): string {
  return `/api/v1/purchase-orders/${id}/pdf/`;
}

/** Download the PO PDF and trigger a browser file save. */
export async function downloadPurchaseOrderPdf(poId: number, filename: string): Promise<void> {
  const response = await api.get(`/purchase-orders/${poId}/pdf/`, { responseType: "blob" });
  const url = URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

// ---- Line item functions ----------------------------------------------------

export async function listLineItems(poId: number): Promise<PurchaseOrderLineItem[]> {
  const { data } = await api.get<PurchaseOrderLineItem[]>(`/purchase-orders/${poId}/line-items/`);
  return data;
}

export async function createLineItem(poId: number, payload: LineItemPayload): Promise<PurchaseOrderLineItem> {
  const { data } = await api.post<PurchaseOrderLineItem>(`/purchase-orders/${poId}/line-items/`, payload);
  return data;
}

export async function updateLineItem(
  poId: number,
  lid: number,
  payload: Partial<LineItemPayload>
): Promise<PurchaseOrderLineItem> {
  const { data } = await api.patch<PurchaseOrderLineItem>(`/purchase-orders/${poId}/line-items/${lid}/`, payload);
  return data;
}

export async function deleteLineItem(poId: number, lid: number): Promise<void> {
  await api.delete(`/purchase-orders/${poId}/line-items/${lid}/`);
}

// Super Admin only — permanently removes the PO from the database.
export async function hardDeletePurchaseOrder(id: number): Promise<void> {
  await api.delete(`/purchase-orders/${id}/hard-delete/`);
}
