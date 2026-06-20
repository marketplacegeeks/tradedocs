// Audit log API calls. Constraint #22: no component calls axios directly.

import axiosInstance from "./axiosInstance";

// ---- Types ------------------------------------------------------------------

export interface AuditLogEntry {
  id: number;
  document_type: string;
  document_id: number;
  document_number: string;
  action: string;
  from_status: string;
  to_status: string;
  comment: string;
  performed_by_name: string | null;
  performed_at: string;
}

export interface AuditLogListParams {
  document_id?: number;
  document_type?: string;
  performed_by?: number;
  action?: string;
  performed_at_after?: string; // ISO date string YYYY-MM-DD
  performed_at_before?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface PaginatedAuditLogResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: AuditLogEntry[];
}

// ---- API functions ----------------------------------------------------------

/** Fetch a paginated, filtered list of audit log entries. */
export async function fetchAuditLogs(
  params: AuditLogListParams = {}
): Promise<PaginatedAuditLogResponse> {
  const response = await axiosInstance.get<PaginatedAuditLogResponse>(
    "/audit-logs/",
    { params }
  );
  return response.data;
}

/** Fetch a single audit log entry by ID. */
export async function fetchAuditLogDetail(id: number): Promise<AuditLogEntry> {
  const response = await axiosInstance.get<AuditLogEntry>(
    `/audit-logs/${id}/`
  );
  return response.data;
}
