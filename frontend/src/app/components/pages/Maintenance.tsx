import { useTranslation } from 'react-i18next';
import { MaintenanceErrorState, MaintenanceLoadingState } from './maintenance/MaintenancePageStates';
import { MaintenanceStatsCards } from './maintenance/MaintenanceStatsCards';
import { MaintenanceTable } from './maintenance/MaintenanceTable';
import { ScheduleMaintenanceDialog } from './maintenance/ScheduleMaintenanceDialog';
import { useMaintenanceManagement } from './maintenance/useMaintenanceManagement';

export function Maintenance() {
  const { t } = useTranslation('maintenance');
  const maintenance = useMaintenanceManagement();

  if (maintenance.loading) {
    return <MaintenanceLoadingState />;
  }

  if (maintenance.error) {
    return <MaintenanceErrorState error={maintenance.error} onRetry={() => void maintenance.retry()} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('title')}</h1>
          <p className="text-slate-600">{t('subtitle')}</p>
        </div>
        <ScheduleMaintenanceDialog
          vehicles={maintenance.vehicles}
          onCreateMaintenance={maintenance.createMaintenance}
        />
      </div>

      <MaintenanceStatsCards stats={maintenance.stats} />

      <MaintenanceTable
        records={maintenance.records}
        vehiclesById={maintenance.vehiclesById}
        updatingRecordId={maintenance.updatingRecordId}
        onUpdateStatus={maintenance.updateMaintenanceStatus}
      />
    </div>
  );
}
