// Bulk workflow API calls. Constraint #22: no component calls axios directly.

import axiosInstance from "./axiosInstance";

// ---- Types ------------------------------------------------------------------

export interface BulkWorkflowRequest {
  document_ids: number[];
  action: string; // Use DOCUMENT_STATUS values from constants.ts for action strings
  comment?: string;
}

export interface BulkWorkflowFailure {
  id: number;
  reason: string;
}

export interface BulkWorkflowResponse {
  succeeded: number[];
  failed: BulkWorkflowFailure[];
}

// ---- API functions ----------------------------------------------------------

/** Bulk workflow action for Proforma Invoices. */
export async function bulkWorkflowPI(
  body: BulkWorkflowRequest
): Promise<BulkWorkflowResponse> {
  const response = await axiosInstance.post<BulkWorkflowResponse>(
    "/proforma-invoices/bulk-workflow/",
    body
  );
  return response.data;
}

/** Bulk workflow action for Packing Lists (also transitions linked CI). */
export async function bulkWorkflowPL(
  body: BulkWorkflowRequest
): Promise<BulkWorkflowResponse> {
  const response = await axiosInstance.post<BulkWorkflowResponse>(
    "/packing-lists/bulk-workflow/",
    body
  );
  return response.data;
}

/** Bulk workflow action for Commercial Invoices. */
export async function bulkWorkflowCI(
  body: BulkWorkflowRequest
): Promise<BulkWorkflowResponse> {
  const response = await axiosInstance.post<BulkWorkflowResponse>(
    "/commercial-invoices/bulk-workflow/",
    body
  );
  return response.data;
}
