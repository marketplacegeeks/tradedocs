// Dashboard summary API. Constraint #22: no component calls axios directly.

import api from "./axiosInstance";

export interface DashboardCounts {
  proforma_invoices: number;
  packing_lists: number;
  purchase_orders: number;
  pending_approvals: number;
}

export interface ActivityEntry {
  id: number;
  document_type: string;
  document_id: number;
  document_number: string;
  action: string;
  action_label: string;
  to_status: string;
  performed_by_name: string;
  performed_at: string; // ISO 8601
  url_prefix: string;
}

export interface DashboardData {
  counts: DashboardCounts;
  recent_activity: ActivityEntry[];
}

export async function getDashboardData(): Promise<DashboardData> {
  const { data } = await api.get<DashboardData>("/dashboard/");
  return data;
}
