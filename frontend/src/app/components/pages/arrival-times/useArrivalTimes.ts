import { useCallback, useEffect, useMemo, useState } from 'react';
import * as arrivalsService from '../../../services/arrivals.service';
import * as routesService from '../../../services/routes.service';
import {
  ALL_STOPS_ID,
  collectStops,
  sortArrivals,
  type ArrivalEstimateWithStop,
  type StopOption,
} from './arrival-helpers';

export function useArrivalTimes() {
  const [stops, setStops] = useState<StopOption[]>([]);
  const [selectedStopId, setSelectedStopId] = useState(ALL_STOPS_ID);
  const [estimates, setEstimates] = useState<ArrivalEstimateWithStop[]>([]);
  const [loadingStops, setLoadingStops] = useState(true);
  const [loadingArrivals, setLoadingArrivals] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadStops = useCallback(async () => {
    setLoadingStops(true);
    setError(null);

    try {
      const routesResult = await routesService.listRoutes({ isActive: true, pageSize: 100 });
      const stopOptions = collectStops(routesResult.items);
      setStops(stopOptions);
      setSelectedStopId((current) => current || ALL_STOPS_ID);
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
      if (stopId === ALL_STOPS_ID) {
        const results = await Promise.all(
          stops.map(async (stop) => {
            const arrivals = await arrivalsService.getArrivals(stop.id);
            return arrivals.map((arrival) => ({
              ...arrival,
              stopId: stop.id,
              stopName: stop.name,
            }));
          }),
        );
        const byVehicleId = new Map<string, ArrivalEstimateWithStop>();

        results.flat().forEach((arrival) => {
          const current = byVehicleId.get(arrival.vehicleId);
          if (!current) {
            byVehicleId.set(arrival.vehicleId, arrival);
            return;
          }

          const currentEta = current.etaMinutes ?? Number.POSITIVE_INFINITY;
          const nextEta = arrival.etaMinutes ?? Number.POSITIVE_INFINITY;
          if (nextEta < currentEta) {
            byVehicleId.set(arrival.vehicleId, arrival);
          }
        });

        setEstimates(sortArrivals([...byVehicleId.values()]));
      } else {
        const stop = stops.find((item) => item.id === stopId);
        const result = await arrivalsService.getArrivals(stopId);
        setEstimates(
          sortArrivals(
            result.map((arrival) => ({
              ...arrival,
              stopId,
              stopName: stop?.name,
            })),
          ),
        );
      }
      setLastUpdated(new Date());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load arrivals');
    } finally {
      setLoadingArrivals(false);
    }
  }, [stops]);

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
    () =>
      selectedStopId === ALL_STOPS_ID
        ? {
            id: ALL_STOPS_ID,
            name: 'All Stops',
            lat: 0,
            lng: 0,
            order: 0,
            routeIds: [],
            routeLabels: ['All active routes'],
          }
        : stops.find((stop) => stop.id === selectedStopId) ?? null,
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
