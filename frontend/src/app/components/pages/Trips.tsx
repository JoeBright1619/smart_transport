import { useTranslation } from 'react-i18next';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { TripsErrorState, TripsLoadingState } from './trips/TripsPageStates';
import { TripsHistoryTable } from './trips/TripsHistoryTable';
import { useTripsHistory, type TripStatusFilter } from './trips/useTripsHistory';

export function Trips() {
  const { t } = useTranslation('trips');
  const trips = useTripsHistory();

  if (trips.error) {
    return <TripsErrorState error={trips.error} onRetry={() => void trips.retry()} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{t('title')}</h1>
          <p className="text-slate-600">{t('subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="tripStatusFilter">{t('filter.label')}</Label>
          <Select
            value={trips.status}
            onValueChange={(value) => trips.setStatus(value as TripStatusFilter)}
          >
            <SelectTrigger id="tripStatusFilter" className="w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('filter.all')}</SelectItem>
              <SelectItem value="scheduled">{t('status.scheduled')}</SelectItem>
              <SelectItem value="active">{t('status.active')}</SelectItem>
              <SelectItem value="completed">{t('status.completed')}</SelectItem>
              <SelectItem value="cancelled">{t('status.cancelled')}</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {trips.loading && trips.trips.length === 0 ? (
        <TripsLoadingState />
      ) : (
        <TripsHistoryTable
          trips={trips.trips}
          total={trips.total}
          page={trips.page}
          pageSize={trips.pageSize}
          vehiclesById={trips.vehiclesById}
          driversById={trips.driversById}
          routesById={trips.routesById}
          onPageChange={trips.setPage}
        />
      )}
    </div>
  );
}
