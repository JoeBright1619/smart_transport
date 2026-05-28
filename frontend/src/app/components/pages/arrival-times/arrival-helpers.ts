import type { ArrivalEstimate, RouteRead, StopRead } from '../../../lib/api-types';

export const ALL_STOPS_ID = '__all__';

export type StopOption = StopRead & {
  routeIds: string[];
  routeLabels: string[];
};

export type ArrivalEstimateWithStop = ArrivalEstimate & {
  stopId?: string;
  stopName?: string;
};

export function collectStops(routes: RouteRead[]): StopOption[] {
  const stopsById = new Map<string, StopOption>();

  routes.forEach((route) => {
    route.stops.forEach((stop) => {
      const current = stopsById.get(stop.id);
      const routeLabel = `${route.number} - ${route.name}`;

      if (current) {
        current.routeIds.push(route.id);
        current.routeLabels.push(routeLabel);
        return;
      }

      stopsById.set(stop.id, {
        ...stop,
        routeIds: [route.id],
        routeLabels: [routeLabel],
      });
    });
  });

  return [...stopsById.values()].sort((a, b) => a.name.localeCompare(b.name));
}

export function sortArrivals<T extends ArrivalEstimate>(estimates: T[]): T[] {
  return [...estimates].sort((a, b) => {
    if (a.etaMinutes === null && b.etaMinutes === null) return 0;
    if (a.etaMinutes === null) return 1;
    if (b.etaMinutes === null) return -1;
    return a.etaMinutes - b.etaMinutes;
  });
}

export function etaLabel(estimate: ArrivalEstimate): string {
  if (estimate.etaMinutes === null) return 'Stopped';
  if (estimate.etaMinutes <= 1) return 'Arriving';
  return `${estimate.etaMinutes} min`;
}

export function formatLastUpdated(value: Date | null): string {
  if (!value) return 'Not refreshed yet';
  return `Updated ${value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}
