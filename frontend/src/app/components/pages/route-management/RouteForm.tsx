import { useEffect } from 'react';
import { type RouteFormState, haversineDistance } from './route-helpers';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { RouteStopsEditor } from './RouteStopsEditor';

type RouteFormProps = {
  form: RouteFormState;
  setForm: React.Dispatch<React.SetStateAction<RouteFormState>>;
  onSubmit: (event: React.FormEvent) => void;
  submitting: boolean;
  submitLabel: string;
  onCancel: () => void;
};

export function RouteForm({ form, setForm, onSubmit, submitting, submitLabel, onCancel }: RouteFormProps) {
  useEffect(() => {
    if (form.stops.length >= 2) {
      let dist = 0;
      for (let i = 0; i < form.stops.length - 1; i++) {
        const s1 = form.stops[i];
        const s2 = form.stops[i + 1];
        if (s1.lat && s1.lng && s2.lat && s2.lng) {
          dist += haversineDistance(Number(s1.lat), Number(s1.lng), Number(s2.lat), Number(s2.lng));
        }
      }
      const distanceRounded = dist.toFixed(1);
      const durationRounded = Math.round(dist).toString();

      if (form.distance !== distanceRounded || form.duration !== durationRounded) {
        setForm((current) => ({
          ...current,
          distance: distanceRounded,
          duration: durationRounded,
        }));
      }
    } else {
      if (form.distance !== '0' || form.duration !== '0') {
        setForm((current) => ({
          ...current,
          distance: '0',
          duration: '0',
        }));
      }
    }
  }, [form.stops, form.distance, form.duration, setForm]);

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div className="grid gap-4 md:grid-cols-5">
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="routeName">Route name</Label>
          <Input
            id="routeName"
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="routeNumber">Number</Label>
          <Input
            id="routeNumber"
            value={form.number}
            onChange={(event) => setForm((current) => ({ ...current, number: event.target.value }))}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="distance">Distance km</Label>
          <Input
            id="distance"
            type="number"
            min="0"
            step="0.1"
            value={form.distance}
            onChange={(event) => setForm((current) => ({ ...current, distance: event.target.value }))}
            required
            readOnly // Will be auto-calculated
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="duration">Duration min</Label>
          <Input
            id="duration"
            type="number"
            min="0"
            value={form.duration}
            onChange={(event) => setForm((current) => ({ ...current, duration: event.target.value }))}
            required
            readOnly // Will be auto-calculated
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="color">Color</Label>
          <Input
            id="color"
            type="color"
            value={form.color}
            onChange={(event) => setForm((current) => ({ ...current, color: event.target.value }))}
          />
        </div>
      </div>

      <RouteStopsEditor stops={form.stops} setForm={setForm} />

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Saving...' : submitLabel}
        </Button>
      </div>
    </form>
  );
}
