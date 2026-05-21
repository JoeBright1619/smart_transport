import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router';
import { AlertTriangle, Bus, CheckCircle, Clock, TrendingUp, Users } from 'lucide-react';
import type { AlertRead, AnalyticsData, VehicleRead, VehicleStatus } from '../../lib/api-types';
import * as alertsService from '../../services/alerts.service';
import * as analyticsService from '../../services/analytics.service';
import * as vehiclesService from '../../services/vehicles.service';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Skeleton } from '../ui/skeleton';

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
  const [dashboard, setDashboard] = useState<DashboardState>(initialDashboardState);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [analytics, alerts, vehicles] = await Promise.all([
        analyticsService.getAnalytics(),
        alertsService.listAlerts({ pageSize: 5, isAcknowledged: false }),
        vehiclesService.listVehicles({ pageSize: 100 }),
      ]);

      setDashboard({
        analytics,
        alerts: alerts.items,
        vehicles: vehicles.items,
      });
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : 'Unable to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchDashboard();
  }, [fetchDashboard]);

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
  const totalVehicles = dashboard.vehicles.length;
  const activeVehicles = fleetCounts.active;
  const fleetUtilization = totalVehicles > 0 ? Math.round((activeVehicles / totalVehicles) * 100) : 0;

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Fleet Dashboard</h1>
          <p className="text-slate-600">Real-time overview of your transport operations</p>
        </div>
        <Card>
          <CardContent className="flex flex-col items-start gap-4 p-6">
            <div>
              <p className="font-medium text-red-700">Unable to load dashboard data</p>
              <p className="mt-1 text-sm text-slate-600">{error}</p>
            </div>
            <Button onClick={() => void fetchDashboard()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Fleet Dashboard</h1>
        <p className="text-slate-600">Real-time overview of your transport operations</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Active Vehicles</CardTitle>
            <Bus className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeVehicles}/{totalVehicles}</div>
            <p className="text-xs text-slate-500">{fleetUtilization}% fleet utilization</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Trips</CardTitle>
            <Clock className="size-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsSummary?.totalTrips ?? 0}</div>
            <p className="text-xs text-slate-500">
              Avg delay: {analyticsSummary?.avgDelay ?? 0} min
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">On-Time Performance</CardTitle>
            <CheckCircle className="size-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsSummary?.onTimePercentage ?? 0}%</div>
            <p className="text-xs text-slate-500">
              {dashboard.alerts.length} unacknowledged alerts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Passengers</CardTitle>
            <Users className="size-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(analyticsSummary?.totalPassengers ?? 0).toLocaleString()}
            </div>
            <p className="text-xs text-slate-500">
              {(analyticsSummary?.totalRevenue ?? 0).toLocaleString()} RWF revenue
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Alerts</CardTitle>
              <Link to="/alerts">
                <Button variant="ghost" size="sm">View All</Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {dashboard.alerts.length === 0 ? (
              <p className="text-sm text-slate-500">No unacknowledged alerts.</p>
            ) : (
              <div className="space-y-3">
                {dashboard.alerts.map((alert) => (
                  <div key={alert.id} className="flex items-start gap-3 rounded-lg border p-3">
                    <AlertTriangle className={`size-5 ${severityClass(alert.severity)}`} />
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium">{alert.title}</p>
                        <Badge variant={alert.isAcknowledged ? 'secondary' : 'default'} className="text-xs">
                          {alert.severity}
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
            <CardTitle>Fleet Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
              {(['active', 'idle', 'maintenance', 'offline'] as VehicleStatus[]).map((status) => (
                <div key={status} className="rounded-lg border p-2">
                  <div className="flex items-center gap-2">
                    <div className={`size-2 rounded-full ${statusDotClass(status)}`} />
                    <span className="capitalize text-slate-600">{status}</span>
                  </div>
                  <p className="mt-1 text-lg font-semibold">{fleetCounts[status]}</p>
                </div>
              ))}
            </div>
            {dashboard.vehicles.length === 0 ? (
              <p className="text-sm text-slate-500">No vehicles found.</p>
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
                        {vehicle.status}
                      </Badge>
                      {vehicle.status === 'active' && (
                        <p className="mt-1 text-xs text-slate-500">{vehicle.speed ?? 0} km/h</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Link to="/fleet">
              <Button variant="outline" className="mt-4 w-full">View Full Fleet</Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Link to="/tracking">
              <Button variant="outline" className="w-full justify-start">
                <Bus className="mr-2 size-4" />
                Track Vehicles
              </Button>
            </Link>
            <Link to="/dispatch">
              <Button variant="outline" className="w-full justify-start">
                <Clock className="mr-2 size-4" />
                Dispatch Control
              </Button>
            </Link>
            <Link to="/analytics">
              <Button variant="outline" className="w-full justify-start">
                <TrendingUp className="mr-2 size-4" />
                View Analytics
              </Button>
            </Link>
            <Link to="/maintenance">
              <Button variant="outline" className="w-full justify-start">
                <AlertTriangle className="mr-2 size-4" />
                Maintenance Log
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
