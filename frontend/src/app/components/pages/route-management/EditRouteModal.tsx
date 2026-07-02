import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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

const createFormKey = () => globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;

function toRouteFormState(route: RouteRead): RouteFormState {
  return {
    name: route.name,
    number: route.number,
    distance: String(route.distance),
    duration: String(route.duration),
    color: route.color,
    stops: route.stops.map((stop) => ({
      key: createFormKey(),
      stopId: stop.id,
      name: stop.name,
      lat: stop.lat,
      lng: stop.lng,
      order: stop.order,
    })),
  };
}

export function EditRouteModal({ route, onUpdateRoute, disabled }: EditRouteModalProps) {
  const { t } = useTranslation('routes');
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<RouteFormState>(() => toRouteFormState(route));
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setForm(toRouteFormState(route));
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
          stopId: stop.stopId,
          order: index + 1,
        })),
      };

      await onUpdateRoute(route.id, payload);
      setOpen(false);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t('unableUpdate'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled}>
          <Pencil className="mr-2 size-4" />
          {t('edit')}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[calc(100vh-2rem)] overflow-y-auto sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RouteIcon className="size-5" />
            {t('editRoute')}
          </DialogTitle>
          <DialogDescription>
            {t('editRouteDesc')}
          </DialogDescription>
        </DialogHeader>

        <RouteForm
          form={form}
          setForm={setForm}
          onSubmit={handleSubmit}
          submitting={submitting}
          submitLabel={t('saveChanges')}
          onCancel={() => setOpen(false)}
        />
      </DialogContent>
    </Dialog>
  );
}
