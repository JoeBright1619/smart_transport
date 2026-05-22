import type { DriverCreate, DriverRead, DriverStatus } from '../../../lib/api-types';

export type DriverFormState = {
  name: string;
  licenseNumber: string;
  phone: string;
  certificationExpiry: string;
};

export type DriverStats = {
  total: number;
  onTrip: number;
  available: number;
  avgRating: string;
};

export const initialDriverFormState: DriverFormState = {
  name: '',
  licenseNumber: '',
  phone: '',
  certificationExpiry: nextYearDate(),
};

export const statusLabels: Record<DriverStatus, string> = {
  available: 'Available',
  'on-trip': 'On Trip',
  'off-duty': 'Off Duty',
};

export function buildDriverCreatePayload(form: DriverFormState): DriverCreate {
  return {
    name: form.name.trim(),
    licenseNumber: form.licenseNumber.trim(),
    phone: form.phone.trim(),
    certificationExpiry: form.certificationExpiry,
  };
}

export function calculateDriverStats(drivers: DriverRead[]): DriverStats {
  const totalRating = drivers.reduce((sum, driver) => sum + driver.rating, 0);

  return {
    total: drivers.length,
    onTrip: drivers.filter((driver) => driver.status === 'on-trip').length,
    available: drivers.filter((driver) => driver.status === 'available').length,
    avgRating: drivers.length > 0 ? (totalRating / drivers.length).toFixed(1) : '0.0',
  };
}

export function driverInitials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

export function statusBadgeVariant(status: DriverStatus): 'default' | 'secondary' | 'outline' {
  if (status === 'on-trip') return 'default';
  if (status === 'available') return 'secondary';
  return 'outline';
}

function nextYearDate(): string {
  const date = new Date();
  date.setFullYear(date.getFullYear() + 1);
  return date.toISOString().slice(0, 10);
}
