import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useTranslation } from 'react-i18next';
import type { AnalyticsDaily } from '../../../lib/api-types';
import { formatDate } from '../../../lib/format';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';

export function TrendCharts({ daily }: { daily: AnalyticsDaily[] }) {
  const { t } = useTranslation('analytics');
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t('trends.dailyPerformance')}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={formatChartDate} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="onTimePercentage" stroke="#10B981" name={t('trends.onTime')} />
                <Line type="monotone" dataKey="totalTrips" stroke="#3B82F6" name={t('trends.totalTrips')} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('trends.revenuePassengers')}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={formatChartDate} />
                <YAxis yAxisId="left" tickFormatter={(value) => Math.round(Number(value)).toLocaleString()} />
                <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => Math.round(Number(value)).toLocaleString()} />
                <Tooltip formatter={(value) => Math.round(Number(value)).toLocaleString()} />
                <Legend />
                <Bar yAxisId="left" dataKey="revenue" fill="#10B981" name={t('trends.revenue')} />
                <Bar yAxisId="right" dataKey="totalPassengers" fill="#3B82F6" name={t('trends.passengers')} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('trends.fuelTrend')}</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={daily}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatChartDate} />
              <YAxis />
              <Tooltip formatter={(value) => Math.round(Number(value)).toLocaleString()} />
              <Legend />
              <Line
                type="monotone"
                dataKey="fuelConsumption"
                stroke="#F59E0B"
                name={t('trends.fuelLiters')}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </>
  );
}

function formatChartDate(value: string) {
  return formatDate(value, { month: 'short', day: 'numeric' });
}
