import { useState } from 'react';
import { toast } from 'sonner';
import { Plus, UserPlus } from 'lucide-react';
import type { DriverCreate } from '../../../lib/api-types';
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
import { buildDriverCreatePayload, initialDriverFormState, type DriverFormState } from './driver-helpers';
import React from 'react';

type AddDriverDialogProps = {
  onCreateDriver: (payload: DriverCreate) => Promise<void>;
};

export function AddDriverDialog({ onCreateDriver }: AddDriverDialogProps) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<DriverFormState>(initialDriverFormState);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      await onCreateDriver(buildDriverCreatePayload(form));
      setForm(initialDriverFormState);
      setOpen(false);
    } catch (createError) {
      toast.error(createError instanceof Error ? createError.message : 'Unable to add driver');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 size-4" />
          Add Driver
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="size-5" />
            Add Driver
          </DialogTitle>
          <DialogDescription>Register a driver with license and certification details.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="driverName">Name</Label>
            <Input id="driverName" value={form.name} onChange={updateField(setForm, 'name')} required />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="licenseNumber">License number</Label>
              <Input
                id="licenseNumber"
                value={form.licenseNumber}
                onChange={updateField(setForm, 'licenseNumber')}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="driverPhone">Phone</Label>
              <Input id="driverPhone" value={form.phone} onChange={updateField(setForm, 'phone')} required />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="certificationExpiry">Certification expiry</Label>
            <Input
              id="certificationExpiry"
              type="date"
              value={form.certificationExpiry}
              onChange={updateField(setForm, 'certificationExpiry')}
              required
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Close
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Adding...' : 'Add Driver'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function updateField(
  setForm: React.Dispatch<React.SetStateAction<DriverFormState>>,
  field: keyof DriverFormState,
) {
  return (event: React.ChangeEvent<HTMLInputElement>) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };
}
