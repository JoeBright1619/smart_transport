import { useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker } from 'react-leaflet';
import type { Marker as LMarker } from 'leaflet';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Battery, AlertCircle } from 'lucide-react';
import type { RouteRead, DriverRead } from '../../../lib/api-types';
import { createVehicleIcon, occupancyColor, MapController } from './vehicle-tracking-helpers';
import type { TrackedVehicle } from './vehicle-tracking-helpers';

const MAP_CENTER: [number, number] = [-1.9536, 30.0606];

type Props = {
  vehicles: TrackedVehicle[];
  routes: RouteRead[];
  drivers: DriverRead[];
  selectedVehicle: TrackedVehicle | null;
  selectedRoute: RouteRead | null;
  markerRefs: React.MutableRefObject<Map<string, LMarker>>;
  onSelectVehicle: (v: TrackedVehicle) => void;
};

export function VehicleMapView({ vehicles, routes, drivers, selectedVehicle, selectedRoute, markerRefs, onSelectVehicle }: Props) {
  const { t } = useTranslation('tracking');
  const noGpsCount = vehicles.filter(v => !v.currentLocation).length;

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{t('liveMapView')}</CardTitle>
          {noGpsCount > 0 && (
            <span className="text-xs text-slate-400">
              {t('noGpsSummary', { count: noGpsCount })}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative h-[600px] rounded-lg overflow-hidden border">
          <MapContainer center={MAP_CENTER} zoom={13} style={{ height: '100%', width: '100%' }} scrollWheelZoom>
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />
            <MapController selectedVehicle={selectedVehicle} />

            {routes.map((route) => {
              const highlighted = selectedVehicle?.routeId === route.id;
              return (
                <Polyline
                  key={route.id}
                  positions={route.stops.map(s => [s.lat, s.lng] as [number, number])}
                  color={highlighted ? route.color : route.color}
                  weight={highlighted ? 5 : 2}
                  opacity={highlighted ? 0.9 : 0.45}
                />
              );
            })}

            {selectedRoute?.stops.map((stop) => {
              const isAt = stop.name === selectedVehicle?.atStop;
              const isNext = !isAt && stop.name === selectedVehicle?.nextStopName;
              return (
                <CircleMarker key={stop.id} center={[stop.lat, stop.lng]}
                  radius={isAt || isNext ? 9 : 6}
                  fillColor={isAt || isNext ? '#F59E0B' : '#3B82F6'}
                  color={isAt ? '#D97706' : 'white'} weight={isAt ? 3 : 2} fillOpacity={0.9}>
                  <Popup>
                    <p className="font-medium text-sm">{stop.name}</p>
                    {isAt && <p className="text-xs text-amber-600 mt-0.5">{t('busStoppedHere')}</p>}
                    {isNext && <p className="text-xs text-blue-600 mt-0.5">{t('nextStop')}</p>}
                  </Popup>
                </CircleMarker>
              );
            })}

            {vehicles.map((vehicle) => {
              if (!vehicle.currentLocation) return null;
              const isSelected = selectedVehicle?.id === vehicle.id;
              const driver = drivers.find(d => d.id === vehicle.driverId);
              const route = routes.find(r => r.id === vehicle.routeId);
              const occupancyRatio = vehicle.seatingCapacity > 0
                ? vehicle.currentOccupancy / vehicle.seatingCapacity
                : 0;
              return (
                <Marker
                  key={vehicle.id}
                  position={[vehicle.currentLocation.lat, vehicle.currentLocation.lng]}
                  icon={createVehicleIcon(vehicle.status, vehicle.heading ?? 0, isSelected, occupancyRatio)}
                  zIndexOffset={isSelected ? 1000 : 0}
                  ref={(m) => { if (m) markerRefs.current.set(vehicle.id, m); else markerRefs.current.delete(vehicle.id); }}
                  eventHandlers={{ click: () => onSelectVehicle(vehicle) }}
                >
                  <Popup>
                    <div className="p-2 space-y-1">
                      <p className="font-bold">{vehicle.registrationNumber}</p>
                      <p className="text-sm text-slate-600">{vehicle.model}</p>
                      {route && <p className="text-sm text-blue-600">{t('routeFull', { number: route.number, name: route.name })}</p>}
                      {driver && <p className="text-sm">{t('driver', { name: driver.name })}</p>}
                      {vehicle.atStop
                        ? <p className="text-sm font-medium text-amber-600">{t('atStop', { stop: vehicle.atStop })}</p>
                        : vehicle.nextStopName && <p className="text-sm text-amber-600">{t('next', { stop: vehicle.nextStopName })}</p>
                      }
                      {vehicle.status === 'active' && (
                        <p className="text-sm" style={{ color: occupancyColor(occupancyRatio) }}>
                          {t('occupancyLine', { current: vehicle.currentOccupancy, capacity: vehicle.seatingCapacity, remaining: vehicle.remainingSeats })}
                        </p>
                      )}
                      <Badge variant={vehicle.status === 'active' ? 'default' : vehicle.status === 'maintenance' ? 'destructive' : 'secondary'}>
                        {t(`fleet:vehicleStatus.${vehicle.status}`)}
                      </Badge>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>

          <div className="absolute bottom-4 left-4 z-[1000] bg-white/95 backdrop-blur-sm rounded-lg shadow-md p-3 text-xs space-y-1.5 pointer-events-none">
            <p className="font-semibold text-slate-700">{t('legend')}</p>
            {[['bg-green-500', t('legendActive')],['bg-yellow-500', t('legendIdle')],['bg-red-500', t('legendMaintenance')],['bg-slate-400', t('legendOffline')]].map(([cls, label]) => (
              <div key={label} className="flex items-center gap-2"><span className={`size-2.5 rounded-full ${cls} shrink-0`}/><span>{label}</span></div>
            ))}
            {selectedVehicle && (
              <div className="border-t border-slate-200 pt-1 space-y-1.5">
                <div className="flex items-center gap-2"><span className="size-2.5 rounded-full border-2 border-blue-500 shrink-0"/><span>{t('selected')}</span></div>
                <div className="flex items-center gap-2"><span className="size-2.5 rounded-full bg-blue-500 shrink-0"/><span>{t('routeStop')}</span></div>
                <div className="flex items-center gap-2"><span className="size-2.5 rounded-full bg-amber-500 shrink-0"/><span>{t('nextStop')}</span></div>
              </div>
            )}
          </div>
        </div>

        {selectedVehicle && (
          <Card className="mt-4">
            <CardContent className="pt-4">
              <div className="grid gap-4 md:grid-cols-4">
                <div>
                  <p className="text-xs text-slate-500">{t('vehicle')}</p>
                  <p className="font-medium">{selectedVehicle.registrationNumber}</p>
                  <p className="text-sm text-slate-600">{selectedVehicle.model}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">{t('status')}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={selectedVehicle.status === 'active' ? 'default' : selectedVehicle.status === 'maintenance' ? 'destructive' : 'secondary'}>
                      {t(`fleet:vehicleStatus.${selectedVehicle.status}`)}
                    </Badge>
                    {selectedVehicle.status === 'active' && selectedVehicle.speed !== null && (
                      <span className="text-sm">{t('kmh', { speed: Math.round(selectedVehicle.speed) })}</span>
                    )}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-slate-500">{t('fuelEngine')}</p>
                  <div className="flex items-center gap-3 mt-1">
                    {selectedVehicle.fuel !== null && (
                      <span className="flex items-center gap-1 text-sm"><Battery className="size-4"/>{selectedVehicle.fuel}%</span>
                    )}
                    <span className="flex items-center gap-1 text-sm">
                      <AlertCircle className={`size-4 ${selectedVehicle.engineStatus === 'good' ? 'text-green-500' : selectedVehicle.engineStatus === 'warning' ? 'text-yellow-500' : 'text-red-500'}`}/>
                      {t(`fleet:engineStatus.${selectedVehicle.engineStatus}`)}
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-slate-500">{selectedVehicle.atStop ? t('atStopLabel') : t('nextStopLabel')}</p>
                  {selectedVehicle.atStop ? (
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className="inline-block size-2 shrink-0 rounded-full bg-amber-500 animate-pulse" />
                      <p className="font-medium text-sm text-amber-600">{selectedVehicle.atStop}</p>
                    </div>
                  ) : (
                    <>
                      <p className="font-medium text-sm mt-1">{selectedVehicle.nextStopName || '—'}</p>
                      {selectedVehicle.progressPct !== undefined && (
                        <p className="text-xs text-slate-400">{t('progressToStop', { pct: selectedVehicle.progressPct })}</p>
                      )}
                    </>
                  )}
                </div>
              </div>
              {selectedVehicle.status === 'active' && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <p className="text-xs text-slate-500 mb-1">{t('occupancy')}</p>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                      {(() => {
                        const ratio = selectedVehicle.seatingCapacity > 0
                          ? selectedVehicle.currentOccupancy / selectedVehicle.seatingCapacity
                          : 0;
                        return (
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(100, ratio * 100)}%`, backgroundColor: occupancyColor(ratio) }}
                          />
                        );
                      })()}
                    </div>
                    <span className="text-sm shrink-0">
                      {t('occupancyLine', { current: selectedVehicle.currentOccupancy, capacity: selectedVehicle.seatingCapacity, remaining: selectedVehicle.remainingSeats })}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  );
}
