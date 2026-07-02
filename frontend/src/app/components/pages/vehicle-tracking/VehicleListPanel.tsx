import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Input } from '../../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Search, Gauge, Battery } from 'lucide-react';
import type { RouteRead, DriverRead } from '../../../lib/api-types';
import { occupancyColor } from './vehicle-tracking-helpers';
import type { TrackedVehicle } from './vehicle-tracking-helpers';

type Props = {
  vehicles: TrackedVehicle[];
  drivers: DriverRead[];
  routes: RouteRead[];
  selectedVehicle: TrackedVehicle | null;
  searchTerm: string;
  statusFilter: string;
  onSelectVehicle: (v: TrackedVehicle) => void;
  onSearchChange: (s: string) => void;
  onStatusFilterChange: (s: string) => void;
};

export function VehicleListPanel({
  vehicles, drivers, routes, selectedVehicle,
  searchTerm, statusFilter,
  onSelectVehicle, onSearchChange, onStatusFilterChange,
}: Props) {
  const { t } = useTranslation('tracking');
  return (
    <Card className="lg:col-span-1">
      <CardHeader>
        <CardTitle>{t('fleetVehicles', { count: vehicles.length })}</CardTitle>
        <div className="space-y-2 mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder={t('searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={statusFilter} onValueChange={onStatusFilterChange}>
            <SelectTrigger>
              <SelectValue placeholder={t('filterByStatus')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('allStatus')}</SelectItem>
              <SelectItem value="active">{t('fleet:vehicleStatus.active')}</SelectItem>
              <SelectItem value="idle">{t('fleet:vehicleStatus.idle')}</SelectItem>
              <SelectItem value="maintenance">{t('fleet:vehicleStatus.maintenance')}</SelectItem>
              <SelectItem value="offline">{t('fleet:vehicleStatus.offline')}</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent className="max-h-[600px] overflow-y-auto">
        <div className="space-y-2">
          {vehicles.map((vehicle) => {
            const driver = drivers.find(d => d.id === vehicle.driverId);
            const route = routes.find(r => r.id === vehicle.routeId);
            const isSelected = selectedVehicle?.id === vehicle.id;
            return (
              <div
                key={vehicle.id}
                onClick={() => onSelectVehicle(vehicle)}
                className={`cursor-pointer rounded-lg border p-3 transition-colors ${
                  isSelected ? 'border-blue-500 bg-blue-50 shadow-sm' : 'hover:bg-slate-50'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <div className={`size-2 rounded-full shrink-0 ${
                        vehicle.status === 'active' ? 'bg-green-500' :
                        vehicle.status === 'idle' ? 'bg-yellow-500' :
                        vehicle.status === 'maintenance' ? 'bg-red-500' : 'bg-slate-400'
                      }`} />
                      <p className="font-medium text-sm">{vehicle.registrationNumber}</p>
                      {!vehicle.currentLocation && (
                        <span className="text-xs text-slate-400 italic">{t('noGpsFix')}</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{vehicle.model}</p>
                    {route && <p className="text-xs text-blue-600 mt-1">{t('route', { number: route.number })}</p>}
                    {vehicle.atStop ? (
                      <div className="mt-1 flex items-center gap-1.5">
                        <span className="inline-block size-2 shrink-0 rounded-full bg-amber-500 animate-pulse" />
                        <p className="text-xs font-medium text-amber-600">{t('atStop', { stop: vehicle.atStop })}</p>
                      </div>
                    ) : vehicle.nextStopName ? (
                      <div className="mt-1">
                        <p className="text-xs text-slate-500">{t('next', { stop: vehicle.nextStopName })}</p>
                        <div className="mt-0.5 h-1 w-full rounded-full bg-slate-200">
                          <div
                            className="h-full rounded-full bg-blue-500"
                            style={{ width: `${vehicle.progressPct ?? 0}%` }}
                          />
                        </div>
                      </div>
                    ) : null}
                    {driver && <p className="text-xs text-slate-500">{driver.name}</p>}
                  </div>
                  <Badge
                    variant={
                      vehicle.status === 'active' ? 'default' :
                      vehicle.status === 'maintenance' ? 'destructive' : 'secondary'
                    }
                    className="shrink-0"
                  >
                    {t(`fleet:vehicleStatus.${vehicle.status}`)}
                  </Badge>
                </div>
                {vehicle.status === 'active' && vehicle.speed !== null && vehicle.fuel !== null && (
                  <div className="mt-2 flex items-center gap-3 text-xs text-slate-600">
                    <span className="flex items-center gap-1"><Gauge className="size-3" />{t('kmh', { speed: Math.round(vehicle.speed) })}</span>
                    <span className="flex items-center gap-1"><Battery className="size-3" />{vehicle.fuel}%</span>
                  </div>
                )}
                {vehicle.status === 'active' ? (
                  <div className="mt-2">
                    {(() => {
                      const ratio = vehicle.seatingCapacity > 0
                        ? vehicle.currentOccupancy / vehicle.seatingCapacity
                        : 0;
                      return (
                        <>
                          <div className="flex justify-between text-xs text-slate-500 mb-0.5">
                            <span>{t('seats', { current: vehicle.currentOccupancy, capacity: vehicle.seatingCapacity })}</span>
                            <span>{t('remaining', { count: vehicle.remainingSeats })}</span>
                          </div>
                          <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(100, ratio * 100)}%`, backgroundColor: occupancyColor(ratio) }}
                            />
                          </div>
                        </>
                      );
                    })()}
                  </div>
                ) : (
                  <p className="mt-1.5 text-xs text-slate-400 italic">{t('notInService')}</p>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
