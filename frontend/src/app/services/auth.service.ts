import { apiClient } from '../lib/api-client';
import type {
  ApiResponse,
  RefreshTokenResponse,
  RegisterResponse,
  TokenResponse,
} from '../lib/api-types';

export type RegisterTenantPayload = {
  companyName: string;
  contactEmail: string;
  adminFullName: string;
  adminEmail: string;
  adminPhone?: string;
  password: string;
};

export async function registerTenant(payload: RegisterTenantPayload): Promise<RegisterResponse> {
  const response = await apiClient.post<ApiResponse<RegisterResponse>>('/auth/register', {
    company_name: payload.companyName,
    contact_email: payload.contactEmail,
    admin_full_name: payload.adminFullName,
    admin_email: payload.adminEmail,
    admin_phone: payload.adminPhone,
    password: payload.password,
  });

  return response.data.data;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await apiClient.post<ApiResponse<TokenResponse>>('/auth/login', {
    email,
    password,
  });

  return response.data.data;
}

export async function refresh(): Promise<RefreshTokenResponse> {
  const response = await apiClient.post<ApiResponse<RefreshTokenResponse>>('/auth/refresh');

  return response.data.data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout');
}
