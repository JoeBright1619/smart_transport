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

const PAGE_SIZE = 10;

export function useAlertsManagement() {
  const [alerts, setAlerts] = useState<AlertRead[]>([]);
  const [summaryAlerts, setSummaryAlerts] = useState<AlertRead[]>([]);
  const [activeTab, setActiveTabState] = useState<AlertTab>('unacknowledged');
  const [severity, setSeverityState] = useState<AlertFilterValue<AlertSeverity>>('all');
  const [type, setTypeState] = useState<AlertFilterValue<AlertType>>('all');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acknowledgingAlertId, setAcknowledgingAlertId] = useState<string | null>(null);

  // Wrap filter setters so they always reset to page 1
  const setActiveTab = (tab: AlertTab) => { setPage(1); setActiveTabState(tab); };
  const setSeverity = (s: AlertFilterValue<AlertSeverity>) => { setPage(1); setSeverityState(s); };
  const setType = (t: AlertFilterValue<AlertType>) => { setPage(1); setTypeState(t); };

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [filteredResult, summaryResult] = await Promise.all([
        alertsService.listAlerts({
          page,
          pageSize: PAGE_SIZE,
          isAcknowledged: tabAcknowledgedValue(activeTab),
          severity: severity === 'all' ? undefined : severity,
          type: type === 'all' ? undefined : type,
        }),
        alertsService.listAlerts({ pageSize: 100 }),
      ]);
      setAlerts(filteredResult.items);
      setTotal(filteredResult.total);
      setSummaryAlerts(summaryResult.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load alerts');
    } finally {
      setLoading(false);
    }
  }, [activeTab, severity, type, page]);

  useEffect(() => {
    void loadAlerts();
  }, [loadAlerts]);

  const stats = useMemo(() => calculateAlertStats(summaryAlerts), [summaryAlerts]);

  const acknowledgeAlert = async (alert: AlertRead) => {
    const previousAlerts = alerts;
    const previousSummaryAlerts = summaryAlerts;
    const previousTotal = total;
    const acknowledged = { ...alert, isAcknowledged: true };

    setAcknowledgingAlertId(alert.id);
    setAlerts((current) =>
      current
        .map((item) => (item.id === alert.id ? acknowledged : item))
        .filter((item) => alertMatchesFilters(item, activeTab, severity, type)),
    );
    setSummaryAlerts((current) => current.map((item) => (item.id === alert.id ? acknowledged : item)));
    setTotal((t) => Math.max(0, t - (alertMatchesFilters(acknowledged, activeTab, severity, type) ? 0 : 1)));

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
      setTotal(previousTotal);
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
    page,
    total,
    pageSize: PAGE_SIZE,
    loading,
    error,
    acknowledgingAlertId,
    stats,
    setActiveTab,
    setSeverity,
    setType,
    setPage,
    acknowledgeAlert,
    retry: loadAlerts,
  };
}
