import type { Dispatch, FormEvent, SetStateAction } from 'react';
import type { VehicleStatus } from '../../../lib/api-types';
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { useTranslation } from 'react-i18next';
import { vehicleStatuses } from './fleet-helpers';
import type { FleetFormState } from './useFleetManagement';

type AddVehicleDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  form: FleetFormState;
  setForm: Dispatch<SetStateAction<FleetFormState>>;
  submitting: boolean;
  onSubmit: (event: FormEvent) => void;
};

export function AddVehicleDialog({
  open,
  onOpenChange,
  form,
  setForm,
  submitting,
  onSubmit,
}: AddVehicleDialogProps) {
  const { t } = useTranslation('fleet');
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button>{t('addDialog.trigger')}</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('addDialog.title')}</DialogTitle>
          <DialogDescription>{t('addDialog.description')}</DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="registrationNumber">{t('addDialog.registration')}</Label>
              <Input
                id="registrationNumber"
                value={form.registrationNumber}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    registrationNumber: event.target.value,
                  }))
                }
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="model">{t('addDialog.model')}</Label>
              <Input
                id="model"
                value={form.model}
                onChange={(event) =>
                  setForm((current) => ({ ...current, model: event.target.value }))
                }
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="seatingCapacity">{t('addDialog.seatingCapacity')}</Label>
              <Input
                id="seatingCapacity"
                type="number"
                min="1"
                value={form.seatingCapacity}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    seatingCapacity: event.target.value,
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>{t('addDialog.status')}</Label>
              <Select
                value={form.status}
                onValueChange={(value) =>
                  setForm((current) => ({ ...current, status: value as VehicleStatus }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {vehicleStatuses.map((status) => (
                    <SelectItem key={status} value={status}>
                      {t(`vehicleStatus.${status}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={submitting}>
              {submitting ? t('addDialog.adding') : t('addDialog.submit')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
