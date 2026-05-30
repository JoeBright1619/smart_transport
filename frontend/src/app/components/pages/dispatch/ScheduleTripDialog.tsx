import { useState } from 'react';
import { toast } from 'sonner';
import { CalendarPlus } from 'lucide-react';
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
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ScheduleTripFormState>(initialScheduleTripFormState);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (new Date(form.scheduledEnd) <= new Date(form.scheduledStart)) {
      toast.error('Scheduled end must be after scheduled start');
      return;
    }
    setSubmitting(true);

    try {
      await onCreateTrip(buildTripCreatePayload(form));
      setForm(initialScheduleTripFormState);
      setOpen(false);
    } catch (createError) {
      toast.error(createError instanceof Error ? createError.message : 'Unable to schedule trip');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <CalendarPlus className="mr-2 size-4" />
          Schedule Trip
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Schedule Trip</DialogTitle>
          <DialogDescription>Assign an available vehicle, route, driver, and trip window.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <TripSelect label="Vehicle" value={form.vehicleId} onChange={setField(setForm, 'vehicleId')}>
            {vehicles.map((vehicle) => (
              <SelectItem key={vehicle.id} value={vehicle.id}>
                {vehicle.registrationNumber}
              </SelectItem>
            ))}
          </TripSelect>
          <TripSelect label="Route" value={form.routeId} onChange={setField(setForm, 'routeId')}>
            {routes.map((route) => (
              <SelectItem key={route.id} value={route.id}>
                {routeLabel(route)}
              </SelectItem>
            ))}
          </TripSelect>
          <TripSelect label="Driver" value={form.driverId} onChange={setField(setForm, 'driverId')}>
            {drivers.map((driver) => (
              <SelectItem key={driver.id} value={driver.id}>
                {driver.name}
              </SelectItem>
            ))}
          </TripSelect>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="scheduledStart">Scheduled start</Label>
              <Input
                id="scheduledStart"
                type="datetime-local"
                value={form.scheduledStart}
                onChange={(event) => setForm((current) => ({ ...current, scheduledStart: event.target.value }))}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="scheduledEnd">Scheduled end</Label>
              <Input
                id="scheduledEnd"
                type="datetime-local"
                value={form.scheduledEnd}
                onChange={(event) => setForm((current) => ({ ...current, scheduledEnd: event.target.value }))}
                required
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Close
            </Button>
            <Button type="submit" disabled={submitting || !form.vehicleId || !form.routeId || !form.driverId}>
              {submitting ? 'Scheduling...' : 'Schedule Trip'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function TripSelect({ label, value, onChange, children }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Select value={value} onValueChange={onChange} required>
        <SelectTrigger>
          <SelectValue placeholder={`Select ${label.toLowerCase()}`} />
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
