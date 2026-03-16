// Shared Axios instance used by all API files.
// Attaches the JWT access token to every request automatically.
// If the token has expired, it calls the refresh endpoint and retries once.

import axios from "axios";

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000/api/v1",
  headers: { "Content-Type": "application/json" },
});

// Attach the stored access token to every outgoing request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the server returns 401, try to refresh the token once, then retry.
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retried) {
      original._retried = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(
            `${original.baseURL ?? ""}/auth/token/refresh/`,
            { refresh: refreshToken }
          );
          localStorage.setItem("access_token", data.access as string);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          // Refresh failed — clear tokens so the app redirects to login.
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("auth_user");
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
