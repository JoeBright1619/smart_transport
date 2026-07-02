import { useTranslation } from 'react-i18next';
import { AlertFiltersBar } from './alerts/AlertFiltersBar';
import { AlertErrorState, AlertLoadingState } from './alerts/AlertPageStates';
import { AlertStatsCards } from './alerts/AlertStatsCards';
import { AlertsTabs } from './alerts/AlertsTabs';
import { useAlertsManagement } from './alerts/useAlertsManagement';

export function Alerts() {
  const { t } = useTranslation('alerts');
  const alertsManagement = useAlertsManagement();

  if (alertsManagement.loading) {
    return <AlertLoadingState />;
  }

  if (alertsManagement.error) {
    return <AlertErrorState error={alertsManagement.error} onRetry={() => void alertsManagement.retry()} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <p className="text-slate-600">{t('subtitle')}</p>
      </div>

      <AlertStatsCards stats={alertsManagement.stats} />

      <AlertFiltersBar
        severity={alertsManagement.severity}
        type={alertsManagement.type}
        onSeverityChange={alertsManagement.setSeverity}
        onTypeChange={alertsManagement.setType}
      />

      <AlertsTabs
        activeTab={alertsManagement.activeTab}
        alerts={alertsManagement.alerts}
        stats={alertsManagement.stats}
        acknowledgingAlertId={alertsManagement.acknowledgingAlertId}
        page={alertsManagement.page}
        pageSize={alertsManagement.pageSize}
        total={alertsManagement.total}
        onTabChange={alertsManagement.setActiveTab}
        onAcknowledge={alertsManagement.acknowledgeAlert}
        onPageChange={alertsManagement.setPage}
      />
    </div>
  );
}
