import { apiClient } from '../lib/api-client';
import type {
  ApiResponse,
  ImpersonateResponse,
  PaginatedResponse,
  SuperadminAnalytics,
  TenantDetail,
  TenantRead,
} from '../lib/api-types';

type ListTenantsParams = {
  page?: number;
  pageSize?: number;
  isActive?: boolean;
};

type ListTenantsResult = {
  items: TenantRead[];
  total: number;
};

export async function listTenants(params?: ListTenantsParams): Promise<ListTenantsResult> {
  const response = await apiClient.get<PaginatedResponse<TenantRead>>('/superadmin/tenants', {
    params: {
      page: params?.page,
      page_size: params?.pageSize,
      isActive: params?.isActive,
    },
  });

  return {
    items: response.data.data,
    total: response.data.meta?.total ?? response.data.data.length,
  };
}

export async function getTenant(id: string): Promise<TenantDetail> {
  const response = await apiClient.get<ApiResponse<TenantDetail>>(`/superadmin/tenants/${id}`);

  return response.data.data;
}

export async function updateTenant(
  id: string,
  data: { is_active: boolean },
): Promise<TenantDetail> {
  const response = await apiClient.patch<ApiResponse<TenantDetail>>(
    `/superadmin/tenants/${id}`,
    data,
  );

  return response.data.data;
}

export async function impersonateTenant(id: string): Promise<ImpersonateResponse> {
  const response = await apiClient.post<ApiResponse<ImpersonateResponse>>(
    `/superadmin/tenants/${id}/impersonate`,
  );

  return response.data.data;
}

export async function getSuperadminAnalytics(params?: {
  from?: string;
  to?: string;
}): Promise<SuperadminAnalytics> {
  const response = await apiClient.get<ApiResponse<SuperadminAnalytics>>('/superadmin/analytics', {
    params: {
      from: params?.from,
      to: params?.to,
    },
  });

  return response.data.data;
}
