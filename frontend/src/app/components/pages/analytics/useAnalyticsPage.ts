import { useCallback, useEffect, useMemo, useState } from 'react';
import type { AnalyticsData, RouteRead, TripRead, VehicleRead } from '../../../lib/api-types';
import * as analyticsService from '../../../services/analytics.service';
import * as routesService from '../../../services/routes.service';
import * as tripsService from '../../../services/trips.service';
import * as vehiclesService from '../../../services/vehicles.service';
import {
  buildFleetStatus,
  buildRoutePerformance,
  calculateTrends,
  defaultDateRange,
} from './analytics-helpers';

const initialRange = defaultDateRange();

export function useAnalyticsPage() {
  const [from, setFrom] = useState(initialRange.from);
  const [to, setTo] = useState(initialRange.to);
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [vehicles, setVehicles] = useState<VehicleRead[]>([]);
  const [routes, setRoutes] = useState<RouteRead[]>([]);
  const [trips, setTrips] = useState<TripRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [analyticsData, vehiclesResult, routesResult, tripsResult] = await Promise.all([
        analyticsService.getAnalytics({ from, to }),
        vehiclesService.listVehicles({ pageSize: 100 }),
        routesService.listRoutes({ pageSize: 100 }),
        tripsService.listTrips({ pageSize: 100 }),
      ]);
      setData(analyticsData);
      setVehicles(vehiclesResult.items);
      setRoutes(routesResult.items);
      setTrips(tripsResult.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load analytics');
    } finally {
      setLoading(false);
    }
  }, [from, to]);

  useEffect(() => {
    void loadAnalytics();
  }, [loadAnalytics]);

  const trends = useMemo(() => calculateTrends(data?.daily ?? []), [data]);
  const routePerformance = useMemo(() => buildRoutePerformance(routes, trips), [routes, trips]);
  const fleetStatus = useMemo(() => buildFleetStatus(vehicles), [vehicles]);

  return {
    data,
    from,
    to,
    loading,
    error,
    trends,
    routePerformance,
    fleetStatus,
    fleetHealth: vehicles,
    setFrom,
    setTo,
    retry: loadAnalytics,
  };
}
