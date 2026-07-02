import { useTranslation } from 'react-i18next';
import { ArrivalEstimateList } from './arrival-times/ArrivalEstimateList';
import { ArrivalErrorState, ArrivalLoadingState } from './arrival-times/ArrivalPageStates';
import { ArrivalStopSelector } from './arrival-times/ArrivalStopSelector';
import { useArrivalTimes } from './arrival-times/useArrivalTimes';

export function ArrivalTimes() {
  const { t } = useTranslation('arrivals');
  const arrivals = useArrivalTimes();

  if (arrivals.loadingStops) {
    return <ArrivalLoadingState />;
  }

  if (arrivals.error) {
    return <ArrivalErrorState error={arrivals.error} onRetry={() => void arrivals.retry()} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <p className="text-slate-600">{t('subtitle')}</p>
      </div>

      <ArrivalStopSelector
        stops={arrivals.stops}
        selectedStopId={arrivals.selectedStopId}
        onStopChange={arrivals.setSelectedStopId}
      />

      <ArrivalEstimateList
        selectedStop={arrivals.selectedStop}
        estimates={arrivals.estimates}
        loading={arrivals.loadingArrivals}
        lastUpdated={arrivals.lastUpdated}
      />
    </div>
  );
}
