import type { RouteCreate, RouteRead } from '../../../lib/api-types';

export type RouteFormStop = {
  key: string;
  stopId: string;
  name: string;
  lat: number;
  lng: number;
  order: number;
};

export type RouteFormState = {
  name: string;
  number: string;
  distance: string;
  duration: string;
  color: string;
  stops: RouteFormStop[];
};

export type RouteStats = {
  totalRoutes: number;
  activeRoutes: number;
  totalDistance: number;
  avgDuration: number;
  totalStops: number;
};

export const initialRouteFormState: RouteFormState = {
  name: '',
  number: '',
  distance: '',
  duration: '',
  color: '#3B82F6',
  stops: [],
};

export function createEmptyStop(order: number): RouteFormStop {
  return {
    key: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${order}`,
    stopId: '',
    name: '',
    lat: 0,
    lng: 0,
    order,
  };
}

export function getRouteStats(routes: RouteRead[]): RouteStats {
  const totalRoutes = routes.length;
  const totalDuration = routes.reduce((sum, route) => sum + route.duration, 0);

  return {
    totalRoutes,
    activeRoutes: routes.filter((route) => route.isActive).length,
    totalDistance: routes.reduce((sum, route) => sum + route.distance, 0),
    avgDuration: totalRoutes > 0 ? Math.round(totalDuration / totalRoutes) : 0,
    totalStops: routes.reduce((sum, route) => sum + route.stops.length, 0),
  };
}

export function toRouteCreatePayload(form: RouteFormState): RouteCreate {
  return {
    name: form.name.trim(),
    number: form.number.trim(),
    distance: Number(form.distance),
    duration: Number(form.duration),
    color: form.color,
    stops: form.stops.map((stop, index) => ({
      stopId: stop.stopId,
      order: index + 1,
    })),
  };
}

// Duration estimate assumptions. A city bus that stops at every stop averages well below
// road speed, so duration is modelled as travel at an urban average speed plus a fixed
// dwell at each stop — not distance-as-minutes (which implied an unrealistic 60 km/h).
export const AVG_ROUTE_SPEED_KMH = 20;
export const DWELL_MINUTES_PER_STOP = 1;

/** Estimate route duration in minutes from total distance (km) and number of stops. */
export function estimateRouteDurationMinutes(distanceKm: number, stopCount: number): number {
  const travelMinutes = (distanceKm / AVG_ROUTE_SPEED_KMH) * 60;
  const dwellMinutes = stopCount * DWELL_MINUTES_PER_STOP;
  return Math.round(travelMinutes + dwellMinutes);
}

export function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth radius in km
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}
