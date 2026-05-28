import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Shield, FileText, Lock, Eye } from 'lucide-react';
import type { AuditLogRead, UserRead } from '../../lib/api-types';
import { listAuditLogs } from '../../services/audit.service';
import { listUsers } from '../../services/users.service';

const DATA_MODIFICATION_ACTIONS = new Set(['create', 'update', 'soft_delete']);

export function Security() {
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
          setError(loadError instanceof Error ? loadError.message : 'Unable to load audit logs');
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
  const stats = useMemo(() => buildSecurityStats(logs, totalLogs), [logs, totalLogs]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Security & Audit</h1>
        <p className="text-slate-600">Security monitoring and audit trail</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <SecurityStatCard title="Total Audit Logs" value={stats.totalAuditLogs.toLocaleString()} icon={<FileText className="size-4 text-green-600" />} />
        <SecurityStatCard title="Last Login" value={stats.lastLoginLabel} icon={<Shield className="size-4 text-blue-600" />} />
        <SecurityStatCard title="Failed Logins" value={stats.failedLogins24h.toLocaleString()} subtitle="Last 24 hours" icon={<Lock className="size-4 text-red-600" />} />
        <SecurityStatCard title="Data Modifications" value={stats.dataModificationsToday.toLocaleString()} subtitle="Today" icon={<Eye className="size-4 text-purple-600" />} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Audit Events</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="py-6 text-center text-sm text-slate-500">Loading audit logs...</p>
          ) : error ? (
            <p className="py-6 text-center text-sm text-red-600">{error}</p>
          ) : logs.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-500">No audit events found.</p>
          ) : (
            <div className="space-y-3">
              {logs.map((event) => (
                <div key={event.id} className="flex items-center justify-between gap-3 rounded-lg border p-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      {formatAction(event.action)} {event.resourceType}
                    </p>
                    <p className="text-xs text-slate-500">
                      by {usersById.get(event.userId)?.email ?? event.userId}
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    <Badge className={actionBadgeClass(event.action)} variant="outline">
                      {event.action}
                    </Badge>
                    <p className="mt-1 text-xs text-slate-500">{relativeTime(event.createdAt)}</p>
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

function buildSecurityStats(logs: AuditLogRead[], totalLogs: number) {
  const now = new Date();
  const today = now.toDateString();
  const last24Hours = now.getTime() - 24 * 60 * 60 * 1000;
  const lastLogin = logs.find((log) => log.action === 'login');

  return {
    totalAuditLogs: totalLogs,
    lastLoginLabel: lastLogin ? relativeTime(lastLogin.createdAt) : 'None',
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

function actionBadgeClass(action: string): string {
  if (action === 'create') return 'border-green-200 bg-green-50 text-green-700';
  if (action === 'update') return 'border-blue-200 bg-blue-50 text-blue-700';
  if (action === 'soft_delete') return 'border-red-200 bg-red-50 text-red-700';
  if (action === 'login_failed') return 'border-red-200 bg-red-50 text-red-700';
  if (action === 'login') return 'border-slate-200 bg-slate-50 text-slate-700';
  return 'border-purple-200 bg-purple-50 text-purple-700';
}

function relativeTime(value: string): string {
  const diffMs = Date.now() - new Date(value).getTime();
  const diffMinutes = Math.max(0, Math.floor(diffMs / 60000));

  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
}
