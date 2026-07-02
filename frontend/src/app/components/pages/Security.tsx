import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import type { TFunction } from 'i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Shield, FileText, Lock, Eye } from 'lucide-react';
import type { AuditLogRead, UserRead } from '../../lib/api-types';
import { listAuditLogs } from '../../services/audit.service';
import { listUsers } from '../../services/users.service';

const DATA_MODIFICATION_ACTIONS = new Set(['create', 'update', 'soft_delete']);

export function Security() {
  const { t } = useTranslation('security');
  const [logs, setLogs] = useState<AuditLogRead[]>([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [users, setUsers] = useState<UserRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadSecurityData() {
      setLoading(true);
      setError(null);

      try {
        const [auditResult, usersResult] = await Promise.all([
          listAuditLogs({ pageSize: 50 }),
          listUsers({ pageSize: 100 }),
        ]);

        if (!cancelled) {
          setLogs(auditResult.items);
          setTotalLogs(auditResult.total);
          setUsers(usersResult.items);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : t('unableLoad'));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadSecurityData();

    return () => {
      cancelled = true;
    };
  }, []);

  const usersById = useMemo(() => new Map(users.map((user) => [user.id, user])), [users]);
  const stats = useMemo(() => buildSecurityStats(logs, totalLogs, t), [logs, totalLogs, t]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <p className="text-slate-600">{t('subtitle')}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <SecurityStatCard title={t('totalAuditLogs')} value={stats.totalAuditLogs.toLocaleString()} icon={<FileText className="size-4 text-green-600" />} />
        <SecurityStatCard title={t('lastLogin')} value={stats.lastLoginLabel} icon={<Shield className="size-4 text-blue-600" />} />
        <SecurityStatCard title={t('failedLogins')} value={stats.failedLogins24h.toLocaleString()} subtitle={t('last24Hours')} icon={<Lock className="size-4 text-red-600" />} />
        <SecurityStatCard title={t('dataModifications')} value={stats.dataModificationsToday.toLocaleString()} subtitle={t('today')} icon={<Eye className="size-4 text-purple-600" />} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('recentAuditEvents')}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="py-6 text-center text-sm text-slate-500">{t('loadingLogs')}</p>
          ) : error ? (
            <p className="py-6 text-center text-sm text-red-600">{error}</p>
          ) : logs.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-500">{t('noEvents')}</p>
          ) : (
            <div className="space-y-3">
              {logs.map((event) => (
                <div key={event.id} className="flex items-center justify-between gap-3 rounded-lg border p-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      {t('eventLine', { action: actionLabel(event.action, t), resource: event.resourceType })}
                    </p>
                    <p className="text-xs text-slate-500">
                      {t('by', { user: usersById.get(event.userId)?.email ?? event.userId })}
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    <Badge className={actionBadgeClass(event.action)} variant="outline">
                      {actionLabel(event.action, t)}
                    </Badge>
                    <p className="mt-1 text-xs text-slate-500">{relativeTime(event.createdAt, t)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SecurityStatCard({
  title,
  value,
  subtitle,
  icon,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-slate-600">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </CardContent>
    </Card>
  );
}

function buildSecurityStats(logs: AuditLogRead[], totalLogs: number, t: TFunction) {
  const now = new Date();
  const today = now.toDateString();
  const last24Hours = now.getTime() - 24 * 60 * 60 * 1000;
  const lastLogin = logs.find((log) => log.action === 'login');

  return {
    totalAuditLogs: totalLogs,
    lastLoginLabel: lastLogin ? relativeTime(lastLogin.createdAt, t) : t('none'),
    failedLogins24h: logs.filter(
      (log) => log.action === 'login_failed' && new Date(log.createdAt).getTime() >= last24Hours,
    ).length,
    dataModificationsToday: logs.filter(
      (log) =>
        DATA_MODIFICATION_ACTIONS.has(log.action) &&
        new Date(log.createdAt).toDateString() === today,
    ).length,
  };
}

function formatAction(action: string): string {
  return action
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function actionLabel(action: string, t: TFunction): string {
  return t(`action_${action}`, { defaultValue: formatAction(action) });
}

function actionBadgeClass(action: string): string {
  if (action === 'create') return 'border-green-200 bg-green-50 text-green-700';
  if (action === 'update') return 'border-blue-200 bg-blue-50 text-blue-700';
  if (action === 'soft_delete') return 'border-red-200 bg-red-50 text-red-700';
  if (action === 'login_failed') return 'border-red-200 bg-red-50 text-red-700';
  if (action === 'login') return 'border-slate-200 bg-slate-50 text-slate-700';
  return 'border-purple-200 bg-purple-50 text-purple-700';
}

function relativeTime(value: string, t: TFunction): string {
  const diffMs = Date.now() - new Date(value).getTime();
  const diffMinutes = Math.max(0, Math.floor(diffMs / 60000));

  if (diffMinutes < 1) return t('justNow');
  if (diffMinutes < 60) return t('minutesAgo', { count: diffMinutes });

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return t('hoursAgo', { count: diffHours });

  const diffDays = Math.floor(diffHours / 24);
  return t('daysAgo', { count: diffDays });
}
