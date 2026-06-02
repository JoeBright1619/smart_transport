import { apiClient } from '../lib/api-client';
import type { AnalyticsData, ApiResponse } from '../lib/api-types';

type GetAnalyticsParams = {
  from?: string;
  to?: string;
};

export async function getAnalytics(params?: GetAnalyticsParams): Promise<AnalyticsData> {
  const response = await apiClient.get<ApiResponse<AnalyticsData>>('/api/v1/analytics', {
    params: {
      from: params?.from,
      to: params?.to,
    },
  });

  return response.data.data;
}

export type GetFilteredReportParams = {
  reportType: 'route' | 'daily' | 'fleet' | 'driver';
  routeId?: string;
  vehicleId?: string;
  driverId?: string;
  dateFrom?: string;
  dateTo?: string;
};

export async function getFilteredReport(params: GetFilteredReportParams) {
  const response = await apiClient.get<ApiResponse<import('../lib/api-types').FilteredReportResponse>>(
    '/api/v1/analytics/report',
    {
      params: {
        report_type: params.reportType,
        route_id: params.routeId,
        vehicle_id: params.vehicleId,
        driver_id: params.driverId,
        date_from: params.dateFrom,
        date_to: params.dateTo,
      },
    }
  );

  return response.data.data;
}
