import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ArrivalEstimate } from '../../../lib/api-types';
import * as arrivalsService from '../../../services/arrivals.service';
import * as routesService from '../../../services/routes.service';
import { collectStops, sortArrivals, type StopOption } from './arrival-helpers';

export function useArrivalTimes() {
  const [stops, setStops] = useState<StopOption[]>([]);
  const [selectedStopId, setSelectedStopId] = useState('');
  const [estimates, setEstimates] = useState<ArrivalEstimate[]>([]);
  const [loadingStops, setLoadingStops] = useState(true);
  const [loadingArrivals, setLoadingArrivals] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadStops = useCallback(async () => {
    setLoadingStops(true);
    setError(null);

    try {
      const routesResult = await routesService.listRoutes({ pageSize: 100 });
      const stopOptions = collectStops(routesResult.items);
      setStops(stopOptions);
      setSelectedStopId((current) => current || stopOptions[0]?.id || '');
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load stops');
    } finally {
      setLoadingStops(false);
    }
  }, []);

  const loadArrivals = useCallback(async (stopId: string) => {
    if (!stopId) {
      setEstimates([]);
      return;
    }

    setLoadingArrivals(true);

    try {
      const result = await arrivalsService.getArrivals(stopId);
      setEstimates(sortArrivals(result));
      setLastUpdated(new Date());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load arrivals');
    } finally {
      setLoadingArrivals(false);
    }
  }, []);

  useEffect(() => {
    void loadStops();
  }, [loadStops]);

  useEffect(() => {
    void loadArrivals(selectedStopId);

    if (!selectedStopId) return;

    const intervalId = window.setInterval(() => {
      void loadArrivals(selectedStopId);
    }, 10000);

    return () => window.clearInterval(intervalId);
  }, [loadArrivals, selectedStopId]);

  const selectedStop = useMemo(
    () => stops.find((stop) => stop.id === selectedStopId) ?? null,
    [selectedStopId, stops],
  );

  return {
    stops,
    selectedStop,
    selectedStopId,
    estimates,
    loadingStops,
    loadingArrivals,
    error,
    lastUpdated,
    setSelectedStopId,
    retry: loadStops,
  };
}
