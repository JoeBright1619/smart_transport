import { ArrivalEstimateList } from './arrival-times/ArrivalEstimateList';
import { ArrivalErrorState, ArrivalLoadingState } from './arrival-times/ArrivalPageStates';
import { ArrivalStopSelector } from './arrival-times/ArrivalStopSelector';
import { useArrivalTimes } from './arrival-times/useArrivalTimes';

export function ArrivalTimes() {
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
        <h1 className="text-2xl font-bold">Arrival Time Estimation</h1>
        <p className="text-slate-600">Real-time ETA at all bus stops</p>
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
