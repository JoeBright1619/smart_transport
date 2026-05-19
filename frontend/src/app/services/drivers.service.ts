import { apiClient } from '../lib/api-client';
import type {
  ApiResponse,
  DriverCreate,
  DriverRead,
  DriverStatus,
  DriverUpdate,
  PaginatedResponse,
} from '../lib/api-types';

type ListDriversParams = {
  page?: number;
  pageSize?: number;
  status?: DriverStatus;
};

type ListDriversResult = {
  items: DriverRead[];
  total: number;
};

export async function listDrivers(params?: ListDriversParams): Promise<ListDriversResult> {
  const response = await apiClient.get<PaginatedResponse<DriverRead>>('/api/v1/drivers', {
    params: {
      page: params?.page,
      page_size: params?.pageSize,
      status: params?.status,
    },
  });

  return {
    items: response.data.data,
    total: response.data.meta?.total ?? response.data.data.length,
  };
}

export async function getDriver(id: string): Promise<DriverRead> {
  const response = await apiClient.get<ApiResponse<DriverRead>>(`/api/v1/drivers/${id}`);

  return response.data.data;
}

export async function createDriver(data: DriverCreate): Promise<DriverRead> {
  const response = await apiClient.post<ApiResponse<DriverRead>>('/api/v1/drivers', data);

  return response.data.data;
}

export async function updateDriver(id: string, data: DriverUpdate): Promise<DriverRead> {
  const response = await apiClient.patch<ApiResponse<DriverRead>>(`/api/v1/drivers/${id}`, data);

  return response.data.data;
}

export async function deleteDriver(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/drivers/${id}`);
}
