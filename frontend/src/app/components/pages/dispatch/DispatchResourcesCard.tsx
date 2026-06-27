import { useTranslation } from 'react-i18next';
import type { DriverRead, VehicleRead } from '../../../lib/api-types';
import { Badge } from '../../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';

export function DispatchResourcesCard({
  availableVehicles,
  availableDrivers,
}: {
  availableVehicles: VehicleRead[];
  availableDrivers: DriverRead[];
}) {
  const { t } = useTranslation('dispatch');
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('resources.title')}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 lg:grid-cols-2">
        <ResourceList
          title={t('resources.availableVehicles')}
          emptyLabel={t('resources.noIdleVehicles')}
          items={availableVehicles.map((vehicle) => ({
            id: vehicle.id,
            label: vehicle.registrationNumber,
            badge: t('resources.idle'),
          }))}
        />
        <ResourceList
          title={t('resources.availableDrivers')}
          emptyLabel={t('resources.noAvailableDrivers')}
          items={availableDrivers.map((driver) => ({
            id: driver.id,
            label: driver.name,
            badge: t('resources.available'),
          }))}
        />
      </CardContent>
    </Card>
  );
}

function ResourceList({
  title,
  emptyLabel,
  items,
}: {
  title: string;
  emptyLabel: string;
  items: Array<{ id: string; label: string; badge: string }>;
}) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium">{title}</p>
      <div className="space-y-2">
        {items.length === 0 ? (
          <div className="rounded-lg border border-dashed p-3 text-sm text-slate-600">{emptyLabel}</div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="flex items-center justify-between rounded-lg border p-2">
              <span className="text-sm">{item.label}</span>
              <Badge variant="secondary">{item.badge}</Badge>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
