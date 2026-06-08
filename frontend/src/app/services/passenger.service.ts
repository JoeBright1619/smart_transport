import { apiClient } from '../lib/api-client';
import type { ApiResponse, PaginatedResponse, PassengerNotification } from '../lib/api-types';

export interface ResolvedRoute {
  id: string;
  name: string;
  number: string;
  color: string;
}

export interface ResolvedStop {
  id: string;
  name: string;
}

export interface PassengerProfile {
  id: string;
  userId: string;
  fullName: string;
  email: string;
  phone: string | null;
  preferredRoutes: ResolvedRoute[];
  preferredStops: ResolvedStop[];
  notifyOnArrival: boolean;
  notifyOnDelay: boolean;
  totalTripsRecorded: number;
}

export interface PassengerProfileUpdate {
  phone?: string | null;
  preferredRoutes?: string[];
  preferredStops?: string[];
  notifyOnArrival?: boolean;
  notifyOnDelay?: boolean;
}

export interface PassengerListItem {
  id: string;
  fullName: string;
  email: string;
  phone: string | null;
  totalTripsRecorded: number;
  createdAt: string;
}

export interface RouteUsage {
  routeId: string;
  routeName: string;
  tripCount: number;
}

export interface WeeklyTrips {
  weekLabel: string;
  trips: number;
}

export interface PassengerStats {
  totalTrips: number;
  routesUsed: RouteUsage[];
  favouriteStop: string | null;
  onTimeRate: number;
  avgWaitMinutes: number;
  thisWeekTrips: number;
  lastWeekTrips: number;
  weeklyTrips: WeeklyTrips[];
  hasEnoughData: boolean;
}

export async function getMyStats(): Promise<PassengerStats> {
  const res = await apiClient.get<ApiResponse<PassengerStats>>('/api/v1/passengers/me/stats');
  return res.data.data;
}

export async function getMyProfile(): Promise<PassengerProfile> {
  const res = await apiClient.get<ApiResponse<PassengerProfile>>('/api/v1/passengers/me');
  return res.data.data;
}

export async function updateMyProfile(data: PassengerProfileUpdate): Promise<PassengerProfile> {
  const res = await apiClient.patch<ApiResponse<PassengerProfile>>('/api/v1/passengers/me', data);
  return res.data.data;
}

export async function getMyNotifications(): Promise<PassengerNotification[]> {
  const res = await apiClient.get<ApiResponse<PassengerNotification[]>>(
    '/api/v1/passengers/me/notifications',
  );
  return res.data.data;
}

export async function listPassengers(
  page = 1,
  pageSize = 20,
): Promise<PaginatedResponse<PassengerListItem>> {
  const res = await apiClient.get<PaginatedResponse<PassengerListItem>>('/api/v1/passengers', {
    params: { page, pageSize },
  });
  return res.data;
}
