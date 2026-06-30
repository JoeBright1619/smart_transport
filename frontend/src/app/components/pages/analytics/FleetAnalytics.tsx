import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { useTranslation } from 'react-i18next';
import type { VehicleRead } from '../../../lib/api-types';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import type { FleetStatusDatum } from './analytics-helpers';

type FleetAnalyticsProps = {
  fleetStatus: FleetStatusDatum[];
  fleetHealth: VehicleRead[];
};

export function FleetAnalytics({ fleetStatus, fleetHealth }: FleetAnalyticsProps) {
  const { t } = useTranslation('analytics');
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>{t('fleet.statusDistribution')}</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={fleetStatus}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {fleetStatus.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('fleet.healthOverview')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {fleetHealth.length === 0 ? (
              <p className="text-sm text-slate-600">{t('fleet.noHealthData')}</p>
            ) : (
              fleetHealth.map((vehicle) => <FleetHealthRow key={vehicle.id} vehicle={vehicle} />)
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function FleetHealthRow({ vehicle }: { vehicle: VehicleRead }) {
  const { t } = useTranslation('analytics');
  const fuel = vehicle.fuel ?? 0;

  return (
    <div className="border-b pb-3 last:border-0">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-medium">{vehicle.registrationNumber}</span>
        <span className={`rounded px-2 py-1 text-xs ${engineClass(vehicle.engineStatus)}`}>
          {t(`fleet.engineStatus.${vehicle.engineStatus}`)}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <div className="mb-1 flex items-center justify-between">
            <span className="text-xs text-slate-500">{t('fleet.fuelLevel')}</span>
            <span className="text-xs">{fuel}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-slate-200">
            <div className={`h-full rounded-full ${fuelClass(fuel)}`} style={{ width: `${fuel}%` }} />
          </div>
        </div>
      </div>
    </div>
  );
}

function engineClass(status: VehicleRead['engineStatus']): string {
  if (status === 'good') return 'bg-green-100 text-green-700';
  if (status === 'warning') return 'bg-yellow-100 text-yellow-700';
  return 'bg-red-100 text-red-700';
}

function fuelClass(fuel: number): string {
  if (fuel > 50) return 'bg-green-500';
  if (fuel > 25) return 'bg-yellow-500';
  return 'bg-red-500';
}
