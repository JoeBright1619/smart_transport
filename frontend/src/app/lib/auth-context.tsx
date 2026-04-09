// Authentication context for user management
import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from './types';
import { mockUsers } from './mock-data';

type StoredRegisteredUser = User & { password: string };

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (payload: {
    fullName: string;
    email: string;
    password: string;
    role?: User['role'];
    phone?: string;
    company?: string;
  }) => Promise<{ ok: true } | { ok: false; reason: 'email_taken' }>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const REGISTERED_USERS_STORAGE_KEY = 'transport-registered-users';

function readRegisteredUsers(): StoredRegisteredUser[] {
  const raw = localStorage.getItem(REGISTERED_USERS_STORAGE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed as StoredRegisteredUser[];
  } catch {
    return [];
  }
}

function writeRegisteredUsers(users: StoredRegisteredUser[]) {
  localStorage.setItem(REGISTERED_USERS_STORAGE_KEY, JSON.stringify(users));
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // Check for stored user on mount
    const storedUser = localStorage.getItem('transport-user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    // Mock authentication - in production, this would call an API
    const foundUser = mockUsers.find(u => u.email === email);
    if (foundUser && password === 'password') {
      setUser(foundUser);
      localStorage.setItem('transport-user', JSON.stringify(foundUser));
      return true;
    }

     const registeredUsers = readRegisteredUsers();
     const foundRegisteredUser = registeredUsers.find(u => u.email === email);
     if (foundRegisteredUser && foundRegisteredUser.password === password) {
       // Strip password before storing current session user
       const { password: _password, ...safeUser } = foundRegisteredUser;
       setUser(safeUser);
       localStorage.setItem('transport-user', JSON.stringify(safeUser));
       return true;
     }

    return false;
  };

  const register: AuthContextType['register'] = async (payload) => {
    const normalizedEmail = payload.email.trim().toLowerCase();
    const fullName = payload.fullName.trim();

    const emailTaken =
      mockUsers.some(u => u.email.toLowerCase() === normalizedEmail) ||
      readRegisteredUsers().some(u => u.email.toLowerCase() === normalizedEmail);

    if (emailTaken) return { ok: false, reason: 'email_taken' };

    const newUser: StoredRegisteredUser = {
      id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}`,
      email: normalizedEmail,
      fullName,
      role: payload.role ?? 'operator',
      phone: payload.phone?.trim() || undefined,
      company: payload.company?.trim() || undefined,
      password: payload.password,
    };

    const registeredUsers = readRegisteredUsers();
    writeRegisteredUsers([newUser, ...registeredUsers]);
    return { ok: true };
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('transport-user');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
