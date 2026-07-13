import { useCallback, useEffect, useState } from 'react';
import type { DriverRead, RouteRead, TripRead, TripStatus, VehicleRead } from '../../../lib/api-types';
import { messageForError } from '../../../lib/error-messages';
import * as driversService from '../../../services/drivers.service';
import * as routesService from '../../../services/routes.service';
import * as tripsService from '../../../services/trips.service';
import * as vehiclesService from '../../../services/vehicles.service';

const PAGE_SIZE = 15;

export type TripStatusFilter = 'all' | TripStatus;

export function useTripsHistory() {
  const [trips, setTrips] = useState<TripRead[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatusState] = useState<TripStatusFilter>('all');
  const [vehiclesById, setVehiclesById] = useState<Map<string, VehicleRead>>(new Map());
  const [driversById, setDriversById] = useState<Map<string, DriverRead>>(new Map());
  const [routesById, setRoutesById] = useState<Map<string, RouteRead>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Reference data (names for the vehicle/driver/route ids on each trip) is loaded once —
  // it doesn't change as you page through history.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const [vehicles, drivers, routes] = await Promise.all([
          vehiclesService.listVehicles({ pageSize: 100 }),
          driversService.listDrivers({ pageSize: 100 }),
          routesService.listRoutes({ pageSize: 100 }),
        ]);
        if (cancelled) return;
        setVehiclesById(new Map(vehicles.items.map((v) => [v.id, v])));
        setDriversById(new Map(drivers.items.map((d) => [d.id, d])));
        setRoutesById(new Map(routes.items.map((r) => [r.id, r])));
      } catch {
        // Names just fall back to ids if reference data fails; not fatal for the list.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const loadTrips = useCallback(async () => {
    setLoading(true);
    try {
      const result = await tripsService.listTrips({
        page,
        pageSize: PAGE_SIZE,
        status: status === 'all' ? undefined : status,
      });
      setTrips(result.items);
      setTotal(result.total);
      setError(null);
    } catch (loadError) {
      setError(messageForError(loadError));
    } finally {
      setLoading(false);
    }
  }, [page, status]);

  useEffect(() => {
    void loadTrips();
  }, [loadTrips]);

  const setStatus = (value: TripStatusFilter) => {
    setPage(1);
    setStatusState(value);
  };

  return {
    trips,
    total,
    page,
    pageSize: PAGE_SIZE,
    status,
    vehiclesById,
    driversById,
    routesById,
    loading,
    error,
    setPage,
    setStatus,
    retry: loadTrips,
  };
}
