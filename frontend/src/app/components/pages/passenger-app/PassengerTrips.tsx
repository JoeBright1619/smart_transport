import { useEffect, useState } from 'react';
import { Bus, MapPin, Navigation } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { getMyBoardings, type PassengerTripRecord } from '../../../services/boarding.service';

export function PassengerTrips() {
  const [records, setRecords] = useState<PassengerTripRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyBoardings()
      .then((r) => setRecords(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-center py-12 text-slate-500 text-sm">Loading trips…</div>;
  }

  if (records.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center space-y-2">
          <Navigation className="size-10 text-slate-300 mx-auto" />
          <p className="font-medium text-slate-600">No trips recorded yet</p>
          <p className="text-sm text-slate-400">
            Your travel history will appear here once you've been recorded on a route.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500">{records.length} recorded event{records.length !== 1 ? 's' : ''}</p>
      {records.map((rec) => (
        <Card key={rec.boardingId}>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <MapPin className="size-4 text-slate-400" />
                {rec.stopName || 'Unknown stop'}
              </span>
              <Badge variant={rec.eventType === 'boarded' ? 'default' : 'secondary'}>
                {rec.eventType === 'boarded' ? `+${rec.count} boarded` : `−${rec.count} alighted`}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-500 space-y-1">
            {rec.vehicleRegistration && (
              <p className="flex items-center gap-1.5">
                <Bus className="size-3.5 shrink-0" />
                {rec.vehicleRegistration}
                {rec.vehicleModel && <span className="text-slate-400">· {rec.vehicleModel}</span>}
              </p>
            )}
            <p>{new Date(rec.recordedAt).toLocaleString()}</p>
            <p>Occupancy after: {rec.occupancyAfter} passengers</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
