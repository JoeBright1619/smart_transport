import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import type { RoutePerformanceDatum } from './analytics-helpers';

export function RouteAnalytics({
  routePerformance,
}: {
  routePerformance: RoutePerformanceDatum[];
}) {
  const { t } = useTranslation('analytics');
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>{t('routes.comparison')}</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={routePerformance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="number" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="passengers" fill="#3B82F6" name={t('routes.totalPassengers')} />
              <Bar dataKey="trips" fill="#10B981" name={t('routes.totalTrips')} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('routes.statistics')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {routePerformance.length === 0 ? (
              <p className="text-sm text-slate-600">{t('routes.noData')}</p>
            ) : (
              routePerformance.map((route) => (
                <RouteStatRow key={route.id} route={route} />
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function RouteStatRow({ route }: { route: RoutePerformanceDatum }) {
  const { t } = useTranslation('analytics');
  return (
    <div className="border-b pb-3 last:border-0">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="size-3 rounded-full" style={{ backgroundColor: route.color }} />
          <span className="font-medium">{t('routes.route', { number: route.number })}</span>
        </div>
        <span className="text-sm text-slate-600">{route.name}</span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-sm">
        <Metric label={t('routes.trips')} value={route.trips} />
        <Metric label={t('routes.passengers')} value={route.passengers} />
        <Metric label={t('routes.avgPerTrip')} value={route.avgPassengers} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
