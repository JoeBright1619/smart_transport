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
import { validateName, validatePhone } from '../../../lib/validation';
import { messageForError } from '../../../lib/error-messages';
import { useTranslation } from 'react-i18next';
import React from 'react';

type AddDriverDialogProps = {
  onCreateDriver: (payload: DriverCreate) => Promise<void>;
};

export function AddDriverDialog({ onCreateDriver }: AddDriverDialogProps) {
  const { t } = useTranslation('drivers');
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<DriverFormState>(initialDriverFormState);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<{ name?: string; phone?: string }>({});

  const validate = (): boolean => {
    const next: { name?: string; phone?: string } = {};
    const nameErr = validateName(form.name);
    if (nameErr) next.name = nameErr;
    // Phone is required for drivers — an empty value is an error here.
    const phoneErr = !form.phone.trim() ? t('add.phoneRequired') : validatePhone(form.phone);
    if (phoneErr) next.phone = phoneErr;
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!validate()) return;
    setSubmitting(true);

    try {
      await onCreateDriver(buildDriverCreatePayload(form));
      setForm(initialDriverFormState);
      setOpen(false);
    } catch (createError) {
      toast.error(messageForError(createError));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 size-4" />
          {t('add.trigger')}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="size-5" />
            {t('add.title')}
          </DialogTitle>
          <DialogDescription>{t('add.description')}</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="driverName">{t('add.name')}</Label>
            <Input
              id="driverName"
              value={form.name}
              onChange={updateField(setForm, 'name')}
              aria-invalid={!!errors.name}
              required
            />
            {errors.name && <p className="text-xs text-red-600">{errors.name}</p>}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="licenseNumber">{t('add.licenseNumber')}</Label>
              <Input
                id="licenseNumber"
                value={form.licenseNumber}
                onChange={updateField(setForm, 'licenseNumber')}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="driverPhone">{t('add.phone')}</Label>
              <Input
                id="driverPhone"
                value={form.phone}
                onChange={updateField(setForm, 'phone')}
                aria-invalid={!!errors.phone}
                required
              />
              {errors.phone && <p className="text-xs text-red-600">{errors.phone}</p>}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="certificationExpiry">{t('add.certificationExpiry')}</Label>
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
              {t('add.close')}
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? t('add.adding') : t('add.submit')}
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
