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
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <MapPin className="size-5 text-blue-600" />
          Stop
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Label>Select stop</Label>
        <Select value={selectedStopId} onValueChange={onStopChange} disabled={stops.length === 0}>
          <SelectTrigger>
            <SelectValue placeholder="Select a stop" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_STOPS_ID}>All Stops</SelectItem>
            {stops.map((stop) => (
              <SelectItem key={stop.id} value={stop.id}>
                {stop.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {stops.length === 0 && <p className="text-sm text-slate-600">No stops found.</p>}
      </CardContent>
    </Card>
  );
}
