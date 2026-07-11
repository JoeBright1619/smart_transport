import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import type {
  DriverRead,
  RouteRead,
  VehicleCreate,
  VehicleRead,
  VehicleUpdate,
} from '../../../lib/api-types';
import * as driversService from '../../../services/drivers.service';
import * as routesService from '../../../services/routes.service';
import * as vehiclesService from '../../../services/vehicles.service';
import { getFleetStats } from './fleet-helpers';

export type FleetFormState = {
  registrationNumber: string;
  model: string;
  seatingCapacity: string;
  status: VehicleCreate['status'];
};

export const initialFleetFormState: FleetFormState = {
  registrationNumber: '',
  model: '',
  seatingCapacity: '45',
  status: 'idle',
};

export function useFleetManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  const [vehicles, setVehicles] = useState<VehicleRead[]>([]);
  const [drivers, setDrivers] = useState<DriverRead[]>([]);
  const [routes, setRoutes] = useState<RouteRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<FleetFormState>(initialFleetFormState);
  const [submitting, setSubmitting] = useState(false);
  const [updatingVehicleId, setUpdatingVehicleId] = useState<string | null>(null);

  const fetchFleetData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [vehicleResult, driverResult, routeResult] = await Promise.all([
        vehiclesService.listVehicles({ pageSize: 100 }),
        driversService.listDrivers({ pageSize: 100 }),
        // Only active routes are assignable to vehicles — disabled routes are excluded.
        routesService.listRoutes({ pageSize: 100, isActive: true }),
      ]);

      setVehicles(vehicleResult.items);
      setDrivers(driverResult.items);
      setRoutes(routeResult.items);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : 'Unable to load fleet data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchFleetData();
  }, [fetchFleetData]);

  const filteredVehicles = useMemo(
    () =>
      vehicles.filter((vehicle) => {
        const query = searchTerm.toLowerCase();
        return (
          vehicle.registrationNumber.toLowerCase().includes(query) ||
          vehicle.model.toLowerCase().includes(query)
        );
      }),
    [searchTerm, vehicles],
  );

  const stats = useMemo(() => getFleetStats(vehicles), [vehicles]);
  const driversById = useMemo(() => new Map(drivers.map((driver) => [driver.id, driver])), [drivers]);
  const routesById = useMemo(() => new Map(routes.map((route) => [route.id, route])), [routes]);

  const createVehicle = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      await vehiclesService.createVehicle({
        registrationNumber: form.registrationNumber.trim(),
        model: form.model.trim(),
        seatingCapacity: Number(form.seatingCapacity) || 45,
        status: form.status,
      });
      toast.success('Vehicle added');
      setDialogOpen(false);
      setForm(initialFleetFormState);
      await fetchFleetData();
    } catch (createError) {
      toast.error(createError instanceof Error ? createError.message : 'Unable to add vehicle');
    } finally {
      setSubmitting(false);
    }
  };

  const updateVehicle = async (vehicleId: string, patch: VehicleUpdate) => {
    setUpdatingVehicleId(vehicleId);
    try {
      const updated = await vehiclesService.updateVehicle(vehicleId, patch);
      setVehicles((current) =>
        current.map((vehicle) => (vehicle.id === updated.id ? updated : vehicle)),
      );
      toast.success('Vehicle updated');
    } catch (updateError) {
      toast.error(updateError instanceof Error ? updateError.message : 'Unable to update vehicle');
    } finally {
      setUpdatingVehicleId(null);
    }
  };

  const deleteVehicle = async (vehicle: VehicleRead) => {
    const confirmed = window.confirm(`Delete vehicle ${vehicle.registrationNumber}?`);
    if (!confirmed) return;

    setUpdatingVehicleId(vehicle.id);
    try {
      await vehiclesService.deleteVehicle(vehicle.id);
      setVehicles((current) => current.filter((item) => item.id !== vehicle.id));
      toast.success('Vehicle deleted');
    } catch (deleteError) {
      toast.error(deleteError instanceof Error ? deleteError.message : 'Unable to delete vehicle');
    } finally {
      setUpdatingVehicleId(null);
    }
  };

  return {
    searchTerm,
    setSearchTerm,
    vehicles,
    filteredVehicles,
    drivers,
    routes,
    driversById,
    routesById,
    stats,
    loading,
    error,
    retry: fetchFleetData,
    dialogOpen,
    setDialogOpen,
    form,
    setForm,
    submitting,
    updatingVehicleId,
    createVehicle,
    updateVehicle,
    deleteVehicle,
  };
}
