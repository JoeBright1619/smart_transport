import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, Navigate } from 'react-router';
import { AlertTriangle, Bus, CheckCircle, Clock, TrendingUp, Users } from 'lucide-react';
import type { AlertRead, AnalyticsData, UserRole, VehicleRead, VehicleStatus } from '../../lib/api-types';
import { useAuth } from '../../lib/auth-context';
import * as alertsService from '../../services/alerts.service';
import * as analyticsService from '../../services/analytics.service';
import * as vehiclesService from '../../services/vehicles.service';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Skeleton } from '../ui/skeleton';
import { ErrorMessage } from '../ui/error-message';
import { formatRevenue } from './analytics/analytics-helpers';

type DashboardState = {
  analytics: AnalyticsData | null;
  alerts: AlertRead[];
  vehicles: VehicleRead[];
};

const initialDashboardState: DashboardState = {
  analytics: null,
  alerts: [],
  vehicles: [],
};

const ANALYTICS_ROLES: UserRole[] = ['admin', 'operator'];

function canViewAnalytics(role: UserRole | undefined): boolean {
  return role !== undefined && ANALYTICS_ROLES.includes(role);
}

function severityClass(severity: AlertRead['severity']): string {
  if (severity === 'critical') return 'text-red-500';
  if (severity === 'high') return 'text-orange-500';
  if (severity === 'medium') return 'text-yellow-500';
  return 'text-blue-500';
}

function statusDotClass(status: VehicleStatus): string {
  if (status === 'active') return 'bg-green-500';
  if (status === 'idle') return 'bg-yellow-500';
  if (status === 'maintenance') return 'bg-red-500';
  return 'bg-slate-400';
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-56" />
        <Skeleton className="mt-2 h-4 w-80 max-w-full" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-20" />
              <Skeleton className="mt-2 h-3 w-28" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-20 w-full" />
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent className="space-y-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} className="h-16 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function Dashboard() {
  const { t } = useTranslation('dashboard');
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<DashboardState>(initialDashboardState);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const showAnalytics = canViewAnalytics(user?.role);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [analytics, alerts, vehicles] = await Promise.all([
        showAnalytics ? analyticsService.getAnalytics() : Promise.resolve(null),
        alertsService.listAlerts({ pageSize: 5, isAcknowledged: false }),
        vehiclesService.listVehicles({ pageSize: 100 }),
      ]);

      setDashboard({
        analytics,
        alerts: alerts.items,
        vehicles: vehicles.items,
      });
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : t('errorLoad'));
    } finally {
      setLoading(false);
    }
  }, [showAnalytics, t]);

  useEffect(() => {
    if (user?.role === 'superadmin') return;
    void fetchDashboard();
  }, [fetchDashboard, user?.role]);

  const fleetCounts = useMemo(
    () =>
      dashboard.vehicles.reduce<Record<VehicleStatus, number>>(
        (counts, vehicle) => {
          counts[vehicle.status] += 1;
          return counts;
        },
        { active: 0, idle: 0, maintenance: 0, offline: 0 },
      ),
    [dashboard.vehicles],
  );

  const analyticsSummary = dashboard.analytics?.summary;
  const tenantName = user?.tenantName;
  const totalVehicles = dashboard.vehicles.length;
  const activeVehicles = fleetCounts.active;
  const fleetUtilization = totalVehicles > 0 ? Math.round((activeVehicles / totalVehicles) * 100) : 0;

  if (user?.role === 'superadmin') {
    return <Navigate to="/superadmin" replace />;
  }

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={() => void fetchDashboard()} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{tenantName ? t('titleTenant', { name: tenantName }) : t('title')}</h1>
        <p className="text-slate-600">{t('subtitle')}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">{t('activeVehicles')}</CardTitle>
            <Bus className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeVehicles}/{totalVehicles}</div>
            <p className="text-xs text-slate-500">{t('fleetUtilization', { pct: fleetUtilization })}</p>
          </CardContent>
        </Card>

        {showAnalytics ? (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">{t('totalTrips')}</CardTitle>
                <Clock className="size-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analyticsSummary?.totalTrips ?? 0}</div>
                <p className="text-xs text-slate-500">
                  {t('avgDelay', { min: analyticsSummary?.avgDelay ?? 0 })}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">{t('onTimePerformance')}</CardTitle>
                <CheckCircle className="size-4 text-emerald-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analyticsSummary?.onTimePercentage ?? 0}%</div>
                <p className="text-xs text-slate-500">{t('last7Days')}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">{t('totalPassengers')}</CardTitle>
                <Users className="size-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(analyticsSummary?.totalPassengers ?? 0).toLocaleString()}
                </div>
                <p className="text-xs text-slate-500">
                  {t('revenue', { amount: formatRevenue(analyticsSummary?.totalRevenue ?? 0) })}
                </p>
              </CardContent>
            </Card>
          </>
        ) : (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">{t('openAlerts')}</CardTitle>
              <AlertTriangle className="size-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboard.alerts.length}</div>
              <p className="text-xs text-slate-500">{t('unacknowledgedAlerts')}</p>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{t('recentAlerts')}</CardTitle>
              <Link to="/alerts">
                <Button variant="ghost" size="sm">{t('viewAll')}</Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {dashboard.alerts.length === 0 ? (
              <p className="text-sm text-slate-500">{t('noUnacknowledged')}</p>
            ) : (
              <div className="space-y-3">
                {dashboard.alerts.map((alert) => (
                  <div key={alert.id} className="flex items-start gap-3 rounded-lg border p-3">
                    <AlertTriangle className={`size-5 ${severityClass(alert.severity)}`} />
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium">{alert.title}</p>
                        <Badge variant={alert.isAcknowledged ? 'secondary' : 'default'} className="text-xs">
                          {t(`alerts:severity_${alert.severity}`)}
                        </Badge>
                      </div>
                      <p className="mt-1 text-xs text-slate-600">{alert.message}</p>
                      <p className="mt-1 text-xs text-slate-400">
                        {new Date(alert.createdAt).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('fleetStatus')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
              {(['active', 'idle', 'maintenance', 'offline'] as VehicleStatus[]).map((status) => (
                <div key={status} className="rounded-lg border p-2">
                  <div className="flex items-center gap-2">
                    <div className={`size-2 rounded-full ${statusDotClass(status)}`} />
                    <span className="text-slate-600">{t(`fleet:vehicleStatus.${status}`)}</span>
                  </div>
                  <p className="mt-1 text-lg font-semibold">{fleetCounts[status]}</p>
                </div>
              ))}
            </div>
            {dashboard.vehicles.length === 0 ? (
              <p className="text-sm text-slate-500">{t('noVehicles')}</p>
            ) : (
              <div className="space-y-3">
                {dashboard.vehicles.slice(0, 6).map((vehicle) => (
                  <div key={vehicle.id} className="flex items-center justify-between rounded-lg border p-3">
                    <div className="flex items-center gap-3">
                      <div className={`size-2 rounded-full ${statusDotClass(vehicle.status)}`} />
                      <div>
                        <p className="text-sm font-medium">{vehicle.registrationNumber}</p>
                        <p className="text-xs text-slate-500">{vehicle.model}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant={vehicle.status === 'active' ? 'default' : 'secondary'}>
                        {t(`fleet:vehicleStatus.${vehicle.status}`)}
                      </Badge>
                      {vehicle.status === 'active' && (
                        <p className="mt-1 text-xs text-slate-500">{t('kmh', { speed: vehicle.speed ?? 0 })}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Link to="/fleet">
              <Button variant="outline" className="mt-4 w-full">{t('viewFullFleet')}</Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('quickActions')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Link to="/tracking">
              <Button variant="outline" className="w-full justify-start">
                <Bus className="mr-2 size-4" />
                {t('trackVehicles')}
              </Button>
            </Link>
            <Link to="/dispatch">
              <Button variant="outline" className="w-full justify-start">
                <Clock className="mr-2 size-4" />
                {t('dispatchControl')}
              </Button>
            </Link>
            {showAnalytics && (
              <Link to="/analytics">
                <Button variant="outline" className="w-full justify-start">
                  <TrendingUp className="mr-2 size-4" />
                  {t('viewAnalytics')}
                </Button>
              </Link>
            )}
            <Link to="/maintenance">
              <Button variant="outline" className="w-full justify-start">
                <AlertTriangle className="mr-2 size-4" />
                {t('maintenanceLog')}
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
