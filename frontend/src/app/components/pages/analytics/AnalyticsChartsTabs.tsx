import type { AnalyticsDaily, VehicleRead } from '../../../lib/api-types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import type { FleetStatusDatum, RoutePerformanceDatum } from './analytics-helpers';
import { FleetAnalytics } from './FleetAnalytics';
import { RouteAnalytics } from './RouteAnalytics';
import { TrendCharts } from './TrendCharts';

type AnalyticsChartsTabsProps = {
  daily: AnalyticsDaily[];
  routePerformance: RoutePerformanceDatum[];
  fleetStatus: FleetStatusDatum[];
  fleetHealth: VehicleRead[];
};

export function AnalyticsChartsTabs({
  daily,
  routePerformance,
  fleetStatus,
  fleetHealth,
}: AnalyticsChartsTabsProps) {
  return (
    <Tabs defaultValue="trends" className="space-y-4">
      <TabsList>
        <TabsTrigger value="trends">Operational Trends</TabsTrigger>
        <TabsTrigger value="routes">Route Performance</TabsTrigger>
        <TabsTrigger value="fleet">Fleet Analysis</TabsTrigger>
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
    </Tabs>
  );
}
