import { apiClient } from '../lib/api-client';
import type {
  ApiResponse,
  PaginatedResponse,
  VehicleCreate,
  VehicleRead,
  VehicleStatus,
  VehicleUpdate,
} from '../lib/api-types';

type ListVehiclesParams = {
  page?: number;
  pageSize?: number;
  status?: VehicleStatus;
  routeId?: string;
};

type ListVehiclesResult = {
  items: VehicleRead[];
  total: number;
};

export async function listVehicles(params?: ListVehiclesParams): Promise<ListVehiclesResult> {
  const response = await apiClient.get<PaginatedResponse<VehicleRead>>('/api/v1/vehicles', {
    params: {
      page: params?.page,
      page_size: params?.pageSize,
      status: params?.status,
      routeId: params?.routeId,
    },
  });

  return {
    items: response.data.data,
    total: response.data.meta?.total ?? response.data.data.length,
  };
}

export async function getVehicle(id: string): Promise<VehicleRead> {
  const response = await apiClient.get<ApiResponse<VehicleRead>>(`/api/v1/vehicles/${id}`);

  return response.data.data;
}

export async function createVehicle(data: VehicleCreate): Promise<VehicleRead> {
  const response = await apiClient.post<ApiResponse<VehicleRead>>('/api/v1/vehicles', data);

  return response.data.data;
}

export async function updateVehicle(id: string, data: VehicleUpdate): Promise<VehicleRead> {
  const response = await apiClient.patch<ApiResponse<VehicleRead>>(`/api/v1/vehicles/${id}`, data);

  return response.data.data;
}

export async function deleteVehicle(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/vehicles/${id}`);
}
