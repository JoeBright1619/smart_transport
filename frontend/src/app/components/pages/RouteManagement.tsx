import { useTranslation } from 'react-i18next';
import { CreateRouteModal } from './route-management/CreateRouteModal';
import { RouteCardsGrid } from './route-management/RouteCardsGrid';
import { RouteErrorState, RouteLoadingState } from './route-management/RoutePageStates';
import { RouteManagementTools } from './route-management/RouteManagementTools';
import { RouteStatsCards } from './route-management/RouteStatsCards';
import { RoutesTable } from './route-management/RoutesTable';
import { useRouteManagement } from './route-management/useRouteManagement';

export function RouteManagement() {
  const { t } = useTranslation('routes');
  const routeManagement = useRouteManagement();

  if (routeManagement.loading) {
    return <RouteLoadingState />;
  }

  if (routeManagement.error) {
    return (
      <RouteErrorState
        error={routeManagement.error}
        onRetry={() => void routeManagement.retry()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('title')}</h1>
          <p className="text-slate-600">{t('subtitle')}</p>
        </div>
        <CreateRouteModal onCreateRoute={routeManagement.createRoute} />
      </div>

      <RouteStatsCards stats={routeManagement.stats} />

      <RoutesTable
        routes={routeManagement.routes}
        updatingRouteId={routeManagement.updatingRouteId}
        onUpdateRoute={routeManagement.updateRoute}
        onDeleteRoute={routeManagement.deleteRoute}
      />

      <RouteManagementTools routes={routeManagement.routes} />

      <RouteCardsGrid
        routes={routeManagement.routes}
        updatingRouteId={routeManagement.updatingRouteId}
        onUpdateRoute={routeManagement.updateRoute}
      />
    </div>
  );
}
