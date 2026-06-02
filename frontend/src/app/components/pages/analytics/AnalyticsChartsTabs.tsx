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
  return (
    <Tabs defaultValue="trends" className="space-y-4">
      <TabsList>
        <TabsTrigger value="trends">Operational Trends</TabsTrigger>
        <TabsTrigger value="routes">Route Performance</TabsTrigger>
        <TabsTrigger value="fleet">Fleet Analysis</TabsTrigger>
        <TabsTrigger value="custom">Custom Reports</TabsTrigger>
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
