// Stores the current user identity and role in memory after login.
// Any component can call useAuth() to read who is logged in.

import React, { createContext, useContext, useState } from "react";
import type { Role } from "../utils/constants";

interface AuthUser {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  role: Role;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (user: AuthUser, accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    // Restore the user from localStorage so a page refresh doesn't log them out.
    const stored = localStorage.getItem("auth_user");
    return stored ? (JSON.parse(stored) as AuthUser) : null;
  });

  function login(authUser: AuthUser, accessToken: string, refreshToken: string) {
    localStorage.setItem("auth_user", JSON.stringify(authUser));
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    setUser(authUser);
  }

  function logout() {
    localStorage.removeItem("auth_user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
