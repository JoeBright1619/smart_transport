import { useTranslation } from 'react-i18next';
import { Clock, MapPin, Route as RouteIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import type { RouteStats } from './route-helpers';

export function RouteStatsCards({ stats }: { stats: RouteStats }) {
  const { t } = useTranslation('routes');
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('totalRoutes')}</CardTitle>
          <RouteIcon className="size-4 text-blue-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalRoutes}</div>
          <p className="text-xs text-slate-500">{t('activeRoutesCount', { count: stats.activeRoutes })}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('totalDistance')}</CardTitle>
          <MapPin className="size-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{t('km', { value: stats.totalDistance.toFixed(1) })}</div>
          <p className="text-xs text-slate-500">{t('combinedLength')}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('avgDuration')}</CardTitle>
          <Clock className="size-4 text-purple-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{t('min', { value: stats.avgDuration })}</div>
          <p className="text-xs text-slate-500">{t('averageRouteTime')}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('totalStops')}</CardTitle>
          <MapPin className="size-4 text-orange-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalStops}</div>
          <p className="text-xs text-slate-500">{t('acrossAllRoutes')}</p>
        </CardContent>
      </Card>
    </div>
  );
}
