import { AnalyticsChartsTabs } from './analytics/AnalyticsChartsTabs';
import { AnalyticsDateRange } from './analytics/AnalyticsDateRange';
import { AnalyticsErrorState, AnalyticsLoadingState } from './analytics/AnalyticsPageStates';
import { AnalyticsStatsCards } from './analytics/AnalyticsStatsCards';
import { useAnalyticsPage } from './analytics/useAnalyticsPage';

export function Analytics() {
  const analytics = useAnalyticsPage();

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
        <AnalyticsDateRange
          from={analytics.from}
          to={analytics.to}
          onFromChange={analytics.setFrom}
          onToChange={analytics.setTo}
        />
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
      />
    </div>
  );
}
