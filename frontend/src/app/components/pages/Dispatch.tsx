import { DispatchErrorState, DispatchLoadingState } from './dispatch/DispatchPageStates';
import { DispatchResourcesCard } from './dispatch/DispatchResourcesCard';
import { DispatchStatsCards } from './dispatch/DispatchStatsCards';
import { ScheduleTripDialog } from './dispatch/ScheduleTripDialog';
import { TripsPanel } from './dispatch/TripsPanel';
import { useDispatchManagement } from './dispatch/useDispatchManagement';

export function Dispatch() {
  const dispatch = useDispatchManagement();

  if (dispatch.loading) {
    return <DispatchLoadingState />;
  }

  if (dispatch.error) {
    return <DispatchErrorState error={dispatch.error} onRetry={() => void dispatch.retry()} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dispatch Management</h1>
          <p className="text-slate-600">Centralized trip assignment and dispatch control</p>
        </div>
        <ScheduleTripDialog
          vehicles={dispatch.availableVehicles}
          drivers={dispatch.availableDrivers}
          routes={dispatch.routes}
          onCreateTrip={dispatch.createTrip}
        />
      </div>

      <DispatchStatsCards stats={dispatch.stats} />

      <div className="grid gap-6 lg:grid-cols-2">
        <TripsPanel
          title="Active Trips"
          trips={dispatch.activeTrips}
          vehiclesById={dispatch.vehiclesById}
          driversById={dispatch.driversById}
          routesById={dispatch.routesById}
          updatingTripId={dispatch.updatingTripId}
          onUpdateStatus={dispatch.updateTripStatus}
        />
        <TripsPanel
          title="Scheduled Trips"
          trips={dispatch.scheduledTrips}
          vehiclesById={dispatch.vehiclesById}
          driversById={dispatch.driversById}
          routesById={dispatch.routesById}
          updatingTripId={dispatch.updatingTripId}
          onUpdateStatus={dispatch.updateTripStatus}
        />
      </div>

      <DispatchResourcesCard
        availableVehicles={dispatch.availableVehicles}
        availableDrivers={dispatch.availableDrivers}
      />
    </div>
  );
}
