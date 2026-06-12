import React, { useEffect, useState } from 'react';
import { UserCog } from 'lucide-react';
import { toast } from 'sonner';
import type { DriverRead, DriverUpdate } from '../../../lib/api-types';
import { Button } from '../../ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../ui/dialog';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';

type EditFormState = {
  name: string;
  phone: string;
  certificationExpiry: string;
};

type EditDriverDialogProps = {
  driver: DriverRead;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (driverId: string, patch: DriverUpdate) => Promise<void>;
};

export function EditDriverDialog({ driver, open, onOpenChange, onSave }: EditDriverDialogProps) {
  const [form, setForm] = useState<EditFormState>(toFormState(driver));
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setForm(toFormState(driver));
  }, [driver]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      await onSave(driver.id, {
        name: form.name.trim(),
        phone: form.phone.trim(),
        certificationExpiry: form.certificationExpiry,
      });
      onOpenChange(false);
    } catch (saveError) {
      toast.error(saveError instanceof Error ? saveError.message : 'Unable to update driver');
    } finally {
      setSubmitting(false);
    }
  };

  const updateField =
    (field: keyof EditFormState) => (event: React.ChangeEvent<HTMLInputElement>) =>
      setForm((current) => ({ ...current, [field]: event.target.value }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserCog className="size-5" />
            Edit Driver
          </DialogTitle>
          <DialogDescription>Update {driver.name}&apos;s information.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="editDriverName">Name</Label>
            <Input
              id="editDriverName"
              value={form.name}
              onChange={updateField('name')}
              required
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="editDriverPhone">Phone</Label>
              <Input
                id="editDriverPhone"
                value={form.phone}
                onChange={updateField('phone')}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="editCertExpiry">Certification expiry</Label>
              <Input
                id="editCertExpiry"
                type="date"
                value={form.certificationExpiry}
                onChange={updateField('certificationExpiry')}
                required
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Saving...' : 'Save changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function toFormState(driver: DriverRead): EditFormState {
  return {
    name: driver.name,
    phone: driver.phone,
    certificationExpiry: driver.certificationExpiry.slice(0, 10),
  };
}
