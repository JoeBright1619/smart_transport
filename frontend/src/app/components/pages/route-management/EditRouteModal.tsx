import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Pencil, Route as RouteIcon } from 'lucide-react';
import type { RouteRead, RouteUpdate } from '../../../lib/api-types';
import { Button } from '../../ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../ui/dialog';
import { RouteForm } from './RouteForm';
import { type RouteFormState } from './route-helpers';

type EditRouteModalProps = {
  route: RouteRead;
  onUpdateRoute: (routeId: string, patch: RouteUpdate) => Promise<void>;
  disabled?: boolean;
};

export function EditRouteModal({ route, onUpdateRoute, disabled }: EditRouteModalProps) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<RouteFormState>({
    name: route.name,
    number: route.number,
    distance: String(route.distance),
    duration: String(route.duration),
    color: route.color,
    stops: route.stops.map((stop) => ({
      key: stop.id,
      name: stop.name,
      lat: stop.lat,
      lng: stop.lng,
      order: stop.order,
    })),
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setForm({
        name: route.name,
        number: route.number,
        distance: String(route.distance),
        duration: String(route.duration),
        color: route.color,
        stops: route.stops.map((stop) => ({
          key: stop.id,
          name: stop.name,
          lat: stop.lat,
          lng: stop.lng,
          order: stop.order,
        })),
      });
    }
  }, [open, route]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      const payload: RouteUpdate = {
        name: form.name.trim(),
        number: form.number.trim(),
        distance: Number(form.distance),
        duration: Number(form.duration),
        color: form.color,
        stops: form.stops.map((stop, index) => ({
          name: stop.name.trim(),
          lat: Number(stop.lat),
          lng: Number(stop.lng),
          order: index + 1,
        })),
      };

      await onUpdateRoute(route.id, payload);
      setOpen(false);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Unable to update route');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled}>
          <Pencil className="mr-2 size-4" />
          Edit
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RouteIcon className="size-5" />
            Edit Route
          </DialogTitle>
          <DialogDescription>
            Modify route details and stops.
          </DialogDescription>
        </DialogHeader>

        <RouteForm
          form={form}
          setForm={setForm}
          onSubmit={handleSubmit}
          submitting={submitting}
          submitLabel="Save Changes"
          onCancel={() => setOpen(false)}
        />
      </DialogContent>
    </Dialog>
  );
}
