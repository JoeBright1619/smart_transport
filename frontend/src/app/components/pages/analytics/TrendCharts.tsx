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
import type { AnalyticsDaily } from '../../../lib/api-types';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';

export function TrendCharts({ daily }: { daily: AnalyticsDaily[] }) {
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Daily Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={formatChartDate} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="onTimePercentage" stroke="#10B981" name="On-Time %" />
                <Line type="monotone" dataKey="totalTrips" stroke="#3B82F6" name="Total Trips" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Revenue & Passengers</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={formatChartDate} />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="revenue" fill="#10B981" name="Revenue (RWF)" />
                <Bar yAxisId="right" dataKey="totalPassengers" fill="#3B82F6" name="Passengers" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Fuel Consumption Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={daily}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatChartDate} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="fuelConsumption"
                stroke="#F59E0B"
                name="Fuel (Liters)"
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
  return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
