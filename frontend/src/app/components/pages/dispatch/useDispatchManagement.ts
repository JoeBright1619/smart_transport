import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { messageForError } from '../../../lib/error-messages';
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
      setError(messageForError(loadError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDispatch();
  }, [loadDispatch]);

  const activeTrips = useMemo(() => trips.filter((trip) => trip.status === 'active'), [trips]);
  const scheduledTrips = useMemo(() => trips.filter((trip) => trip.status === 'scheduled'), [trips]);

  const bookedVehicleIds = useMemo(
    () => new Set([...activeTrips, ...scheduledTrips].map((t) => t.vehicleId)),
    [activeTrips, scheduledTrips],
  );
  const bookedDriverIds = useMemo(
    () => new Set([...activeTrips, ...scheduledTrips].map((t) => t.driverId)),
    [activeTrips, scheduledTrips],
  );

  const availableVehicles = useMemo(
    () => vehicles.filter((v) => v.status === 'idle' && !bookedVehicleIds.has(v.id)),
    [vehicles, bookedVehicleIds],
  );
  const availableDrivers = useMemo(
    () => drivers.filter((d) => d.status === 'available' && !bookedDriverIds.has(d.id)),
    [drivers, bookedDriverIds],
  );
  const schedulableRoutes = useMemo(() => routes.filter((r) => r.isActive), [routes]);
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
      await loadDispatch();
      toast.success('Trip scheduled');
    } catch (createError) {
      toast.error(messageForError(createError));
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
      toast.error(messageForError(updateError));
    } finally {
      setUpdatingTripId(null);
    }
  };

  return {
    activeTrips,
    scheduledTrips,
    availableVehicles,
    availableDrivers,
    schedulableRoutes,
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
