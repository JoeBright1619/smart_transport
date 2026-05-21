import { useState, type ChangeEvent, type Dispatch, type FormEvent, type SetStateAction } from 'react';
import { toast } from 'sonner';
import { CalendarPlus } from 'lucide-react';
import type { MaintenanceCreate, VehicleRead } from '../../../lib/api-types';
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
import {
  buildMaintenanceCreatePayload,
  initialMaintenanceFormState,
  maintenanceTypeOptions,
  type MaintenanceFormState,
} from './maintenance-helpers';

type ScheduleMaintenanceDialogProps = {
  vehicles: VehicleRead[];
  onCreateMaintenance: (payload: MaintenanceCreate) => Promise<void>;
};

export function ScheduleMaintenanceDialog({
  vehicles,
  onCreateMaintenance,
}: ScheduleMaintenanceDialogProps) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<MaintenanceFormState>(initialMaintenanceFormState);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      await onCreateMaintenance(buildMaintenanceCreatePayload(form));
      setForm(initialMaintenanceFormState);
      setOpen(false);
    } catch (createError) {
      toast.error(createError instanceof Error ? createError.message : 'Unable to schedule maintenance');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <CalendarPlus className="mr-2 size-4" />
          Schedule Maintenance
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Schedule Maintenance</DialogTitle>
          <DialogDescription>Create a vehicle maintenance job with date, type, and cost.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Vehicle</Label>
            <Select value={form.vehicleId} onValueChange={setField(setForm, 'vehicleId')} required>
              <SelectTrigger>
                <SelectValue placeholder="Select vehicle" />
              </SelectTrigger>
              <SelectContent>
                {vehicles.map((vehicle) => (
                  <SelectItem key={vehicle.id} value={vehicle.id}>
                    {vehicle.registrationNumber}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={form.type} onValueChange={setField(setForm, 'type')} required>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {maintenanceTypeOptions.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <InputField label="Cost" type="number" value={form.cost} onChange={updateField(setForm, 'cost')} />
          </div>

          <InputField label="Description" value={form.description} onChange={updateField(setForm, 'description')} />

          <div className="grid gap-4 md:grid-cols-2">
            <InputField label="Scheduled date" type="date" value={form.scheduledDate} onChange={updateField(setForm, 'scheduledDate')} />
            <InputField label="Next due" type="date" value={form.nextDue} onChange={updateField(setForm, 'nextDue')} required={false} />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Close
            </Button>
            <Button type="submit" disabled={submitting || !form.vehicleId}>
              {submitting ? 'Scheduling...' : 'Schedule Maintenance'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function InputField({
  label,
  value,
  onChange,
  type = 'text',
  required = true,
}: {
  label: string;
  value: string;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Input type={type} value={value} onChange={onChange} required={required} min={type === 'number' ? '0' : undefined} />
    </div>
  );
}

function updateField(
  setForm: Dispatch<SetStateAction<MaintenanceFormState>>,
  field: keyof MaintenanceFormState,
) {
  return (event: ChangeEvent<HTMLInputElement>) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };
}

function setField(
  setForm: Dispatch<SetStateAction<MaintenanceFormState>>,
  field: keyof MaintenanceFormState,
) {
  return (value: string) => setForm((current) => ({ ...current, [field]: value }));
}
