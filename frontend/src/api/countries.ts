// API calls for the Countries reference data resource.

import api from "./axiosInstance";

export interface Country {
  id: number;
  name: string;
  iso2: string;
  iso3: string;
  is_active: boolean;
}

export interface CountryPayload {
  name: string;
  iso2: string;
  iso3: string;
}

export async function listCountries(): Promise<Country[]> {
  const { data } = await api.get<Country[]>("/master-data/countries/");
  return data;
}

export async function createCountry(payload: CountryPayload): Promise<Country> {
  const { data } = await api.post<Country>("/master-data/countries/", payload);
  return data;
}

export async function updateCountry(id: number, payload: Partial<CountryPayload>): Promise<Country> {
  const { data } = await api.patch<Country>(`/master-data/countries/${id}/`, payload);
  return data;
}

export async function deleteCountry(id: number): Promise<void> {
  await api.delete(`/master-data/countries/${id}/`);
}
