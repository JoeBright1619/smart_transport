// Type definitions for the transport system

export type UserRole = 'superadmin' | 'admin' | 'operator' | 'dispatcher' | 'passenger';

export interface User {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  phone?: string;
  company?: string;
  tenantName?: string;
}
