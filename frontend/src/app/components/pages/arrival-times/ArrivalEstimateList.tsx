import { Clock, Navigation } from 'lucide-react';
import { Badge } from '../../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { ALL_STOPS_ID, etaLabel, formatLastUpdated, type ArrivalEstimateWithStop, type StopOption } from './arrival-helpers';

type ArrivalEstimateListProps = {
  selectedStop: StopOption | null;
  estimates: ArrivalEstimateWithStop[];
  loading: boolean;
  lastUpdated: Date | null;
};

export function ArrivalEstimateList({
  selectedStop,
  estimates,
  loading,
  lastUpdated,
}: ArrivalEstimateListProps) {
  const showStopName = selectedStop?.id === ALL_STOPS_ID;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>{selectedStop?.name ?? 'Arrival estimates'}</CardTitle>
            <p className="mt-1 text-sm text-slate-600">
              {selectedStop?.routeLabels.join(', ') ?? 'Select a stop to view arrivals'}
            </p>
          </div>
          <Badge variant="outline">{loading ? 'Refreshing' : formatLastUpdated(lastUpdated)}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {!selectedStop ? (
          <p className="py-6 text-center text-sm text-slate-500">Select a stop to view arrival estimates.</p>
        ) : estimates.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-500">No active vehicles heading to this stop.</p>
        ) : (
          estimates.map((estimate) => (
            <ArrivalEstimateRow key={estimate.vehicleId} estimate={estimate} showStopName={showStopName} />
          ))
        )}
      </CardContent>
    </Card>
  );
}

function ArrivalEstimateRow({
  estimate,
  showStopName,
}: {
  estimate: ArrivalEstimateWithStop;
  showStopName: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border p-3">
      <div className="flex items-center gap-3">
        <Badge>{estimate.routeName}</Badge>
        <div>
          <p className="font-medium text-sm">{estimate.registrationNumber}</p>
          {showStopName && estimate.stopName && (
            <p className="text-xs font-medium text-blue-700">To {estimate.stopName}</p>
          )}
          <p className="text-xs text-slate-500">
            {estimate.distanceToStopKm.toFixed(2)} km away - {estimate.currentSpeedKmh} km/h
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {estimate.etaMinutes === null ? (
          <Navigation className="size-4 text-slate-500" />
        ) : (
          <Clock className="size-4 text-blue-600" />
        )}
        <div className="text-right">
          <p className="text-lg font-bold text-blue-600">{etaLabel(estimate)}</p>
          <p className="text-xs text-slate-500">{estimate.status}</p>
        </div>
      </div>
    </div>
  );
}
