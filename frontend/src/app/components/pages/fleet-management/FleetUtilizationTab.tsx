import type { DriverRead, RouteRead, VehicleRead } from '../../../lib/api-types';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { fuelBarClass, getUtilization } from './fleet-helpers';

type FleetUtilizationTabProps = {
  vehicles: VehicleRead[];
  driversById: Map<string, DriverRead>;
  routesById: Map<string, RouteRead>;
};

export function FleetUtilizationTab({
  vehicles,
  driversById,
  routesById,
}: FleetUtilizationTabProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Fleet Utilization</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {vehicles.map((vehicle) => {
            const utilization = getUtilization(vehicle.status);
            return (
              <div key={vehicle.id}>
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-sm font-medium">{vehicle.registrationNumber}</span>
                  <span className="text-sm text-slate-600">{utilization}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-200">
                  <div className="h-full rounded-full bg-blue-600" style={{ width: `${utilization}%` }} />
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {driversById.get(vehicle.driverId ?? '')?.name ?? 'No driver'} -{' '}
                  {routesById.get(vehicle.routeId ?? '')?.number ?? 'No route'}
                </p>
              </div>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Average Fuel Levels</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {vehicles.map((vehicle) => {
              const fuel = vehicle.fuel ?? 0;
              return (
                <div key={vehicle.id}>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-sm font-medium">{vehicle.registrationNumber}</span>
                    <span className="text-sm text-slate-600">{fuel}%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-200">
                    <div className={`h-full rounded-full ${fuelBarClass(vehicle.fuel)}`} style={{ width: `${fuel}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
