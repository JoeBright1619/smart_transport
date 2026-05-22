import type {
  MaintenanceCreate,
  MaintenanceRead,
  MaintenanceStatus,
  MaintenanceType,
} from '../../../lib/api-types';

export type MaintenanceFormState = {
  vehicleId: string;
  type: MaintenanceType;
  description: string;
  scheduledDate: string;
  cost: string;
  nextDue: string;
};

export type MaintenanceStats = {
  scheduled: number;
  inProgress: number;
  completed: number;
  totalCost: string;
};

export const maintenanceTypeOptions: MaintenanceType[] = ['routine', 'repair', 'inspection'];

export const statusLabels: Record<MaintenanceStatus, string> = {
  scheduled: 'Scheduled',
  'in-progress': 'In Progress',
  completed: 'Completed',
};

export const initialMaintenanceFormState: MaintenanceFormState = {
  vehicleId: '',
  type: 'routine',
  description: '',
  scheduledDate: todayDate(),
  cost: '0',
  nextDue: '',
};

export function buildMaintenanceCreatePayload(form: MaintenanceFormState): MaintenanceCreate {
  return {
    vehicleId: form.vehicleId,
    type: form.type,
    description: form.description.trim(),
    scheduledDate: form.scheduledDate,
    cost: Number(form.cost),
    nextDue: form.nextDue || undefined,
  };
}

export function calculateMaintenanceStats(records: MaintenanceRead[]): MaintenanceStats {
  const totalCost = records.reduce((sum, record) => sum + record.cost, 0);

  return {
    scheduled: records.filter((record) => record.status === 'scheduled').length,
    inProgress: records.filter((record) => record.status === 'in-progress').length,
    completed: records.filter((record) => record.status === 'completed').length,
    totalCost: `${(totalCost / 1000).toFixed(0)}K`,
  };
}

export function statusBadgeVariant(status: MaintenanceStatus): 'default' | 'secondary' | 'outline' {
  if (status === 'completed') return 'default';
  if (status === 'in-progress') return 'secondary';
  return 'outline';
}

export function formatDate(value: string | null): string {
  if (!value) return '-';
  return new Date(value).toLocaleDateString();
}

function todayDate(): string {
  return new Date().toISOString().slice(0, 10);
}
