import { AlertTriangle, Bell, CheckCircle, Clock, Users, XCircle } from 'lucide-react';
import type { AlertRead, AlertSeverity, AlertType } from '../../../lib/api-types';

export type AlertTab = 'unacknowledged' | 'acknowledged' | 'all';
export type AlertFilterValue<T extends string> = T | 'all';

export type AlertStats = {
  unread: number;
  critical: number;
  high: number;
  acknowledged: number;
  total: number;
};

export const alertSeverityOptions: Array<AlertSeverity | 'all'> = [
  'all',
  'critical',
  'high',
  'medium',
  'low',
];

export const alertTypeOptions: Array<AlertType | 'all'> = [
  'all',
  'delay',
  'breakdown',
  'maintenance',
  'geofence',
  'speeding',
  'info',
  'capacity',
];

export function tabAcknowledgedValue(tab: AlertTab): boolean | undefined {
  if (tab === 'unacknowledged') return false;
  if (tab === 'acknowledged') return true;
  return undefined;
}

export function calculateAlertStats(alerts: AlertRead[]): AlertStats {
  const unacknowledged = alerts.filter((alert) => !alert.isAcknowledged);

  return {
    unread: unacknowledged.length,
    critical: unacknowledged.filter((alert) => alert.severity === 'critical').length,
    high: unacknowledged.filter((alert) => alert.severity === 'high').length,
    acknowledged: alerts.filter((alert) => alert.isAcknowledged).length,
    total: alerts.length,
  };
}

export function alertMatchesFilters(
  alert: AlertRead,
  tab: AlertTab,
  severity: AlertFilterValue<AlertSeverity>,
  type: AlertFilterValue<AlertType>,
): boolean {
  const acknowledged = tabAcknowledgedValue(tab);
  if (acknowledged !== undefined && alert.isAcknowledged !== acknowledged) return false;
  if (severity !== 'all' && alert.severity !== severity) return false;
  if (type !== 'all' && alert.type !== type) return false;
  return true;
}

export function alertIcon(type: AlertType) {
  switch (type) {
    case 'delay':
      return Clock;
    case 'breakdown':
      return XCircle;
    case 'maintenance':
      return AlertTriangle;
    case 'capacity':
      return Users;
    default:
      return Bell;
  }
}

export function severityColor(severity: AlertSeverity): string {
  if (severity === 'critical') return 'text-red-500';
  if (severity === 'high') return 'text-orange-500';
  if (severity === 'medium') return 'text-yellow-500';
  return 'text-blue-500';
}

export function severityBadgeVariant(severity: AlertSeverity): 'default' | 'secondary' | 'destructive' {
  if (severity === 'critical' || severity === 'high') return 'destructive';
  if (severity === 'low') return 'secondary';
  return 'default';
}

export { AlertTriangle, Bell, CheckCircle };
