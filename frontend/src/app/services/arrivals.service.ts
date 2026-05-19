import { apiClient } from '../lib/api-client';
import type { ApiResponse, ArrivalEstimate } from '../lib/api-types';

export async function getArrivals(stopId: string): Promise<ArrivalEstimate[]> {
  const response = await apiClient.get<ApiResponse<ArrivalEstimate[]>>('/api/v1/arrivals', {
    params: {
      stopId,
    },
  });

  return response.data.data;
}
