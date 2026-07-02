import { useTranslation } from 'react-i18next';
import type { AlertRead } from '../../../lib/api-types';
import { formatDateTime } from '../../../lib/format';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { TablePagination } from '../../ui/table-pagination';
import { alertIcon, CheckCircle, severityBadgeVariant, severityColor } from './alert-helpers';

type AlertPagination = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

type AlertsListProps = {
  title: string;
  alerts: AlertRead[];
  acknowledgingAlertId: string | null;
  onAcknowledge: (alert: AlertRead) => void;
  pagination?: AlertPagination;
};

export function AlertsList({
  title,
  alerts,
  acknowledgingAlertId,
  onAcknowledge,
  pagination,
}: AlertsListProps) {
  const { t } = useTranslation('alerts');
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {alerts.length === 0 ? (
          <div className="py-8 text-center text-slate-500">
            <CheckCircle className="mx-auto mb-3 size-12 text-green-500" />
            <p>{t('noAlerts')}</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <AlertRow
              key={alert.id}
              alert={alert}
              disabled={acknowledgingAlertId === alert.id}
              onAcknowledge={onAcknowledge}
            />
          ))
        )}
        {pagination && (
          <TablePagination
            page={pagination.page}
            pageSize={pagination.pageSize}
            total={pagination.total}
            onPageChange={pagination.onPageChange}
          />
        )}
      </CardContent>
    </Card>
  );
}

function AlertRow({
  alert,
  disabled,
  onAcknowledge,
}: {
  alert: AlertRead;
  disabled: boolean;
  onAcknowledge: (alert: AlertRead) => void;
}) {
  const { t } = useTranslation('alerts');
  const Icon = alertIcon(alert.type);
  const muted = alert.isAcknowledged;

  return (
    <div className={`rounded-lg border p-4 ${muted ? 'bg-slate-50' : ''}`}>
      <div className="flex items-start gap-3">
        <div className={muted ? 'text-slate-400' : severityColor(alert.severity)}>
          <Icon className="size-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className={`font-medium ${muted ? 'text-slate-700' : ''}`}>{alert.title}</p>
              <p className="mt-1 text-sm text-slate-600">{alert.message}</p>
              <div className="mt-2 flex items-center gap-2">
                <p className="text-xs text-slate-400">{formatDateTime(alert.createdAt)}</p>
                {muted && (
                  <>
                    <CheckCircle className="size-3 text-green-600" />
                    <span className="text-xs text-green-600">{t('acknowledgedBadge')}</span>
                  </>
                )}
              </div>
            </div>
            <Badge variant={muted ? 'outline' : severityBadgeVariant(alert.severity)}>
              {t(`severity_${alert.severity}`)}
            </Badge>
          </div>
          {!muted && (
            <Button size="sm" variant="outline" className="mt-3" disabled={disabled} onClick={() => onAcknowledge(alert)}>
              {disabled ? t('acknowledging') : t('acknowledge')}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
