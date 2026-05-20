import { Bus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import type { FleetStats } from './fleet-helpers';

export function FleetStatsCards({ stats }: { stats: FleetStats }) {
  const activePercentage =
    stats.totalVehicles > 0 ? Math.round((stats.activeVehicles / stats.totalVehicles) * 100) : 0;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">Total Vehicles</CardTitle>
          <Bus className="size-4 text-blue-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalVehicles}</div>
          <p className="text-xs text-slate-500">Total capacity: {stats.totalCapacity} passengers</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">Active Vehicles</CardTitle>
          <div className="size-2 rounded-full bg-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">{stats.activeVehicles}</div>
          <p className="text-xs text-slate-500">{activePercentage}% of fleet</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">Idle Vehicles</CardTitle>
          <div className="size-2 rounded-full bg-yellow-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-yellow-600">{stats.idleVehicles}</div>
          <p className="text-xs text-slate-500">Available for dispatch</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">Maintenance</CardTitle>
          <div className="size-2 rounded-full bg-red-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600">{stats.maintenanceVehicles}</div>
          <p className="text-xs text-slate-500">Avg fuel: {stats.avgFuel}%</p>
        </CardContent>
      </Card>
    </div>
  );
}
