import type {
  DriverRead,
  RouteRead,
  TripCreate,
  TripRead,
  VehicleRead,
} from '../../../lib/api-types';

export type ScheduleTripFormState = {
  vehicleId: string;
  routeId: string;
  driverId: string;
  scheduledStart: string;
  scheduledEnd: string;
};

export type DispatchStats = {
  activeTrips: number;
  scheduledTrips: number;
  availableVehicles: number;
  availableDrivers: number;
};

export const initialScheduleTripFormState: ScheduleTripFormState = {
  vehicleId: '',
  routeId: '',
  driverId: '',
  scheduledStart: defaultDateTimeLocal(30),
  scheduledEnd: defaultDateTimeLocal(90),
};

export function buildTripCreatePayload(form: ScheduleTripFormState): TripCreate {
  return {
    vehicleId: form.vehicleId,
    routeId: form.routeId,
    driverId: form.driverId,
    scheduledStart: new Date(form.scheduledStart).toISOString(),
    scheduledEnd: new Date(form.scheduledEnd).toISOString(),
  };
}

export function calculateDispatchStats(
  trips: TripRead[],
  availableVehicles: VehicleRead[],
  availableDrivers: DriverRead[],
): DispatchStats {
  return {
    activeTrips: trips.filter((trip) => trip.status === 'active').length,
    scheduledTrips: trips.filter((trip) => trip.status === 'scheduled').length,
    availableVehicles: availableVehicles.length,
    availableDrivers: availableDrivers.length,
  };
}

export function routeLabel(route?: RouteRead): string {
  if (!route) return 'Unknown route';
  return `${route.number} - ${route.name}`;
}

export function formatTripTime(value: string | null): string {
  if (!value) return '-';
  return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function defaultDateTimeLocal(offsetMinutes: number): string {
  const date = new Date(Date.now() + offsetMinutes * 60 * 1000);
  date.setSeconds(0, 0);
  return date.toISOString().slice(0, 16);
}
