import { apiClient } from '../lib/api-client';
import type {
  ApiResponse,
  MaintenanceCreate,
  MaintenanceRead,
  MaintenanceStatus,
  MaintenanceUpdate,
  PaginatedResponse,
} from '../lib/api-types';

type ListMaintenanceParams = {
  page?: number;
  pageSize?: number;
  vehicleId?: string;
  status?: MaintenanceStatus;
};

type ListMaintenanceResult = {
  items: MaintenanceRead[];
  total: number;
};

export async function listMaintenance(
  params?: ListMaintenanceParams,
): Promise<ListMaintenanceResult> {
  const response = await apiClient.get<PaginatedResponse<MaintenanceRead>>(
    '/api/v1/maintenance',
    {
      params: {
        page: params?.page,
        page_size: params?.pageSize,
        vehicleId: params?.vehicleId,
        status: params?.status,
      },
    },
  );

  return {
    items: response.data.data,
    total: response.data.meta?.total ?? response.data.data.length,
  };
}

export async function getMaintenance(id: string): Promise<MaintenanceRead> {
  const response = await apiClient.get<ApiResponse<MaintenanceRead>>(
    `/api/v1/maintenance/${id}`,
  );

  return response.data.data;
}

export async function createMaintenance(data: MaintenanceCreate): Promise<MaintenanceRead> {
  const response = await apiClient.post<ApiResponse<MaintenanceRead>>(
    '/api/v1/maintenance',
    data,
  );

  return response.data.data;
}

export async function updateMaintenance(
  id: string,
  data: MaintenanceUpdate,
): Promise<MaintenanceRead> {
  const response = await apiClient.patch<ApiResponse<MaintenanceRead>>(
    `/api/v1/maintenance/${id}`,
    data,
  );

  return response.data.data;
}
