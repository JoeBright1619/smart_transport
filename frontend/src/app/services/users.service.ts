import { apiClient } from '../lib/api-client';
import type { ApiResponse, PaginatedResponse, UserCreate, UserRead, UserUpdate } from '../lib/api-types';

type ListUsersParams = {
  page?: number;
  pageSize?: number;
  role?: string;
};

type ListUsersResult = {
  items: UserRead[];
  total: number;
};

export async function listUsers(params?: ListUsersParams): Promise<ListUsersResult> {
  const response = await apiClient.get<PaginatedResponse<UserRead>>('/api/v1/users', {
    params: {
      page: params?.page,
      page_size: params?.pageSize,
      role: params?.role,
    },
  });

  return {
    items: response.data.data,
    total: response.data.meta?.total ?? response.data.data.length,
  };
}

export async function getUser(id: string): Promise<UserRead> {
  const response = await apiClient.get<ApiResponse<UserRead>>(`/api/v1/users/${id}`);

  return response.data.data;
}

export async function createUser(data: UserCreate): Promise<UserRead> {
  const response = await apiClient.post<ApiResponse<UserRead>>('/api/v1/users', data);

  return response.data.data;
}

export async function updateUser(id: string, data: UserUpdate): Promise<UserRead> {
  const response = await apiClient.patch<ApiResponse<UserRead>>(`/api/v1/users/${id}`, data);

  return response.data.data;
}

export async function deleteUser(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/users/${id}`);
}
