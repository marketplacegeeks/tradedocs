// All API calls for the Currency master data resource.
// Constraint #22: no component calls axios directly — only this file does.

import api from "./axiosInstance";

// ---- Types ----------------------------------------------------------------

export interface Currency {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
}

export interface CurrencyPayload {
  code: string;
  name: string;
}

// ---- API functions --------------------------------------------------------

/** Fetch all active currencies. Used to populate currency dropdowns. */
export async function listCurrencies(): Promise<Currency[]> {
  const { data } = await api.get<Currency[]>("/master-data/currencies/");
  return data;
}

export async function createCurrency(payload: CurrencyPayload): Promise<Currency> {
  const { data } = await api.post<Currency>("/master-data/currencies/", payload);
  return data;
}

export async function updateCurrency(id: number, payload: Partial<CurrencyPayload>): Promise<Currency> {
  const { data } = await api.patch<Currency>(`/master-data/currencies/${id}/`, payload);
  return data;
}

export async function deleteCurrency(id: number): Promise<void> {
  await api.delete(`/master-data/currencies/${id}/`);
}
