// All API calls for the Organisation master data resource.
// Constraint #22: no component calls axios directly — only this file does.

import api from "./axiosInstance";
import type { OrgTag } from "../utils/constants";

// ---- Types ----------------------------------------------------------------

export interface OrgAddress {
  id?: number;
  address_type: string;
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  pin?: string;
  country: number;       // Country ID
  country_name?: string; // read-only, returned by API
  email: string;
  contact_name: string;
  phone_country_code?: string;
  phone_number?: string;
  iec_code?: string;
  tax_type?: string;
  tax_code?: string;
}

export interface OrgTag {
  id?: number;
  tag: string;
}

export interface Organisation {
  id: number;
  name: string;
  is_active: boolean;
  addresses: OrgAddress[];
  tags: OrgTag[];
  created_at: string;
  updated_at: string;
}

export interface OrganisationPayload {
  name: string;
  is_active?: boolean;
  addresses: OrgAddress[];
  tags: OrgTag[];
}

// ---- API functions --------------------------------------------------------

/** Fetch the list of active organisations. Pass a tag to filter (e.g. "EXPORTER"). */
export async function listOrganisations(tag?: string): Promise<Organisation[]> {
  const params: Record<string, string> = {};
  if (tag) params.tag = tag;
  const { data } = await api.get<Organisation[]>("/master-data/organisations/", { params });
  return data;
}

/** Fetch a single organisation by ID, including all nested addresses/tags/tax codes. */
export async function getOrganisation(id: number): Promise<Organisation> {
  const { data } = await api.get<Organisation>(`/master-data/organisations/${id}/`);
  return data;
}

/** Create a new organisation with its nested sub-records in one request. */
export async function createOrganisation(payload: OrganisationPayload): Promise<Organisation> {
  const { data } = await api.post<Organisation>("/master-data/organisations/", payload);
  return data;
}

/** Update an organisation. Use PATCH for partial updates (e.g. deactivating). */
export async function updateOrganisation(
  id: number,
  payload: Partial<OrganisationPayload>
): Promise<Organisation> {
  const { data } = await api.patch<Organisation>(`/master-data/organisations/${id}/`, payload);
  return data;
}

/** Add a new address to an existing organisation. */
export async function addAddress(orgId: number, payload: OrgAddress): Promise<OrgAddress> {
  const { data } = await api.post<OrgAddress>(
    `/master-data/organisations/${orgId}/addresses/`,
    payload
  );
  return data;
}

/** Update an existing address. */
export async function updateAddress(
  orgId: number,
  addressId: number,
  payload: Partial<OrgAddress>
): Promise<OrgAddress> {
  const { data } = await api.patch<OrgAddress>(
    `/master-data/organisations/${orgId}/addresses/${addressId}/`,
    payload
  );
  return data;
}

/** Delete an address. The API will reject this if it is the organisation's only address. */
export async function deleteAddress(orgId: number, addressId: number): Promise<void> {
  await api.delete(`/master-data/organisations/${orgId}/addresses/${addressId}/`);
}
