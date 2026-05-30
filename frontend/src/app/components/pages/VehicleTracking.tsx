import { useState, useMemo, useEffect, useRef } from 'react';
import { Badge } from '../ui/badge';
import { WifiOff } from 'lucide-react';
import type { RouteRead, DriverRead } from '../../lib/api-types';
import type { Marker as LMarker } from 'leaflet';
import { listVehicles } from '../../services/vehicles.service';
import { listRoutes } from '../../services/routes.service';
import { listDrivers } from '../../services/drivers.service';
import { VehicleTrackingSocket } from '../../lib/ws-client';
import type { TrackedVehicle } from './vehicle-tracking/vehicle-tracking-helpers';
import { VehicleListPanel } from './vehicle-tracking/VehicleListPanel';
import { VehicleMapView } from './vehicle-tracking/VehicleMapView';

export function VehicleTracking() {
  const [vehicles, setVehicles] = useState<TrackedVehicle[]>([]);
  const [routes, setRoutes] = useState<RouteRead[]>([]);
  const [drivers, setDrivers] = useState<DriverRead[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<TrackedVehicle | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const socketRef = useRef<VehicleTrackingSocket | null>(null);
  const markerRefs = useRef<Map<string, LMarker>>(new Map());

  useEffect(() => {
    let mounted = true;
    let reconnectTimer: number;

    Promise.all([
      listVehicles({ pageSize: 100 }),
      listRoutes({ pageSize: 100 }),
      listDrivers({ pageSize: 100 }),
    ]).then(([vd, rd, dd]) => {
      if (!mounted) return;
      setVehicles(vd.items);
      setRoutes(rd.items);
      setDrivers(dd.items);
    }).catch(err => console.error('Failed to load tracking data', err));

    const connectWs = () => {
      if (!mounted) return;
      setConnectionStatus('connecting');
      socketRef.current = new VehicleTrackingSocket(
        (msg) => {
          if (msg.type !== 'vehicle_positions') return;
          setVehicles(prev => {
            const updated = [...prev];
            msg.vehicles.forEach(pos => {
              const idx = updated.findIndex(v => v.id === pos.vehicleId);
              if (idx !== -1) updated[idx] = { ...updated[idx], currentLocation: { lat: pos.lat, lng: pos.lng }, speed: pos.speed, heading: pos.heading, fuel: pos.fuel, status: pos.status, engineStatus: pos.engineStatus || updated[idx].engineStatus, nextStopName: pos.nextStopName, progressPct: pos.progressPct, lastUpdate: pos.timestamp };
            });
            return updated;
          });
          setSelectedVehicle(prev => {
            if (!prev) return prev;
            const pos = msg.vehicles.find(v => v.vehicleId === prev.id);
            if (!pos) return prev;
            return { ...prev, currentLocation: { lat: pos.lat, lng: pos.lng }, speed: pos.speed, heading: pos.heading, fuel: pos.fuel, status: pos.status, engineStatus: pos.engineStatus || prev.engineStatus, nextStopName: pos.nextStopName, progressPct: pos.progressPct, lastUpdate: pos.timestamp };
          });
        },
        undefined,
        () => { if (mounted) { setConnectionStatus('disconnected'); reconnectTimer = window.setTimeout(connectWs, 5000); } },
      );
      socketRef.current.connect();
      setConnectionStatus('connected');
    };

    connectWs();
    return () => { mounted = false; clearTimeout(reconnectTimer); socketRef.current?.disconnect(); };
  }, []);

  useEffect(() => {
    if (selectedVehicle?.id) markerRefs.current.get(selectedVehicle.id)?.openPopup();
  }, [selectedVehicle?.id]);

  const filteredVehicles = useMemo(() =>
    vehicles.filter(v => {
      const matchSearch = v.registrationNumber.toLowerCase().includes(searchTerm.toLowerCase()) || v.model.toLowerCase().includes(searchTerm.toLowerCase());
      return matchSearch && (statusFilter === 'all' || v.status === statusFilter);
    }),
    [vehicles, searchTerm, statusFilter],
  );

  const selectedRoute = useMemo<RouteRead | null>(
    () => selectedVehicle?.routeId ? (routes.find(r => r.id === selectedVehicle.routeId) ?? null) : null,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selectedVehicle?.routeId, routes],
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Vehicle Tracking</h1>
          <p className="text-slate-600">Real-time GPS tracking of all fleet vehicles</p>
        </div>
        {connectionStatus === 'disconnected' && (
          <Badge variant="destructive" className="flex items-center gap-1">
            <WifiOff className="size-3" /> Disconnected — reconnecting…
          </Badge>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <VehicleListPanel
          vehicles={filteredVehicles} drivers={drivers} routes={routes}
          selectedVehicle={selectedVehicle} searchTerm={searchTerm} statusFilter={statusFilter}
          onSelectVehicle={setSelectedVehicle} onSearchChange={setSearchTerm} onStatusFilterChange={setStatusFilter}
        />
        <VehicleMapView
          vehicles={filteredVehicles} routes={routes} drivers={drivers}
          selectedVehicle={selectedVehicle} selectedRoute={selectedRoute}
          markerRefs={markerRefs} onSelectVehicle={setSelectedVehicle}
        />
      </div>
    </div>
  );
}
