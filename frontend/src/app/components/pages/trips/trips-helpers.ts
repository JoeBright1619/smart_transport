import type { DelayStatus, TripStatus } from '../../../lib/api-types';

/**
 * Format a minute count for display, rolling over to hours past 60:
 *   45 -> "45min", 60 -> "1hr", 90 -> "1hr30min", 366 -> "6hr06min".
 * Sign is ignored — the badge label conveys late/early separately.
 */
export function formatDurationMinutes(minutes: number): string {
  const total = Math.round(Math.abs(minutes));
  if (total < 60) return `${total}min`;
  const hours = Math.floor(total / 60);
  const mins = total % 60;
  return mins === 0 ? `${hours}hr` : `${hours}hr${String(mins).padStart(2, '0')}min`;
}

export function tripStatusBadgeVariant(
  status: TripStatus,
): 'default' | 'secondary' | 'outline' | 'destructive' {
  switch (status) {
    case 'active':
      return 'default';
    case 'scheduled':
      return 'secondary';
    case 'cancelled':
      return 'destructive';
    default:
      return 'outline'; // completed
  }
}

export function delayBadgeVariant(
  status: DelayStatus,
): 'secondary' | 'outline' | 'destructive' {
  switch (status) {
    case 'delayed':
      return 'destructive';
    case 'quick':
      return 'secondary';
    default:
      return 'outline'; // on_time
  }
}
