import { apiClient } from '../lib/api-client';
import type {
  ApiResponse,
  PaginatedResponse,
  TripCreate,
  TripRead,
  TripStatus,
} from '../lib/api-types';

type ListTripsParams = {
  page?: number;
  pageSize?: number;
  status?: TripStatus;
  vehicleId?: string;
  driverId?: string;
  routeId?: string;
};

type ListTripsResult = {
  items: TripRead[];
  total: number;
};

export async function listTrips(params?: ListTripsParams): Promise<ListTripsResult> {
  const response = await apiClient.get<PaginatedResponse<TripRead>>('/api/v1/trips', {
    params: {
      page: params?.page,
      page_size: params?.pageSize,
      status: params?.status,
      vehicleId: params?.vehicleId,
      driverId: params?.driverId,
      routeId: params?.routeId,
    },
  });

  return {
    items: response.data.data,
    total: response.data.meta?.total ?? response.data.data.length,
  };
}

export async function getTrip(id: string): Promise<TripRead> {
  const response = await apiClient.get<ApiResponse<TripRead>>(`/api/v1/trips/${id}`);

  return response.data.data;
}

export async function createTrip(data: TripCreate): Promise<TripRead> {
  const response = await apiClient.post<ApiResponse<TripRead>>('/api/v1/trips', data);

  return response.data.data;
}

export async function updateTripStatus(id: string, status: TripStatus): Promise<TripRead> {
  const response = await apiClient.patch<ApiResponse<TripRead>>(`/api/v1/trips/${id}`, {
    status,
  });

  return response.data.data;
}
