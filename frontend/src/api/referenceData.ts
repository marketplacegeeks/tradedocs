// API calls for all FR-06 reference data entities (except Countries, which are in countries.ts).
// Constraint #22: no component calls axios directly — only api files do.

import api from "./axiosInstance";

// ---- Shared soft-delete response (all delete calls return 204 No Content) --

// ---- Incoterms ---------------------------------------------------------------

export interface Incoterm {
  id: number;
  code: string;
  full_name: string;
  description: string;
  is_active: boolean;
}
export interface IncotermPayload { code: string; full_name: string; description?: string; }

export async function listIncoterms(): Promise<Incoterm[]> {
  const { data } = await api.get<Incoterm[]>("/master-data/incoterms/");
  return data;
}
export async function createIncoterm(payload: IncotermPayload): Promise<Incoterm> {
  const { data } = await api.post<Incoterm>("/master-data/incoterms/", payload);
  return data;
}
export async function updateIncoterm(id: number, payload: Partial<IncotermPayload>): Promise<Incoterm> {
  const { data } = await api.patch<Incoterm>(`/master-data/incoterms/${id}/`, payload);
  return data;
}
export async function deleteIncoterm(id: number): Promise<void> {
  await api.delete(`/master-data/incoterms/${id}/`);
}

// ---- Units of Measurement ---------------------------------------------------

export interface UOM {
  id: number;
  name: string;
  abbreviation: string;
  is_active: boolean;
}
export interface UOMPayload { name: string; abbreviation: string; }

export async function listUOMs(): Promise<UOM[]> {
  const { data } = await api.get<UOM[]>("/master-data/uom/");
  return data;
}
export async function createUOM(payload: UOMPayload): Promise<UOM> {
  const { data } = await api.post<UOM>("/master-data/uom/", payload);
  return data;
}
export async function updateUOM(id: number, payload: Partial<UOMPayload>): Promise<UOM> {
  const { data } = await api.patch<UOM>(`/master-data/uom/${id}/`, payload);
  return data;
}
export async function deleteUOM(id: number): Promise<void> {
  await api.delete(`/master-data/uom/${id}/`);
}

// ---- Payment Terms ----------------------------------------------------------

export interface PaymentTerm {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
}
export interface PaymentTermPayload { name: string; description?: string; }

export async function listPaymentTerms(): Promise<PaymentTerm[]> {
  const { data } = await api.get<PaymentTerm[]>("/master-data/payment-terms/");
  return data;
}
export async function createPaymentTerm(payload: PaymentTermPayload): Promise<PaymentTerm> {
  const { data } = await api.post<PaymentTerm>("/master-data/payment-terms/", payload);
  return data;
}
export async function updatePaymentTerm(id: number, payload: Partial<PaymentTermPayload>): Promise<PaymentTerm> {
  const { data } = await api.patch<PaymentTerm>(`/master-data/payment-terms/${id}/`, payload);
  return data;
}
export async function deletePaymentTerm(id: number): Promise<void> {
  await api.delete(`/master-data/payment-terms/${id}/`);
}

// ---- Ports ------------------------------------------------------------------

export interface Port {
  id: number;
  name: string;
  code: string;
  country: number;
  country_name: string;
  is_active: boolean;
}
export interface PortPayload { name: string; code: string; country: number; }

export async function listPorts(): Promise<Port[]> {
  const { data } = await api.get<Port[]>("/master-data/ports/");
  return data;
}
export async function createPort(payload: PortPayload): Promise<Port> {
  const { data } = await api.post<Port>("/master-data/ports/", payload);
  return data;
}
export async function updatePort(id: number, payload: Partial<PortPayload>): Promise<Port> {
  const { data } = await api.patch<Port>(`/master-data/ports/${id}/`, payload);
  return data;
}
export async function deletePort(id: number): Promise<void> {
  await api.delete(`/master-data/ports/${id}/`);
}

// ---- Locations --------------------------------------------------------------

export interface Location {
  id: number;
  name: string;
  country: number;
  country_name: string;
  is_active: boolean;
}
export interface LocationPayload { name: string; country: number; }

export async function listLocations(): Promise<Location[]> {
  const { data } = await api.get<Location[]>("/master-data/locations/");
  return data;
}
export async function createLocation(payload: LocationPayload): Promise<Location> {
  const { data } = await api.post<Location>("/master-data/locations/", payload);
  return data;
}
export async function updateLocation(id: number, payload: Partial<LocationPayload>): Promise<Location> {
  const { data } = await api.patch<Location>(`/master-data/locations/${id}/`, payload);
  return data;
}
export async function deleteLocation(id: number): Promise<void> {
  await api.delete(`/master-data/locations/${id}/`);
}

// ---- Pre-Carriage By --------------------------------------------------------

export interface PreCarriageBy {
  id: number;
  name: string;
  is_active: boolean;
}
export interface PreCarriageByPayload { name: string; }

export async function listPreCarriageBy(): Promise<PreCarriageBy[]> {
  const { data } = await api.get<PreCarriageBy[]>("/master-data/pre-carriage/");
  return data;
}
export async function createPreCarriageBy(payload: PreCarriageByPayload): Promise<PreCarriageBy> {
  const { data } = await api.post<PreCarriageBy>("/master-data/pre-carriage/", payload);
  return data;
}
export async function updatePreCarriageBy(id: number, payload: Partial<PreCarriageByPayload>): Promise<PreCarriageBy> {
  const { data } = await api.patch<PreCarriageBy>(`/master-data/pre-carriage/${id}/`, payload);
  return data;
}
export async function deletePreCarriageBy(id: number): Promise<void> {
  await api.delete(`/master-data/pre-carriage/${id}/`);
}
