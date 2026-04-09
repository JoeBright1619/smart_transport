import React from 'react';
import { toast } from 'sonner';
import { Plus } from 'lucide-react';
import { Button } from '../../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';
import { mockStops } from '../../../../lib/mock-data';

export type RouteDraftStop = { id: string; name: string };

function reorder<T>(arr: T[], from: number, to: number) {
  const next = [...arr];
  const [item] = next.splice(from, 1);
  next.splice(to, 0, item);
  return next;
}

export function CreateRouteStopsTab(props: {
  draftStops: RouteDraftStop[];
  onDraftStopsChange: (next: RouteDraftStop[]) => void;
}) {
  const handleAddStop = () => {
    const next = mockStops.find((s) => !props.draftStops.some((d) => d.id === s.id));
    if (!next) {
      toast.message('All available stops are already included');
      return;
    }
    props.onDraftStopsChange([...props.draftStops, { id: next.id, name: next.name }]);
  };

  const handleRemoveStop = (stopId: string) => {
    props.onDraftStopsChange(props.draftStops.filter((s) => s.id !== stopId));
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">Waypoints and stops</CardTitle>
        <Button size="sm" variant="outline" onClick={handleAddStop}>
          <Plus className="mr-2 size-4" />
          Add stop
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {props.draftStops.map((stop, idx) => (
          <div key={stop.id} className="flex items-center justify-between rounded-lg border p-3">
            <div className="flex items-center gap-3">
              <span className="flex size-6 items-center justify-center rounded-full bg-slate-100 text-xs font-medium">
                {idx + 1}
              </span>
              <div>
                <p className="font-medium">{stop.name}</p>
                <p className="text-xs text-slate-500">Stop ID: {stop.id}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={idx === 0}
                onClick={() => props.onDraftStopsChange(reorder(props.draftStops, idx, idx - 1))}
              >
                Up
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={idx === props.draftStops.length - 1}
                onClick={() => props.onDraftStopsChange(reorder(props.draftStops, idx, idx + 1))}
              >
                Down
              </Button>
              <Button variant="ghost" size="sm" onClick={() => handleRemoveStop(stop.id)}>
                Remove
              </Button>
            </div>
          </div>
        ))}
        <p className="text-xs text-slate-500">
          Prototype supports reorder + add/remove. In production, stops are geocoded and validated against coverage.
        </p>
      </CardContent>
    </Card>
  );
}

