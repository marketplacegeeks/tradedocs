// All API calls for the Bank master data resource.
// Constraint #22: no component calls axios directly — only this file does.

import api from "./axiosInstance";

// ---- Types ----------------------------------------------------------------

export interface Bank {
  id: number;
  nickname: string;
  beneficiary_name: string;
  bank_name: string;
  bank_country: number;       // Country ID
  bank_country_name: string;  // read-only, returned by API
  branch_name: string;
  branch_address: string;
  account_number: string;
  account_type: string;
  currency: number;           // Currency ID
  currency_code: string;      // read-only, returned by API
  currency_name: string;      // read-only, returned by API
  swift_code: string;
  iban: string;
  routing_number: string;
}

export interface BankPayload {
  nickname: string;
  beneficiary_name: string;
  bank_name: string;
  bank_country: number;
  branch_name: string;
  branch_address?: string;
  account_number: string;
  account_type: string;
  currency: number;
  swift_code?: string;
  iban?: string;
  routing_number?: string;
}

// ---- API functions --------------------------------------------------------

/** Fetch all bank accounts. Used for the Bank list page and PI/CI dropdowns. */
export async function listBanks(): Promise<Bank[]> {
  const { data } = await api.get<Bank[]>("/master-data/banks/");
  return data;
}

/** Fetch a single bank account by ID. */
export async function getBank(id: number): Promise<Bank> {
  const { data } = await api.get<Bank>(`/master-data/banks/${id}/`);
  return data;
}

/** Create a new bank account. */
export async function createBank(payload: BankPayload): Promise<Bank> {
  const { data } = await api.post<Bank>("/master-data/banks/", payload);
  return data;
}

/** Update an existing bank account via PATCH (partial update). */
export async function updateBank(id: number, payload: Partial<BankPayload>): Promise<Bank> {
  const { data } = await api.patch<Bank>(`/master-data/banks/${id}/`, payload);
  return data;
}
