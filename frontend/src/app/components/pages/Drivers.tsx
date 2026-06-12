import { AddDriverDialog } from './drivers/AddDriverDialog';
import { DriverErrorState, DriverLoadingState } from './drivers/DriverPageStates';
import { DriverStatsCards } from './drivers/DriverStatsCards';
import { DriversTable } from './drivers/DriversTable';
import { useDriversManagement } from './drivers/useDriversManagement';

export function Drivers() {
  const driversManagement = useDriversManagement();

  if (driversManagement.loading) {
    return <DriverLoadingState />;
  }

  if (driversManagement.error) {
    return (
      <DriverErrorState
        error={driversManagement.error}
        onRetry={() => void driversManagement.retry()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Driver Management</h1>
          <p className="text-slate-600">Manage driver profiles and performance</p>
        </div>
        <AddDriverDialog onCreateDriver={driversManagement.createDriver} />
      </div>

      <DriverStatsCards stats={driversManagement.stats} />

      <DriversTable
        drivers={driversManagement.drivers}
        vehiclesById={driversManagement.vehiclesById}
        updatingDriverId={driversManagement.updatingDriverId}
        onUpdateStatus={driversManagement.updateDriverStatus}
        onEditDriver={driversManagement.updateDriver}
        onDeleteDriver={driversManagement.deleteDriver}
      />
    </div>
  );
}
