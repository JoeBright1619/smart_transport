import { Clock, MapPin, Route as RouteIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import type { RouteStats } from './route-helpers';

export function RouteStatsCards({ stats }: { stats: RouteStats }) {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">Total Routes</CardTitle>
          <RouteIcon className="size-4 text-blue-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalRoutes}</div>
          <p className="text-xs text-slate-500">{stats.activeRoutes} active routes</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">Total Distance</CardTitle>
          <MapPin className="size-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalDistance.toFixed(1)} km</div>
          <p className="text-xs text-slate-500">Combined length</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">Avg Duration</CardTitle>
          <Clock className="size-4 text-purple-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.avgDuration} min</div>
          <p className="text-xs text-slate-500">Average route time</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">Total Stops</CardTitle>
          <MapPin className="size-4 text-orange-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalStops}</div>
          <p className="text-xs text-slate-500">Across all routes</p>
        </CardContent>
      </Card>
    </div>
  );
}
