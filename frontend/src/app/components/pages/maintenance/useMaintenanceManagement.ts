import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import type {
  MaintenanceCreate,
  MaintenanceRead,
  MaintenanceStatus,
  VehicleRead,
} from '../../../lib/api-types';
import * as maintenanceService from '../../../services/maintenance.service';
import * as vehiclesService from '../../../services/vehicles.service';
import { calculateMaintenanceStats } from './maintenance-helpers';

export function useMaintenanceManagement() {
  const [records, setRecords] = useState<MaintenanceRead[]>([]);
  const [vehicles, setVehicles] = useState<VehicleRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingRecordId, setUpdatingRecordId] = useState<string | null>(null);

  const loadMaintenance = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [maintenanceResult, vehiclesResult] = await Promise.all([
        maintenanceService.listMaintenance({ pageSize: 100 }),
        vehiclesService.listVehicles({ pageSize: 100 }),
      ]);
      setRecords(maintenanceResult.items);
      setVehicles(vehiclesResult.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load maintenance records');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMaintenance();
  }, [loadMaintenance]);

  const vehiclesById = useMemo(
    () => new Map(vehicles.map((vehicle) => [vehicle.id, vehicle])),
    [vehicles],
  );

  const stats = useMemo(() => calculateMaintenanceStats(records), [records]);

  const createMaintenance = async (payload: MaintenanceCreate) => {
    const createdRecord = await maintenanceService.createMaintenance(payload);
    setRecords((current) => [createdRecord, ...current]);
    toast.success('Maintenance scheduled');
  };

  const updateMaintenanceStatus = async (record: MaintenanceRead, status: MaintenanceStatus) => {
    setUpdatingRecordId(record.id);

    try {
      const updatedRecord = await maintenanceService.updateMaintenance(record.id, { status });
      setRecords((current) =>
        current.map((item) => (item.id === updatedRecord.id ? updatedRecord : item)),
      );
      toast.success('Maintenance status updated');
    } catch (updateError) {
      toast.error(updateError instanceof Error ? updateError.message : 'Unable to update maintenance');
    } finally {
      setUpdatingRecordId(null);
    }
  };

  return {
    records,
    vehicles,
    vehiclesById,
    loading,
    error,
    updatingRecordId,
    stats,
    createMaintenance,
    updateMaintenanceStatus,
    retry: loadMaintenance,
  };
}
