import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { ApiError } from '../../../lib/api-client';
import type { DriverRead, RouteRead, TripCreate, TripRead, TripStatus, VehicleRead } from '../../../lib/api-types';
import * as driversService from '../../../services/drivers.service';
import * as routesService from '../../../services/routes.service';
import * as tripsService from '../../../services/trips.service';
import * as vehiclesService from '../../../services/vehicles.service';
import { calculateDispatchStats } from './dispatch-helpers';

export function useDispatchManagement() {
  const [trips, setTrips] = useState<TripRead[]>([]);
  const [vehicles, setVehicles] = useState<VehicleRead[]>([]);
  const [drivers, setDrivers] = useState<DriverRead[]>([]);
  const [routes, setRoutes] = useState<RouteRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingTripId, setUpdatingTripId] = useState<string | null>(null);

  const loadDispatch = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [tripsResult, vehiclesResult, driversResult, routesResult] = await Promise.all([
        tripsService.listTrips({ pageSize: 100 }),
        vehiclesService.listVehicles({ pageSize: 100 }),
        driversService.listDrivers({ pageSize: 100 }),
        routesService.listRoutes({ pageSize: 100 }),
      ]);
      setTrips(tripsResult.items);
      setVehicles(vehiclesResult.items);
      setDrivers(driversResult.items);
      setRoutes(routesResult.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load dispatch data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDispatch();
  }, [loadDispatch]);

  const activeTrips = useMemo(() => trips.filter((trip) => trip.status === 'active'), [trips]);
  const scheduledTrips = useMemo(() => trips.filter((trip) => trip.status === 'scheduled'), [trips]);
  const availableVehicles = useMemo(() => vehicles.filter((vehicle) => vehicle.status === 'idle'), [vehicles]);
  const availableDrivers = useMemo(() => drivers.filter((driver) => driver.status === 'available'), [drivers]);
  const vehiclesById = useMemo(() => new Map(vehicles.map((vehicle) => [vehicle.id, vehicle])), [vehicles]);
  const driversById = useMemo(() => new Map(drivers.map((driver) => [driver.id, driver])), [drivers]);
  const routesById = useMemo(() => new Map(routes.map((route) => [route.id, route])), [routes]);
  const stats = useMemo(
    () => calculateDispatchStats(trips, availableVehicles, availableDrivers),
    [availableDrivers, availableVehicles, trips],
  );

  const createTrip = async (payload: TripCreate) => {
    try {
      const createdTrip = await tripsService.createTrip(payload);
      setTrips((current) => [createdTrip, ...current]);
      toast.success('Trip scheduled');
    } catch (createError) {
      if (createError instanceof ApiError && [409, 422].includes(createError.status ?? 0)) {
        toast.error(createError.message);
        return;
      }
      toast.error(createError instanceof Error ? createError.message : 'Unable to schedule trip');
    }
  };

  const updateTripStatus = async (tripId: string, status: TripStatus) => {
    setUpdatingTripId(tripId);

    try {
      const updatedTrip = await tripsService.updateTripStatus(tripId, status);
      setTrips((current) => current.map((trip) => (trip.id === updatedTrip.id ? updatedTrip : trip)));
      await loadDispatch();
      toast.success('Trip status updated');
    } catch (updateError) {
      toast.error(updateError instanceof Error ? updateError.message : 'Unable to update trip');
    } finally {
      setUpdatingTripId(null);
    }
  };

  return {
    activeTrips,
    scheduledTrips,
    availableVehicles,
    availableDrivers,
    routes,
    vehiclesById,
    driversById,
    routesById,
    loading,
    error,
    updatingTripId,
    stats,
    createTrip,
    updateTripStatus,
    retry: loadDispatch,
  };
}
