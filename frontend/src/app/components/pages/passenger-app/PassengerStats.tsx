import { useEffect, useState } from 'react';
import { BarChart2, Clock, MapPin, TrendingUp } from 'lucide-react';
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import {
  getMyStats,
  type PassengerStats,
  type RouteUsage,
} from '../../../services/passenger.service';

export function PassengerStats() {
  const { t } = useTranslation('passenger');
  const [stats, setStats] = useState<PassengerStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="text-center py-12 text-slate-500 text-sm">
        {t('stats.loading')}
      </div>
    );
  }

  if (!stats || !stats.hasEnoughData) {
    return (
      <Card>
        <CardContent className="py-12 text-center space-y-2">
          <BarChart2 className="size-10 text-slate-300 mx-auto" />
          <p className="font-medium text-slate-600">{t('stats.noStatsTitle')}</p>
          <p className="text-sm text-slate-400">
            {t('stats.noStatsBody')}
          </p>
        </CardContent>
      </Card>
    );
  }

  const weekTrend = stats.thisWeekTrips - stats.lastWeekTrips;
  const topRoute = stats.routesUsed[0];

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          label={t('stats.totalTrips')}
          value={String(stats.totalTrips)}
          icon={<TrendingUp className="size-4" />}
        />
        <StatCard
          label={t('stats.onTimeRate')}
          value={stats.onTimeRate > 0 ? `${stats.onTimeRate}%` : t('stats.notAvailable')}
          icon={<Clock className="size-4" />}
        />
        <StatCard
          label={t('stats.favouriteRoute')}
          value={topRoute?.routeName ?? t('stats.noneYet')}
          icon={<MapPin className="size-4" />}
        />
        <StatCard
          label={t('stats.avgWait')}
          value={stats.avgWaitMinutes > 0 ? t('stats.minutes', { count: stats.avgWaitMinutes }) : t('stats.notAvailable')}
          icon={<Clock className="size-4" />}
        />
      </div>

      {/* Weekly bar chart */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center justify-between">
            {t('stats.tripsPerWeek')}
            {weekTrend !== 0 && (
              <span
                className={`text-xs font-normal ${
                  weekTrend > 0 ? 'text-green-600' : 'text-orange-500'
                }`}
              >
                {t('stats.vsLastWeek', { trend: `${weekTrend > 0 ? '+' : ''}${weekTrend}` })}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={130}>
            <BarChart
              data={stats.weeklyTrips}
              margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
            >
              <XAxis dataKey="weekLabel" tick={{ fontSize: 10 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="trips" radius={[3, 3, 0, 0]}>
                {stats.weeklyTrips.map((_, i) => (
                  <Cell
                    key={i}
                    fill={
                      i === stats.weeklyTrips.length - 1 ? '#3b82f6' : '#bfdbfe'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Routes used */}
      {stats.routesUsed.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">{t('stats.routesUsed')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {stats.routesUsed.map((r: RouteUsage) => (
              <div
                key={r.routeId}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-slate-700">{r.routeName}</span>
                <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full font-medium">
                  {t('stats.tripCount', { count: r.tripCount })}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {stats.favouriteStop && (
        <p className="text-xs text-slate-500 text-center">
          {t('stats.mostVisited')}{' '}
          <span className="font-medium text-slate-700">{stats.favouriteStop}</span>
        </p>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <Card>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <p className="text-xs text-slate-500">{label}</p>
            <p className="text-base font-bold text-slate-800 mt-0.5 truncate">
              {value}
            </p>
          </div>
          <div className="text-blue-500 ml-2 flex-shrink-0">{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}
