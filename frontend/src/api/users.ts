// All API calls for the User Management resource.
// Constraint #22: no component calls axios directly — only this file does.

import api from "./axiosInstance";

// ---- Types ----------------------------------------------------------------

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  is_active: boolean;
  date_joined: string;
  phone_country_code: string;
  phone_number: string;
}

export interface UserCreatePayload {
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  password: string;
  phone_country_code?: string;
  phone_number?: string;
}

export interface UserUpdatePayload {
  role?: string;
  is_active?: boolean;
  phone_country_code?: string;
  phone_number?: string;
}

// ---- API functions --------------------------------------------------------

/** Fetch all users (active and inactive). Company Admin only. */
export async function listUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>("/users/");
  return data;
}

/** Create (invite) a new user with a set password. Company Admin only. */
export async function createUser(payload: UserCreatePayload): Promise<User> {
  const { data } = await api.post<User>("/users/", payload);
  return data;
}

/** Update a user's role or active status via PATCH. Company Admin only. */
export async function updateUser(id: number, payload: UserUpdatePayload): Promise<User> {
  const { data } = await api.patch<User>(`/users/${id}/`, payload);
  return data;
}

/** Reset a user's password. Company Admin and Super Admin only. */
export async function resetPassword(userId: number, newPassword: string): Promise<void> {
  await api.post(`/users/${userId}/reset-password/`, { new_password: newPassword });
}
