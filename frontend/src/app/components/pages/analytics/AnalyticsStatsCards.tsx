import { Clock, DollarSign, Fuel, TrendingDown, TrendingUp, Users } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { AnalyticsSummary } from '../../../lib/api-types';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import {
  averageDailyFuel,
  formatPassengers,
  formatRevenue,
  type AnalyticsTrends,
} from './analytics-helpers';

type AnalyticsStatsCardsProps = {
  summary: AnalyticsSummary;
  trends: AnalyticsTrends;
  dayCount: number;
};

export function AnalyticsStatsCards({ summary, trends, dayCount }: AnalyticsStatsCardsProps) {
  const { t } = useTranslation('analytics');
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('stats.totalRevenue')}</CardTitle>
          <DollarSign className="size-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatRevenue(summary.totalRevenue)}</div>
          <TrendLine value={trends.revenueChange} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('stats.avgOnTime')}</CardTitle>
          <Clock className="size-4 text-blue-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{summary.onTimePercentage}%</div>
          <p className="mt-1 text-xs text-slate-500">{t('stats.acrossAllRoutes')}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('stats.totalPassengers')}</CardTitle>
          <Users className="size-4 text-purple-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatPassengers(summary.totalPassengers)}</div>
          <TrendLine value={trends.passengerChange} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-600">{t('stats.fuelConsumption')}</CardTitle>
          <Fuel className="size-4 text-orange-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{Math.round(summary.totalFuelConsumption)}L</div>
          <p className="mt-1 text-xs text-slate-500">
            {t('stats.avgPerDay', { value: averageDailyFuel(summary.totalFuelConsumption, dayCount) })}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function TrendLine({ value }: { value: string }) {
  const { t } = useTranslation('analytics');
  const positive = Number(value) >= 0;

  return (
    <div className="mt-1 flex items-center gap-1 text-xs">
      {positive ? (
        <TrendingUp className="size-3 text-green-600" />
      ) : (
        <TrendingDown className="size-3 text-red-600" />
      )}
      <span className={positive ? 'text-green-600' : 'text-red-600'}>
        {positive ? '+' : ''}
        {value}%
      </span>
      <span className="text-slate-500">{t('stats.firstToLast')}</span>
    </div>
  );
}
