import { useState } from 'react';
import { toast } from 'sonner';
import { Plus, Route as RouteIcon } from 'lucide-react';
import type { RouteCreate } from '../../../lib/api-types';
import { Button } from '../../ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../ui/dialog';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import {
  initialRouteFormState,
  toRouteCreatePayload,
  type RouteFormState,
} from './route-helpers';
import { RouteStopsEditor } from './RouteStopsEditor';

type CreateRouteModalProps = {
  onCreateRoute: (payload: RouteCreate) => Promise<void>;
};

export function CreateRouteModal({ onCreateRoute }: CreateRouteModalProps) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<RouteFormState>(initialRouteFormState);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      await onCreateRoute(toRouteCreatePayload(form));
      setForm(initialRouteFormState);
      setOpen(false);
    } catch (createError) {
      toast.error(createError instanceof Error ? createError.message : 'Unable to create route');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 size-4" />
          Create New Route
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RouteIcon className="size-5" />
            Create New Route
          </DialogTitle>
          <DialogDescription>
            Define route details and ordered stops for backend route creation.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5">
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

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Close
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Creating...' : 'Create Route'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
