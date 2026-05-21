import { Trash2 } from 'lucide-react';
import type { Dispatch, SetStateAction } from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { createEmptyStop, type RouteFormState, type RouteFormStop } from './route-helpers';

type RouteStopsEditorProps = {
  stops: RouteFormStop[];
  setForm: Dispatch<SetStateAction<RouteFormState>>;
};

export function RouteStopsEditor({ stops, setForm }: RouteStopsEditorProps) {
  const updateStop = (
    key: string,
    field: 'name' | 'lat' | 'lng',
    value: string,
  ) => {
    setForm((current) => ({
      ...current,
      stops: current.stops.map((stop) =>
        stop.key === key
          ? { ...stop, [field]: field === 'name' ? value : Number(value) }
          : stop,
      ),
    }));
  };

  const removeStop = (key: string) => {
    setForm((current) => ({
      ...current,
      stops: current.stops
        .filter((stop) => stop.key !== key)
        .map((stop, index) => ({ ...stop, order: index + 1 })),
    }));
  };

  const addStop = () => {
    setForm((current) => ({
      ...current,
      stops: [...current.stops, createEmptyStop(current.stops.length + 1)],
    }));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label>Stops</Label>
        <Button type="button" variant="outline" size="sm" onClick={addStop}>
          Add stop
        </Button>
      </div>
      <div className="max-h-72 space-y-3 overflow-y-auto pr-2">
        {stops.map((stop, index) => (
          <div key={stop.key} className="grid gap-3 rounded-lg border p-3 md:grid-cols-[2rem_1fr_8rem_8rem_2.5rem]">
            <div className="flex size-8 items-center justify-center rounded-full bg-slate-100 text-sm">
              {index + 1}
            </div>
            <Input
              placeholder="Stop name"
              value={stop.name}
              onChange={(event) => updateStop(stop.key, 'name', event.target.value)}
              required
            />
            <Input
              type="number"
              step="0.000001"
              placeholder="Latitude"
              value={stop.lat}
              onChange={(event) => updateStop(stop.key, 'lat', event.target.value)}
              required
            />
            <Input
              type="number"
              step="0.000001"
              placeholder="Longitude"
              value={stop.lng}
              onChange={(event) => updateStop(stop.key, 'lng', event.target.value)}
              required
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              disabled={stops.length === 1}
              onClick={() => removeStop(stop.key)}
            >
              <Trash2 className="size-4 text-red-500" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
