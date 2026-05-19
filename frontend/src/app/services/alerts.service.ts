import { apiClient } from '../lib/api-client';
import type {
  AlertRead,
  AlertSeverity,
  AlertType,
  ApiResponse,
  PaginatedResponse,
} from '../lib/api-types';

type ListAlertsParams = {
  page?: number;
  pageSize?: number;
  severity?: AlertSeverity;
  type?: AlertType;
  isAcknowledged?: boolean;
};

type ListAlertsResult = {
  items: AlertRead[];
  total: number;
};

export async function listAlerts(params?: ListAlertsParams): Promise<ListAlertsResult> {
  const response = await apiClient.get<PaginatedResponse<AlertRead>>('/api/v1/alerts', {
    params: {
      page: params?.page,
      page_size: params?.pageSize,
      severity: params?.severity,
      type: params?.type,
      isAcknowledged: params?.isAcknowledged,
    },
  });

  return {
    items: response.data.data,
    total: response.data.meta?.total ?? response.data.data.length,
  };
}

export async function acknowledgeAlert(id: string): Promise<AlertRead> {
  const response = await apiClient.post<ApiResponse<AlertRead>>(`/api/v1/alerts/${id}/acknowledge`);

  return response.data.data;
}
