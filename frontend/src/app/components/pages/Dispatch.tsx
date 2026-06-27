import { useTranslation } from 'react-i18next';
import { DispatchErrorState, DispatchLoadingState } from './dispatch/DispatchPageStates';
import { DispatchResourcesCard } from './dispatch/DispatchResourcesCard';
import { DispatchStatsCards } from './dispatch/DispatchStatsCards';
import { ScheduleTripDialog } from './dispatch/ScheduleTripDialog';
import { TripsPanel } from './dispatch/TripsPanel';
import { useDispatchManagement } from './dispatch/useDispatchManagement';

export function Dispatch() {
  const { t } = useTranslation('dispatch');
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
          <h1 className="text-2xl font-bold">{t('title')}</h1>
          <p className="text-slate-600">{t('subtitle')}</p>
        </div>
        <ScheduleTripDialog
          vehicles={dispatch.availableVehicles}
          drivers={dispatch.availableDrivers}
          routes={dispatch.schedulableRoutes}
          onCreateTrip={dispatch.createTrip}
        />
      </div>

      <DispatchStatsCards stats={dispatch.stats} />

      <div className="grid gap-6 lg:grid-cols-2">
        <TripsPanel
          title={t('panel.activeTrips')}
          emptyLabel={t('panel.noActiveTrips')}
          trips={dispatch.activeTrips}
          vehiclesById={dispatch.vehiclesById}
          driversById={dispatch.driversById}
          routesById={dispatch.routesById}
          updatingTripId={dispatch.updatingTripId}
          onUpdateStatus={dispatch.updateTripStatus}
        />
        <TripsPanel
          title={t('panel.scheduledTrips')}
          emptyLabel={t('panel.noScheduledTrips')}
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
