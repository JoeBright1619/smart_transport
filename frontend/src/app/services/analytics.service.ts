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
