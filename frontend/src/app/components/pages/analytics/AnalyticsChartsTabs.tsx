import { useTranslation } from 'react-i18next';
import type { AnalyticsDaily, DriverRead, RouteRead, VehicleRead } from '../../../lib/api-types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import type { FleetStatusDatum, RoutePerformanceDatum } from './analytics-helpers';
import { FilteredReportPanel } from './FilteredReportPanel';
import { FleetAnalytics } from './FleetAnalytics';
import { RouteAnalytics } from './RouteAnalytics';
import { TrendCharts } from './TrendCharts';

type AnalyticsChartsTabsProps = {
  daily: AnalyticsDaily[];
  routePerformance: RoutePerformanceDatum[];
  fleetStatus: FleetStatusDatum[];
  fleetHealth: VehicleRead[];
  routes: RouteRead[];
  vehicles: VehicleRead[];
  drivers: DriverRead[];
};

export function AnalyticsChartsTabs({
  daily,
  routePerformance,
  fleetStatus,
  fleetHealth,
  routes,
  vehicles,
  drivers,
}: AnalyticsChartsTabsProps) {
  const { t } = useTranslation('analytics');
  return (
    <Tabs defaultValue="trends" className="space-y-4">
      <TabsList>
        <TabsTrigger value="trends">{t('tabs.trends')}</TabsTrigger>
        <TabsTrigger value="routes">{t('tabs.routes')}</TabsTrigger>
        <TabsTrigger value="fleet">{t('tabs.fleet')}</TabsTrigger>
        <TabsTrigger value="custom">{t('tabs.custom')}</TabsTrigger>
      </TabsList>

      <TabsContent value="trends" className="space-y-4">
        <TrendCharts daily={daily} />
      </TabsContent>
      <TabsContent value="routes" className="space-y-4">
        <RouteAnalytics routePerformance={routePerformance} />
      </TabsContent>
      <TabsContent value="fleet" className="space-y-4">
        <FleetAnalytics fleetStatus={fleetStatus} fleetHealth={fleetHealth} />
      </TabsContent>
      <TabsContent value="custom" className="space-y-4">
        <FilteredReportPanel routes={routes} vehicles={vehicles} drivers={drivers} />
      </TabsContent>
    </Tabs>
  );
}
