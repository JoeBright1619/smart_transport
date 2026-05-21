import type { RouteCreate, RouteRead, StopCreate } from '../../../lib/api-types';

export type RouteFormStop = StopCreate & {
  key: string;
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
  stops: [createEmptyStop(1)],
};

export function createEmptyStop(order: number): RouteFormStop {
  return {
    key: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${order}`,
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
    activeRoutes: routes.filter((route) => route.is_active).length,
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
      name: stop.name.trim(),
      lat: Number(stop.lat),
      lng: Number(stop.lng),
      order: index + 1,
    })),
  };
}
