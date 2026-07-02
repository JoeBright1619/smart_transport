import { useTranslation } from 'react-i18next';
import { AlertTriangle, Bell, CheckCircle } from './alert-helpers';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import type { AlertStats } from './alert-helpers';

export function AlertStatsCards({ stats }: { stats: AlertStats }) {
  const { t } = useTranslation('alerts');
  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('totalUnread')}</CardTitle>
          <Bell className="size-4 text-blue-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.unread}</div>
          <p className="text-xs text-slate-500">{t('pendingReview')}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('critical')}</CardTitle>
          <AlertTriangle className="size-4 text-red-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600">{stats.critical}</div>
          <p className="text-xs text-slate-500">{t('immediateAction')}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('highPriority')}</CardTitle>
          <AlertTriangle className="size-4 text-orange-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-orange-600">{stats.high}</div>
          <p className="text-xs text-slate-500">{t('requiresAttention')}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('acknowledged')}</CardTitle>
          <CheckCircle className="size-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">{stats.acknowledged}</div>
          <p className="text-xs text-slate-500">{t('resolvedReviewed')}</p>
        </CardContent>
      </Card>
    </div>
  );
}
