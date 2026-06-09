import { apiClient } from '../lib/api-client';
import type { PaginatedResponse } from '../lib/api-types';

export interface PassengerTripRecord {
  boardingId: string;
  eventType: 'boarded' | 'alighted';
  count: number;
  stopId: string;
  stopName: string;
  tripId: string | null;
  recordedAt: string;
  occupancyAfter: number;
  vehicleRegistration: string | null;
  vehicleModel: string | null;
}

export async function getMyBoardings(page = 1, pageSize = 20): Promise<PaginatedResponse<PassengerTripRecord>> {
  const res = await apiClient.get<PaginatedResponse<PassengerTripRecord>>('/api/v1/boardings/me', {
    params: { page, pageSize },
  });
  return res.data;
}
