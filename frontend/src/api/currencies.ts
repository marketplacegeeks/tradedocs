// All API calls for the Currency master data resource.
// Constraint #22: no component calls axios directly — only this file does.

import api from "./axiosInstance";

// ---- Types ----------------------------------------------------------------

export interface Currency {
  id: number;
  code: string;
  name: string;
}

// ---- API functions --------------------------------------------------------

/** Fetch all currencies. Used to populate the currency dropdown on the Bank form. */
export async function listCurrencies(): Promise<Currency[]> {
  const { data } = await api.get<Currency[]>("/master-data/currencies/");
  return data;
}
