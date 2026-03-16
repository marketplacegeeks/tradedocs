// All API calls for the T&C Template master data resource.
// Constraint #22: no component calls axios directly — only this file does.

import api from "./axiosInstance";

// ---- Types ----------------------------------------------------------------

export interface TCTemplate {
  id: number;
  name: string;
  body: string;                      // rich HTML string from TipTap
  organisations: number[];           // array of Organisation IDs
  organisation_names: string[];      // read-only, returned by API
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TCTemplatePayload {
  name: string;
  body: string;
  organisations: number[];           // array of Organisation IDs
}

// ---- API functions --------------------------------------------------------

/** Fetch all active T&C templates. Used for the list page and document dropdowns. */
export async function listTCTemplates(): Promise<TCTemplate[]> {
  const { data } = await api.get<TCTemplate[]>("/master-data/tc-templates/");
  return data;
}

/** Fetch a single T&C template by ID. */
export async function getTCTemplate(id: number): Promise<TCTemplate> {
  const { data } = await api.get<TCTemplate>(`/master-data/tc-templates/${id}/`);
  return data;
}

/** Create a new T&C template. */
export async function createTCTemplate(payload: TCTemplatePayload): Promise<TCTemplate> {
  const { data } = await api.post<TCTemplate>("/master-data/tc-templates/", payload);
  return data;
}

/** Update an existing T&C template via PATCH (partial update). */
export async function updateTCTemplate(
  id: number,
  payload: Partial<TCTemplatePayload>
): Promise<TCTemplate> {
  const { data } = await api.patch<TCTemplate>(`/master-data/tc-templates/${id}/`, payload);
  return data;
}

/** Soft-delete a T&C template (sets is_active=False on the backend). */
export async function deleteTCTemplate(id: number): Promise<void> {
  await api.delete(`/master-data/tc-templates/${id}/`);
}
