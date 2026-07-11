import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import type { RouteRead, RouteUpdate } from '../../../lib/api-types';
import * as routesService from '../../../services/routes.service';
import { messageForError } from '../../../lib/error-messages';
import { getRouteStats } from './route-helpers';

export function useRouteManagement() {
  const [routes, setRoutes] = useState<RouteRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingRouteId, setUpdatingRouteId] = useState<string | null>(null);

  const fetchRoutes = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await routesService.listRoutes({ pageSize: 100 });
      setRoutes(result.items);
    } catch (fetchError) {
      setError(messageForError(fetchError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchRoutes();
  }, [fetchRoutes]);

  const stats = useMemo(() => getRouteStats(routes), [routes]);

  const createRoute = async (payload: Parameters<typeof routesService.createRoute>[0]) => {
    const route = await routesService.createRoute(payload);
    setRoutes((current) => [route, ...current]);
    toast.success('Route created');
  };

  const updateRoute = async (routeId: string, patch: RouteUpdate) => {
    setUpdatingRouteId(routeId);
    try {
      await routesService.updateRoute(routeId, patch);
      await fetchRoutes();
      toast.success('Route updated');
    } catch (updateError) {
      toast.error(messageForError(updateError));
    } finally {
      setUpdatingRouteId(null);
    }
  };

  const deleteRoute = async (route: RouteRead) => {
    const confirmed = window.confirm(`Delete route ${route.number}?`);
    if (!confirmed) return;

    setUpdatingRouteId(route.id);
    try {
      await routesService.deleteRoute(route.id);
      setRoutes((current) => current.filter((item) => item.id !== route.id));
      toast.success('Route deleted');
    } catch (deleteError) {
      toast.error(messageForError(deleteError));
    } finally {
      setUpdatingRouteId(null);
    }
  };

  return {
    routes,
    stats,
    loading,
    error,
    retry: fetchRoutes,
    updatingRouteId,
    createRoute,
    updateRoute,
    deleteRoute,
  };
}
