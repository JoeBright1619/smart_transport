import type {
  DriverRead,
  RouteRead,
  TripCreate,
  TripRead,
  VehicleRead,
} from '../../../lib/api-types';
import { formatTime } from '../../../lib/format';

export type ScheduleTripFormState = {
  vehicleId: string;
  routeId: string;
  driverId: string;
  scheduledStart: string;
  plannedLoops: string;
};

export type DispatchStats = {
  activeTrips: number;
  scheduledTrips: number;
  availableVehicles: number;
  availableDrivers: number;
};

export const DEFAULT_TRIP_ROUNDS = 5;

export const initialScheduleTripFormState: ScheduleTripFormState = {
  vehicleId: '',
  routeId: '',
  driverId: '',
  scheduledStart: defaultDateTimeLocal(30),
  plannedLoops: String(DEFAULT_TRIP_ROUNDS),
};

export function buildTripCreatePayload(form: ScheduleTripFormState): TripCreate {
  const rounds = Number(form.plannedLoops);
  // scheduledEnd is intentionally omitted — the server derives it from the route's
  // duration and the rounds count.
  return {
    vehicleId: form.vehicleId,
    routeId: form.routeId,
    driverId: form.driverId,
    scheduledStart: new Date(form.scheduledStart).toISOString(),
    plannedLoops: rounds > 0 ? rounds : DEFAULT_TRIP_ROUNDS,
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
  return formatTime(value);
}

function defaultDateTimeLocal(offsetMinutes: number): string {
  const date = new Date(Date.now() + offsetMinutes * 60 * 1000);
  date.setSeconds(0, 0);
  return date.toISOString().slice(0, 16);
}
