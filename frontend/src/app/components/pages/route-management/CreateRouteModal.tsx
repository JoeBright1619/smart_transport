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
import { RouteForm } from './RouteForm';

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
      <DialogContent className="max-h-[calc(100vh-2rem)] overflow-y-auto sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RouteIcon className="size-5" />
            Create New Route
          </DialogTitle>
          <DialogDescription>
            Define route details and ordered stops for backend route creation.
          </DialogDescription>
        </DialogHeader>

        <RouteForm
          form={form}
          setForm={setForm}
          onSubmit={handleSubmit}
          submitting={submitting}
          submitLabel="Create Route"
          onCancel={() => setOpen(false)}
        />
      </DialogContent>
    </Dialog>
  );
}
