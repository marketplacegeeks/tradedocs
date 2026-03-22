// API calls for report endpoints.
// Constraint #22: no component calls axios directly — only this file does.

import axiosInstance from "./axiosInstance";

// ---- R-04 Commodity Sales Report --------------------------------------------

export interface CommoditySalesRow {
  doc_type: "PI" | "CI";
  doc_number: string;
  doc_date: string | null;
  status: string;
  consignee_name: string | null;
  country_of_destination: string | null;
  hsn_code: string;
  item_code: string;
  description: string;
  quantity: string;
  uom_abbr: string | null;
  rate_usd: string;
  amount_usd: string;
  incoterms_code: string | null;
  port_of_loading_name: string | null;
}

export interface CommoditySalesParams {
  doc_type?: string;       // "PI" | "CI" | ""
  date_after?: string;
  date_before?: string;
  status?: string;
  consignee?: string;
  hsn_code?: string;
  item_code?: string;
  uom?: string;
}

export function getCommoditySalesReport(params: CommoditySalesParams) {
  const p: Record<string, string> = {};
  if (params.doc_type)  p.doc_type   = params.doc_type;
  if (params.date_after)  p.date_after  = params.date_after;
  if (params.date_before) p.date_before = params.date_before;
  if (params.status)    p.status     = params.status;
  if (params.consignee) p.consignee  = params.consignee;
  if (params.hsn_code)  p.hsn_code   = params.hsn_code;
  if (params.item_code) p.item_code  = params.item_code;
  if (params.uom)       p.uom        = params.uom;
  return axiosInstance
    .get<CommoditySalesRow[]>("/reports/commodity-sales/", { params: p })
    .then((r) => r.data);
}

// ---- R-05 Consignee-wise Business Summary -----------------------------------

export interface ConsigneeSummaryRow {
  consignee_id: number;
  consignee_name: string;
  pi_count: number;
  ci_count: number;
  total_pi_value: string;
  total_ci_value: string;
  total_value: string;
  latest_doc_date: string | null;
}

export interface ConsigneeSummaryParams {
  doc_type?: string;    // "PI" | "CI" | ""
  date_after?: string;
  date_before?: string;
  status?: string;
  consignee?: string;
}

export function getConsigneeBusinessSummary(params: ConsigneeSummaryParams) {
  const p: Record<string, string> = {};
  if (params.doc_type)    p.doc_type    = params.doc_type;
  if (params.date_after)  p.date_after  = params.date_after;
  if (params.date_before) p.date_before = params.date_before;
  if (params.status)      p.status      = params.status;
  if (params.consignee)   p.consignee   = params.consignee;
  return axiosInstance
    .get<ConsigneeSummaryRow[]>("/reports/consignee-business-summary/", { params: p })
    .then((r) => r.data);
}
