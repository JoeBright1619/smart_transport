import { apiClient } from '../lib/api-client';
import type { AuditLogRead, PaginatedResponse } from '../lib/api-types';

type ListAuditLogsParams = {
  page?: number;
  pageSize?: number;
  action?: string;
  resourceType?: string;
};

type ListAuditLogsResult = {
  items: AuditLogRead[];
  total: number;
};

export async function listAuditLogs(params?: ListAuditLogsParams): Promise<ListAuditLogsResult> {
  const response = await apiClient.get<PaginatedResponse<AuditLogRead>>('/api/v1/audit-logs', {
    params: {
      page: params?.page,
      page_size: params?.pageSize,
      action: params?.action,
      resource_type: params?.resourceType,
    },
  });

  return {
    items: response.data.data,
    total: response.data.meta?.total ?? response.data.data.length,
  };
}
