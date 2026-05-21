import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import type { AlertRead, AlertSeverity, AlertType } from '../../../lib/api-types';
import * as alertsService from '../../../services/alerts.service';
import {
  alertMatchesFilters,
  calculateAlertStats,
  tabAcknowledgedValue,
  type AlertFilterValue,
  type AlertTab,
} from './alert-helpers';

export function useAlertsManagement() {
  const [alerts, setAlerts] = useState<AlertRead[]>([]);
  const [summaryAlerts, setSummaryAlerts] = useState<AlertRead[]>([]);
  const [activeTab, setActiveTab] = useState<AlertTab>('unacknowledged');
  const [severity, setSeverity] = useState<AlertFilterValue<AlertSeverity>>('all');
  const [type, setType] = useState<AlertFilterValue<AlertType>>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acknowledgingAlertId, setAcknowledgingAlertId] = useState<string | null>(null);

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [filteredResult, summaryResult] = await Promise.all([
        alertsService.listAlerts({
          pageSize: 100,
          isAcknowledged: tabAcknowledgedValue(activeTab),
          severity: severity === 'all' ? undefined : severity,
          type: type === 'all' ? undefined : type,
        }),
        alertsService.listAlerts({ pageSize: 100 }),
      ]);
      setAlerts(filteredResult.items);
      setSummaryAlerts(summaryResult.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load alerts');
    } finally {
      setLoading(false);
    }
  }, [activeTab, severity, type]);

  useEffect(() => {
    void loadAlerts();
  }, [loadAlerts]);

  const stats = useMemo(() => calculateAlertStats(summaryAlerts), [summaryAlerts]);

  const acknowledgeAlert = async (alert: AlertRead) => {
    const previousAlerts = alerts;
    const previousSummaryAlerts = summaryAlerts;
    const acknowledged = { ...alert, isAcknowledged: true };

    setAcknowledgingAlertId(alert.id);
    setAlerts((current) =>
      current
        .map((item) => (item.id === alert.id ? acknowledged : item))
        .filter((item) => alertMatchesFilters(item, activeTab, severity, type)),
    );
    setSummaryAlerts((current) => current.map((item) => (item.id === alert.id ? acknowledged : item)));

    try {
      const confirmed = await alertsService.acknowledgeAlert(alert.id);
      setSummaryAlerts((current) => current.map((item) => (item.id === confirmed.id ? confirmed : item)));
      setAlerts((current) =>
        current
          .map((item) => (item.id === confirmed.id ? confirmed : item))
          .filter((item) => alertMatchesFilters(item, activeTab, severity, type)),
      );
      toast.success('Alert acknowledged');
    } catch (ackError) {
      setAlerts(previousAlerts);
      setSummaryAlerts(previousSummaryAlerts);
      toast.error(ackError instanceof Error ? ackError.message : 'Unable to acknowledge alert');
    } finally {
      setAcknowledgingAlertId(null);
    }
  };

  return {
    alerts,
    activeTab,
    severity,
    type,
    loading,
    error,
    acknowledgingAlertId,
    stats,
    setActiveTab,
    setSeverity,
    setType,
    acknowledgeAlert,
    retry: loadAlerts,
  };
}
