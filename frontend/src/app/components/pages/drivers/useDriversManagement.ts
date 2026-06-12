import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { ApiError } from '../../../lib/api-client';
import type { DriverCreate, DriverRead, DriverStatus, DriverUpdate, VehicleRead } from '../../../lib/api-types';
import * as driversService from '../../../services/drivers.service';
import * as vehiclesService from '../../../services/vehicles.service';
import { calculateDriverStats } from './driver-helpers';

export function useDriversManagement() {
  const [drivers, setDrivers] = useState<DriverRead[]>([]);
  const [vehicles, setVehicles] = useState<VehicleRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingDriverId, setUpdatingDriverId] = useState<string | null>(null);

  const loadDrivers = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [driversResult, vehiclesResult] = await Promise.all([
        driversService.listDrivers({ pageSize: 100 }),
        vehiclesService.listVehicles({ pageSize: 100 }),
      ]);
      setDrivers(driversResult.items);
      setVehicles(vehiclesResult.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load drivers');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDrivers();
  }, [loadDrivers]);

  const vehiclesById = useMemo(
    () => new Map(vehicles.map((vehicle) => [vehicle.id, vehicle])),
    [vehicles],
  );

  const stats = useMemo(() => calculateDriverStats(drivers), [drivers]);

  const createDriver = async (payload: DriverCreate) => {
    const createdDriver = await driversService.createDriver(payload);
    setDrivers((current) => [createdDriver, ...current]);
    toast.success('Driver added');
  };

  const updateDriverStatus = async (driverId: string, status: DriverStatus) => {
    setUpdatingDriverId(driverId);

    try {
      const updatedDriver = await driversService.updateDriver(driverId, { status });
      setDrivers((current) =>
        current.map((driver) => (driver.id === updatedDriver.id ? updatedDriver : driver)),
      );
      toast.success('Driver status updated');
    } catch (updateError) {
      toast.error(updateError instanceof Error ? updateError.message : 'Unable to update driver');
    } finally {
      setUpdatingDriverId(null);
    }
  };

  const updateDriver = async (driverId: string, patch: DriverUpdate) => {
    setUpdatingDriverId(driverId);
    try {
      const updatedDriver = await driversService.updateDriver(driverId, patch);
      setDrivers((current) =>
        current.map((driver) => (driver.id === updatedDriver.id ? updatedDriver : driver)),
      );
      toast.success('Driver updated');
    } catch (updateError) {
      toast.error(updateError instanceof Error ? updateError.message : 'Unable to update driver');
      throw updateError;
    } finally {
      setUpdatingDriverId(null);
    }
  };

  const deleteDriver = async (driver: DriverRead) => {
    const confirmed = window.confirm(`Delete driver ${driver.name}?`);
    if (!confirmed) return;

    setUpdatingDriverId(driver.id);

    try {
      await driversService.deleteDriver(driver.id);
      setDrivers((current) => current.filter((item) => item.id !== driver.id));
      toast.success('Driver deleted');
    } catch (deleteError) {
      if (deleteError instanceof ApiError && deleteError.status === 400) {
        toast.error(deleteError.message);
      } else {
        toast.error(deleteError instanceof Error ? deleteError.message : 'Unable to delete driver');
      }
    } finally {
      setUpdatingDriverId(null);
    }
  };

  return {
    drivers,
    vehiclesById,
    loading,
    error,
    updatingDriverId,
    stats,
    createDriver,
    updateDriver,
    updateDriverStatus,
    deleteDriver,
    retry: loadDrivers,
  };
}
