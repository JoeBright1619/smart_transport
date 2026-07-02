import { useTranslation } from 'react-i18next';
import { MapPin } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { ALL_STOPS_ID, type StopOption } from './arrival-helpers';

type ArrivalStopSelectorProps = {
  stops: StopOption[];
  selectedStopId: string;
  onStopChange: (stopId: string) => void;
};

export function ArrivalStopSelector({
  stops,
  selectedStopId,
  onStopChange,
}: ArrivalStopSelectorProps) {
  const { t } = useTranslation('arrivals');
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <MapPin className="size-5 text-blue-600" />
          {t('stop')}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Label>{t('selectStop')}</Label>
        <Select value={selectedStopId} onValueChange={onStopChange} disabled={stops.length === 0}>
          <SelectTrigger>
            <SelectValue placeholder={t('selectStopPlaceholder')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_STOPS_ID}>{t('allStops')}</SelectItem>
            {stops.map((stop) => (
              <SelectItem key={stop.id} value={stop.id}>
                {stop.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {stops.length === 0 && <p className="text-sm text-slate-600">{t('noStops')}</p>}
      </CardContent>
    </Card>
  );
}
