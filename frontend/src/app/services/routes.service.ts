import { apiClient } from '../lib/api-client';
import type {
  ApiResponse,
  PaginatedResponse,
  RouteCreate,
  RouteRead,
  RouteUpdate,
} from '../lib/api-types';

type ListRoutesParams = {
  page?: number;
  pageSize?: number;
  isActive?: boolean;
};

type ListRoutesResult = {
  items: RouteRead[];
  total: number;
};

export async function listRoutes(params?: ListRoutesParams): Promise<ListRoutesResult> {
  const response = await apiClient.get<PaginatedResponse<RouteRead>>('/api/v1/routes', {
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

export async function getRoute(id: string): Promise<RouteRead> {
  const response = await apiClient.get<ApiResponse<RouteRead>>(`/api/v1/routes/${id}`);

  return response.data.data;
}

export async function createRoute(data: RouteCreate): Promise<RouteRead> {
  const response = await apiClient.post<ApiResponse<RouteRead>>('/api/v1/routes', data);

  return response.data.data;
}

export async function updateRoute(id: string, data: RouteUpdate): Promise<RouteRead> {
  const response = await apiClient.patch<ApiResponse<RouteRead>>(`/api/v1/routes/${id}`, data);

  return response.data.data;
}

export async function deleteRoute(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/routes/${id}`);
}
