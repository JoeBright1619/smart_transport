import { Calendar, CheckCircle, DollarSign, Wrench } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import type { MaintenanceStats } from './maintenance-helpers';

export function MaintenanceStatsCards({ stats }: { stats: MaintenanceStats }) {
  const { t } = useTranslation('maintenance');
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('stats.scheduled')}</CardTitle>
          <Calendar className="size-4 text-blue-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.scheduled}</div>
          <p className="text-xs text-slate-500">{t('stats.upcomingServices')}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('stats.inProgress')}</CardTitle>
          <Wrench className="size-4 text-orange-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.inProgress}</div>
          <p className="text-xs text-slate-500">{t('stats.currentlyServicing')}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('stats.completed')}</CardTitle>
          <CheckCircle className="size-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.completed}</div>
          <p className="text-xs text-slate-500">{t('stats.thisPeriod')}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('stats.totalCost')}</CardTitle>
          <DollarSign className="size-4 text-purple-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalCost}</div>
          <p className="text-xs text-slate-500">{t('stats.currency')}</p>
        </CardContent>
      </Card>
    </div>
  );
}
