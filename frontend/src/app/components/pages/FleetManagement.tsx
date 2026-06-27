import { BarChart, Bus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { FleetErrorState, FleetLoadingState } from './fleet-management/FleetPageStates';
import { FleetStatsCards } from './fleet-management/FleetStatsCards';
import { FleetUtilizationTab } from './fleet-management/FleetUtilizationTab';
import { useFleetManagement } from './fleet-management/useFleetManagement';
import { VehicleFleetTable } from './fleet-management/VehicleFleetTable';

export function FleetManagement() {
  const { t } = useTranslation('fleet');
  const fleet = useFleetManagement();

  if (fleet.loading) {
    return <FleetLoadingState />;
  }

  if (fleet.error) {
    return <FleetErrorState error={fleet.error} onRetry={() => void fleet.retry()} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <p className="text-slate-600">{t('subtitle')}</p>
      </div>

      <FleetStatsCards stats={fleet.stats} />

      <Tabs defaultValue="vehicles" className="space-y-4">
        <TabsList>
          <TabsTrigger value="vehicles">
            <Bus className="mr-2 size-4" />
            {t('tabs.vehicles')}
          </TabsTrigger>
          <TabsTrigger value="utilization">
            <BarChart className="mr-2 size-4" />
            {t('tabs.utilization')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="vehicles" className="space-y-4">
          <VehicleFleetTable
            searchTerm={fleet.searchTerm}
            setSearchTerm={fleet.setSearchTerm}
            vehicles={fleet.filteredVehicles}
            drivers={fleet.drivers}
            routes={fleet.routes}
            updatingVehicleId={fleet.updatingVehicleId}
            updateVehicle={fleet.updateVehicle}
            deleteVehicle={fleet.deleteVehicle}
            dialogOpen={fleet.dialogOpen}
            setDialogOpen={fleet.setDialogOpen}
            form={fleet.form}
            setForm={fleet.setForm}
            submitting={fleet.submitting}
            createVehicle={fleet.createVehicle}
          />
        </TabsContent>

        <TabsContent value="utilization" className="space-y-4">
          <FleetUtilizationTab
            vehicles={fleet.vehicles}
            driversById={fleet.driversById}
            routesById={fleet.routesById}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
