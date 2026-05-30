import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import {
  ApiError,
  clearStoredToken,
  getStoredToken,
  refreshAccessToken,
  setStoredToken,
} from './api-client';
import type { AuthUserSummary } from './api-types';
import type { User } from './types';
import * as authService from '../services/auth.service';

type JwtPayload = {
  userId?: string;
  tenantId?: string | null;
  tenantName?: string | null;
  tenantEmail?: string | null;
  tenantAddress?: string | null;
  tenantPhone?: string | null;
  tenantLogoPath?: string | null;
  role?: User['role'];
  email?: string | null;
  full_name?: string | null;
  fullName?: string | null;
  exp?: number;
};

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (payload: {
    companyName: string;
    contactEmail: string;
    adminFullName: string;
    adminEmail: string;
    adminPhone?: string;
    password: string;
  }) => Promise<{ ok: true } | { ok: false; reason: 'email_taken' }>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isInitializing: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const LEGACY_USER_STORAGE_KEY = 'transport-user';
const LEGACY_REGISTERED_USERS_STORAGE_KEY = 'transport-registered-users';

function removeLegacyAuthStorage(): void {
  localStorage.removeItem(LEGACY_USER_STORAGE_KEY);
  localStorage.removeItem(LEGACY_REGISTERED_USERS_STORAGE_KEY);
}

function decodeJwt(token: string): JwtPayload | null {
  const [, payload] = token.split('.');

  if (!payload) return null;

  try {
    const normalizedPayload = payload.replace(/-/g, '+').replace(/_/g, '/');
    const paddedPayload = normalizedPayload.padEnd(
      normalizedPayload.length + ((4 - (normalizedPayload.length % 4)) % 4),
      '=',
    );

    return JSON.parse(atob(paddedPayload)) as JwtPayload;
  } catch {
    return null;
  }
}

function isExpired(payload: JwtPayload): boolean {
  if (!payload.exp) return false;
  return payload.exp * 1000 <= Date.now();
}

function userFromAuthSummary(summary: AuthUserSummary): User {
  return {
    id: summary.id,
    email: summary.email ?? '',
    fullName: summary.fullName ?? summary.email ?? 'User',
    role: summary.role,
    company: summary.tenantId ?? undefined,
    tenantName: summary.tenantName ?? undefined,
    tenantEmail: summary.tenantEmail ?? undefined,
    tenantAddress: summary.tenantAddress ?? undefined,
    tenantPhone: summary.tenantPhone ?? undefined,
    tenantLogoPath: summary.tenantLogoPath ?? undefined,
  };
}

function userFromTokenPayload(payload: JwtPayload): User | null {
  if (!payload.userId || !payload.role) return null;

  const email = payload.email ?? '';

  return {
    id: payload.userId,
    email,
    fullName: payload.full_name ?? payload.fullName ?? (email || 'User'),
    role: payload.role,
    company: payload.tenantId ?? undefined,
    tenantName: payload.tenantName ?? undefined,
    tenantEmail: payload.tenantEmail ?? undefined,
    tenantAddress: payload.tenantAddress ?? undefined,
    tenantPhone: payload.tenantPhone ?? undefined,
    tenantLogoPath: payload.tenantLogoPath ?? undefined,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    removeLegacyAuthStorage();

    let cancelled = false;

    async function bootstrapSession() {
      const token = getStoredToken();
      const payload = token ? decodeJwt(token) : null;

      if (token && payload && !isExpired(payload)) {
        const decodedUser = userFromTokenPayload(payload);
        if (decodedUser) {
          setUser(decodedUser);
          setIsInitializing(false);
          return;
        }
      }

      try {
        const accessToken = await refreshAccessToken();
        if (cancelled) return;

        const refreshedUser = userFromTokenPayload(decodeJwt(accessToken) ?? {});
        if (refreshedUser) {
          setUser(refreshedUser);
        } else {
          clearStoredToken();
        }
      } catch {
        if (cancelled) return;
        clearStoredToken();
        setUser(null);
      } finally {
        if (!cancelled) {
          setIsInitializing(false);
        }
      }
    }

    void bootstrapSession();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await authService.login(email, password);
      setStoredToken(response.accessToken);
      setUser(userFromAuthSummary(response.user));
      return true;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        return false;
      }

      throw error;
    }
  };

  const register: AuthContextType['register'] = async (payload) => {
    try {
      await authService.registerTenant({
        companyName: payload.companyName,
        contactEmail: payload.contactEmail,
        adminFullName: payload.adminFullName,
        adminEmail: payload.adminEmail,
        adminPhone: payload.adminPhone,
        password: payload.password,
      });

      return { ok: true };
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        return { ok: false, reason: 'email_taken' };
      }

      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } finally {
      clearStoredToken();
      setUser(null);
    }
  };

  const value = useMemo(
    () => ({
      user,
      login,
      register,
      logout,
      isAuthenticated: !!user,
      isInitializing,
    }),
    [user, isInitializing],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
