// API calls for the Countries reference data resource.

import api from "./axiosInstance";

export interface Country {
  id: number;
  name: string;
  iso2: string;
  iso3: string;
}

export async function listCountries(): Promise<Country[]> {
  const { data } = await api.get<Country[]>("/master-data/countries/");
  return data;
}
