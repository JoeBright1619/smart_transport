import { useState } from 'react';
import { toast } from 'sonner';
import { CalendarPlus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { messageForError } from '../../../lib/error-messages';
import type { DriverRead, RouteRead, TripCreate, VehicleRead } from '../../../lib/api-types';
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
import { buildTripCreatePayload, initialScheduleTripFormState, routeLabel, type ScheduleTripFormState } from './dispatch-helpers';

type ScheduleTripDialogProps = {
  vehicles: VehicleRead[];
  drivers: DriverRead[];
  routes: RouteRead[];
  onCreateTrip: (payload: TripCreate) => Promise<void>;
};

export function ScheduleTripDialog({ vehicles, drivers, routes, onCreateTrip }: ScheduleTripDialogProps) {
  const { t } = useTranslation('dispatch');
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ScheduleTripFormState>(initialScheduleTripFormState);
  const [submitting, setSubmitting] = useState(false);

  const nowMin = toDatetimeLocalString(new Date());

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const now = new Date();
    if (new Date(form.scheduledStart) < now) {
      toast.error(t('schedule.startInFuture'));
      return;
    }
    if (new Date(form.scheduledEnd) <= new Date(form.scheduledStart)) {
      toast.error(t('schedule.endAfterStart'));
      return;
    }
    setSubmitting(true);

    try {
      await onCreateTrip(buildTripCreatePayload(form));
      setForm(initialScheduleTripFormState);
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
          <CalendarPlus className="mr-2 size-4" />
          {t('schedule.trigger')}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('schedule.title')}</DialogTitle>
          <DialogDescription>{t('schedule.description')}</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <TripSelect label={t('schedule.vehicle')} placeholder={t('schedule.selectVehicle')} value={form.vehicleId} onChange={setField(setForm, 'vehicleId')}>
            {vehicles.map((vehicle) => (
              <SelectItem key={vehicle.id} value={vehicle.id}>
                {vehicle.registrationNumber}
              </SelectItem>
            ))}
          </TripSelect>
          <TripSelect label={t('schedule.route')} placeholder={t('schedule.selectRoute')} value={form.routeId} onChange={setField(setForm, 'routeId')}>
            {routes.map((route) => (
              <SelectItem key={route.id} value={route.id}>
                {routeLabel(route)}
              </SelectItem>
            ))}
          </TripSelect>
          <TripSelect label={t('schedule.driver')} placeholder={t('schedule.selectDriver')} value={form.driverId} onChange={setField(setForm, 'driverId')}>
            {drivers.map((driver) => (
              <SelectItem key={driver.id} value={driver.id}>
                {driver.name}
              </SelectItem>
            ))}
          </TripSelect>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="scheduledStart">{t('schedule.scheduledStart')}</Label>
              <Input
                id="scheduledStart"
                type="datetime-local"
                value={form.scheduledStart}
                min={nowMin}
                onChange={(event) => setForm((current) => ({ ...current, scheduledStart: event.target.value }))}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="scheduledEnd">{t('schedule.scheduledEnd')}</Label>
              <Input
                id="scheduledEnd"
                type="datetime-local"
                value={form.scheduledEnd}
                min={form.scheduledStart || nowMin}
                onChange={(event) => setForm((current) => ({ ...current, scheduledEnd: event.target.value }))}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="plannedLoops">{t('schedule.rounds')}</Label>
            <Input
              id="plannedLoops"
              type="number"
              min="1"
              value={form.plannedLoops}
              onChange={(event) => setForm((current) => ({ ...current, plannedLoops: event.target.value }))}
              required
            />
            <p className="text-xs text-muted-foreground">{t('schedule.roundsHint')}</p>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              {t('schedule.close')}
            </Button>
            <Button type="submit" disabled={submitting || !form.vehicleId || !form.routeId || !form.driverId}>
              {submitting ? t('schedule.scheduling') : t('schedule.submit')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function TripSelect({ label, placeholder, value, onChange, children }: {
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Select value={value} onValueChange={onChange} required>
        <SelectTrigger>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>{children}</SelectContent>
      </Select>
    </div>
  );
}

function setField(
  setForm: React.Dispatch<React.SetStateAction<ScheduleTripFormState>>,
  field: keyof ScheduleTripFormState,
) {
  return (value: string) => setForm((current) => ({ ...current, [field]: value }));
}

function toDatetimeLocalString(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
