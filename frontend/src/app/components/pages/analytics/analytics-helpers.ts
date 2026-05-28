import type {
  AnalyticsDaily,
  AnalyticsData,
  RouteRead,
  TripRead,
  VehicleRead,
} from '../../../lib/api-types';

export type AnalyticsTrends = {
  revenueChange: string;
  passengerChange: string;
};

export type FleetStatusDatum = {
  name: string;
  value: number;
  color: string;
};

export type RoutePerformanceDatum = {
  id: string;
  name: string;
  number: string;
  color: string;
  passengers: number;
  trips: number;
  avgPassengers: number;
};

export function defaultDateRange() {
  const to = new Date();
  const from = new Date();
  from.setDate(to.getDate() - 6);

  return {
    from: toDateInputValue(from),
    to: toDateInputValue(to),
  };
}

export function calculateTrends(daily: AnalyticsDaily[]): AnalyticsTrends {
  const first = daily[0];
  const last = daily[daily.length - 1];

  return {
    revenueChange: percentageChange(first?.revenue ?? 0, last?.revenue ?? 0),
    passengerChange: percentageChange(first?.totalPassengers ?? 0, last?.totalPassengers ?? 0),
  };
}

export function buildRoutePerformance(
  routes: RouteRead[],
  trips: TripRead[],
): RoutePerformanceDatum[] {
  return routes.map((route) => {
    const routeTrips = trips.filter((trip) => trip.routeId === route.id);
    const passengers = routeTrips.reduce((sum, trip) => sum + trip.passengers, 0);

    return {
      id: route.id,
      name: route.name,
      number: route.number,
      color: route.color,
      passengers,
      trips: routeTrips.length,
      avgPassengers: routeTrips.length > 0 ? Math.round(passengers / routeTrips.length) : 0,
    };
  });
}

export function buildFleetStatus(vehicles: VehicleRead[]): FleetStatusDatum[] {
  return [
    { name: 'Active', value: countVehicles(vehicles, 'active'), color: '#10B981' },
    { name: 'Idle', value: countVehicles(vehicles, 'idle'), color: '#F59E0B' },
    { name: 'Maintenance', value: countVehicles(vehicles, 'maintenance'), color: '#EF4444' },
    { name: 'Offline', value: countVehicles(vehicles, 'offline'), color: '#6B7280' },
  ];
}

export function formatRevenue(value: number): string {
  const rounded = Math.round(value);

  if (rounded >= 1000000) {
    return `${(rounded / 1000000).toFixed(1)}M RWF`;
  }

  if (rounded >= 1000) {
    return `${Math.round(rounded / 1000).toLocaleString()}K RWF`;
  }

  return `${rounded.toLocaleString()} RWF`;
}

export function formatPassengers(value: number): string {
  const rounded = Math.round(value);

  if (rounded >= 1000) {
    return `${Math.round(rounded / 1000).toLocaleString()}K`;
  }

  return rounded.toLocaleString();
}

export function averageDailyFuel(summaryFuel: number, dayCount: number): number {
  const days = Math.max(dayCount, 1);
  return Math.round(summaryFuel / days);
}

function percentageChange(first: number, last: number): string {
  if (!first) return '0.0';
  return (((last - first) / first) * 100).toFixed(1);
}

function countVehicles(vehicles: VehicleRead[], status: VehicleRead['status']): number {
  return vehicles.filter((vehicle) => vehicle.status === status).length;
}

function toDateInputValue(date: Date): string {
  return date.toISOString().slice(0, 10);
}
