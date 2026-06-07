import { apiClient } from '../lib/api-client';
import type { ApiResponse, ArrivalEstimate, GlobalStopRead } from '../lib/api-types';

export async function getArrivals(stopId: string): Promise<ArrivalEstimate[]> {
  const response = await apiClient.get<ApiResponse<ArrivalEstimate[]>>('/api/v1/arrivals', {
    params: { stopId },
  });
  return response.data.data;
}

export async function getPublicStops(): Promise<GlobalStopRead[]> {
  const response = await apiClient.get<ApiResponse<GlobalStopRead[]>>('/api/v1/stops/public');
  return response.data.data;
}

export async function getCrossTenantArrivals(stopId: string): Promise<ArrivalEstimate[]> {
  const response = await apiClient.get<ApiResponse<ArrivalEstimate[]>>('/api/v1/arrivals/public', {
    params: { stop_id: stopId },
  });
  return response.data.data;
}
