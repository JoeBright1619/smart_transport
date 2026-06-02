import { FileDown } from 'lucide-react';
import { Button } from '../ui/button';
import { AnalyticsChartsTabs } from './analytics/AnalyticsChartsTabs';
import { AnalyticsDateRange } from './analytics/AnalyticsDateRange';
import { AnalyticsErrorState, AnalyticsLoadingState } from './analytics/AnalyticsPageStates';
import { AnalyticsStatsCards } from './analytics/AnalyticsStatsCards';
import { exportAnalyticsPDF } from './analytics/analytics-pdf';
import { useAnalyticsPage } from './analytics/useAnalyticsPage';
import { useAuth } from '../../lib/auth-context';

export function Analytics() {
  const analytics = useAnalyticsPage();
  const { user } = useAuth();

  if (analytics.loading) {
    return <AnalyticsLoadingState />;
  }

  if (analytics.error) {
    return <AnalyticsErrorState error={analytics.error} onRetry={() => void analytics.retry()} />;
  }

  if (!analytics.data) {
    return <AnalyticsErrorState error="No analytics data returned" onRetry={() => void analytics.retry()} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics & Reporting</h1>
          <p className="text-slate-600">Performance metrics and operational insights</p>
        </div>
        <div className="flex items-center gap-2">
          <AnalyticsDateRange
            from={analytics.from}
            to={analytics.to}
            onFromChange={analytics.setFrom}
            onToChange={analytics.setTo}
          />
          <Button
            variant="outline"
            onClick={async () =>
              exportAnalyticsPDF({
                data: analytics.data!,
                routePerformance: analytics.routePerformance,
                fleetStatus: analytics.fleetStatus,
                from: analytics.from,
                to: analytics.to,
                tenantName: user?.tenantName,
                tenantEmail: user?.tenantEmail,
                tenantAddress: user?.tenantAddress,
                tenantPhone: user?.tenantPhone,
                tenantLogoPath: user?.tenantLogoPath,
              })
            }
          >
            <FileDown className="mr-2 size-4" />
            Export PDF
          </Button>
        </div>
      </div>

      <AnalyticsStatsCards
        summary={analytics.data.summary}
        trends={analytics.trends}
        dayCount={analytics.data.daily.length}
      />

      <AnalyticsChartsTabs
        daily={analytics.data.daily}
        routePerformance={analytics.routePerformance}
        fleetStatus={analytics.fleetStatus}
        fleetHealth={analytics.fleetHealth}
        routes={analytics.routes}
        vehicles={analytics.vehicles}
        drivers={analytics.drivers}
      />
    </div>
  );
}
