import { useEffect, useState } from 'react';
import { Bus, MapPin, Navigation } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { getMyBoardings, type PassengerTripRecord } from '../../../services/boarding.service';

export function PassengerTrips() {
  const { t } = useTranslation('passenger');
  const [records, setRecords] = useState<PassengerTripRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyBoardings()
      .then((r) => setRecords(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-center py-12 text-slate-500 text-sm">{t('trips.loading')}</div>;
  }

  if (records.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center space-y-2">
          <Navigation className="size-10 text-slate-300 mx-auto" />
          <p className="font-medium text-slate-600">{t('trips.noTripsTitle')}</p>
          <p className="text-sm text-slate-400">
            {t('trips.noTripsBody')}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500">{t('trips.recordedEvents', { count: records.length })}</p>
      {records.map((rec) => (
        <Card key={rec.boardingId}>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <MapPin className="size-4 text-slate-400" />
                {rec.stopName || t('trips.unknownStop')}
              </span>
              <Badge variant={rec.eventType === 'boarded' ? 'default' : 'secondary'}>
                {rec.eventType === 'boarded'
                  ? t('trips.boarded', { count: rec.count })
                  : t('trips.alighted', { count: rec.count })}
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
            <p>{t('trips.occupancyAfter', { count: rec.occupancyAfter })}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
