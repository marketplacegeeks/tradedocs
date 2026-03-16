// All API calls for authentication.
// Constraint #22: no component calls axios directly — only this file does.

import api from "./axiosInstance";

// ---- Types ----------------------------------------------------------------

export interface AuthUser {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
}

interface MeResponse {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
}

// ---- API functions --------------------------------------------------------

/**
 * Log in with email + password. Returns the user profile and both JWT tokens.
 * Calls /auth/login/ for tokens, then /auth/me/ for the user profile.
 */
export async function loginUser(
  email: string,
  password: string
): Promise<{ user: AuthUser; accessToken: string; refreshToken: string }> {
  const { data: tokens } = await api.post<LoginResponse>("/auth/login/", {
    email,
    password,
  });

  // Store tokens before calling /me/ so the request interceptor can attach them.
  localStorage.setItem("access_token", tokens.access);
  localStorage.setItem("refresh_token", tokens.refresh);

  const { data: me } = await api.get<MeResponse>("/auth/me/");

  const user: AuthUser = {
    id: me.id,
    email: me.email,
    firstName: me.first_name,
    lastName: me.last_name,
    role: me.role,
  };

  return { user, accessToken: tokens.access, refreshToken: tokens.refresh };
}

/**
 * Log out by blacklisting the refresh token server-side.
 * Clears localStorage regardless of whether the server call succeeds.
 */
export async function logoutUser(): Promise<void> {
  const refreshToken = localStorage.getItem("refresh_token");
  try {
    if (refreshToken) {
      await api.post("/auth/logout/", { refresh: refreshToken });
    }
  } finally {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("auth_user");
  }
}
