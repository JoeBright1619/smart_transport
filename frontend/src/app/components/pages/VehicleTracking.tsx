import { useState, useMemo, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import { Icon } from 'leaflet';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Search, Gauge, Battery, AlertCircle, WifiOff } from 'lucide-react';
import type { VehicleRead, RouteRead, DriverRead } from '../../lib/api-types';
import { listVehicles } from '../../services/vehicles.service';
import { listRoutes } from '../../services/routes.service';
import { listDrivers } from '../../services/drivers.service';
import { VehicleTrackingSocket } from '../../lib/ws-client';

// Create custom icon for vehicles
const createVehicleIcon = (status: string) => {
  const color =
    status === 'active' ? '#10B981' :
    status === 'idle' ? '#F59E0B' :
    status === 'maintenance' ? '#EF4444' : '#6B7280';

  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(`
      <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="12" fill="${color}" stroke="white" stroke-width="2"/>
        <path d="M12 14h8v4h-8z M10 18h12v2h-12z M11 20h2v2h-2z M19 20h2v2h-2z" fill="white"/>
      </svg>
    `)}`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
};

export function VehicleTracking() {
  const [vehicles, setVehicles] = useState<VehicleRead[]>([]);
  const [routes, setRoutes] = useState<RouteRead[]>([]);
  const [drivers, setDrivers] = useState<DriverRead[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<VehicleRead | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const socketRef = useRef<VehicleTrackingSocket | null>(null);

  useEffect(() => {
    let mounted = true;
    let reconnectTimer: number;

    const initialize = async () => {
      try {
        const [vehicleData, routeData, driverData] = await Promise.all([
          listVehicles({ pageSize: 100 }),
          listRoutes({ pageSize: 100 }),
          listDrivers({ pageSize: 100 }),
        ]);
        if (mounted) {
          setVehicles(vehicleData.items);
          setRoutes(routeData.items);
          setDrivers(driverData.items);
        }
      } catch (err) {
        console.error('Failed to load initial tracking data', err);
      }
    };

    initialize();

    const connectWs = () => {
      if (!mounted) return;
      setConnectionStatus('connecting');

      socketRef.current = new VehicleTrackingSocket(
        (msg) => {
          if (msg.type === 'vehicle_positions') {
            setVehicles(prevVehicles => {
              const updated = [...prevVehicles];
              msg.vehicles.forEach(pos => {
                const idx = updated.findIndex(v => v.id === pos.vehicleId);
                if (idx !== -1) {
                  updated[idx] = {
                    ...updated[idx],
                    currentLocation: { lat: pos.lat, lng: pos.lng },
                    speed: pos.speed,
                    heading: pos.heading,
                    fuel: pos.fuel,
                    status: pos.status,
                    engineStatus: (pos as any).engineStatus || updated[idx].engineStatus,
                    lastUpdate: pos.timestamp,
                  };
                }
              });
              return updated;
            });

            setSelectedVehicle(prev => {
              if (!prev) return prev;
              const pos = msg.vehicles.find(v => v.vehicleId === prev.id);
              if (pos) {
                return {
                  ...prev,
                  currentLocation: { lat: pos.lat, lng: pos.lng },
                  speed: pos.speed,
                  heading: pos.heading,
                  fuel: pos.fuel,
                  status: pos.status,
                  engineStatus: (pos as any).engineStatus || prev.engineStatus,
                  lastUpdate: pos.timestamp,
                };
              }
              return prev;
            });
          }
        },
        undefined,
        () => {
          if (mounted) {
            setConnectionStatus('disconnected');
            reconnectTimer = window.setTimeout(connectWs, 5000);
          }
        }
      );

      socketRef.current.connect();
      setConnectionStatus('connected');
    };

    connectWs();

    return () => {
      mounted = false;
      clearTimeout(reconnectTimer);
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  const filteredVehicles = useMemo(() => {
    return vehicles.filter(vehicle => {
      const matchesSearch = vehicle.registrationNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           vehicle.model.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || vehicle.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [vehicles, searchTerm, statusFilter]);

  // Kigali center coordinates
  const mapCenter: [number, number] = [-1.9536, 30.0606];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">Vehicle Tracking</h1>
          <p className="text-slate-600">Real-time GPS tracking of all fleet vehicles</p>
        </div>
        {connectionStatus === 'disconnected' && (
          <Badge variant="destructive" className="flex items-center gap-1">
            <WifiOff className="size-3" />
            Disconnected — reconnecting…
          </Badge>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Vehicle List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Fleet Vehicles ({filteredVehicles.length})</CardTitle>
            <div className="space-y-2 mt-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                <Input
                  placeholder="Search vehicles..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="idle">Idle</SelectItem>
                  <SelectItem value="maintenance">Maintenance</SelectItem>
                  <SelectItem value="offline">Offline</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent className="max-h-[600px] overflow-y-auto">
            <div className="space-y-2">
              {filteredVehicles.map((vehicle) => {
                const driver = drivers.find(d => d.id === vehicle.driverId);
                const route = routes.find(r => r.id === vehicle.routeId);

                return (
                  <div
                    key={vehicle.id}
                    onClick={() => setSelectedVehicle(vehicle)}
                    className={`cursor-pointer rounded-lg border p-3 transition-colors ${
                      selectedVehicle?.id === vehicle.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <div className={`size-2 rounded-full ${
                            vehicle.status === 'active' ? 'bg-green-500' :
                            vehicle.status === 'idle' ? 'bg-yellow-500' :
                            vehicle.status === 'maintenance' ? 'bg-red-500' :
                            'bg-slate-400'
                          }`} />
                          <p className="font-medium text-sm">{vehicle.registrationNumber}</p>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">{vehicle.model}</p>
                        {route && (
                          <p className="text-xs text-blue-600 mt-1">Route {route.number}</p>
                        )}
                        {driver && (
                          <p className="text-xs text-slate-500">{driver.name}</p>
                        )}
                      </div>
                      <Badge variant={vehicle.status === 'active' ? 'default' : 'secondary'}>
                        {vehicle.status}
                      </Badge>
                    </div>
                    {vehicle.status === 'active' && vehicle.speed !== null && vehicle.fuel !== null && (
                      <div className="mt-2 flex items-center gap-3 text-xs text-slate-600">
                        <span className="flex items-center gap-1">
                          <Gauge className="size-3" />
                          {Math.round(vehicle.speed)} km/h
                        </span>
                        <span className="flex items-center gap-1">
                          <Battery className="size-3" />
                          {vehicle.fuel}%
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Map */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Live Map View</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[600px] rounded-lg overflow-hidden border">
              <MapContainer
                center={mapCenter}
                zoom={13}
                style={{ height: '100%', width: '100%' }}
                scrollWheelZoom={true}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />

                {/* Vehicle markers */}
                {filteredVehicles.map((vehicle) => {
                  if (!vehicle.currentLocation) return null;

                  const driver = drivers.find(d => d.id === vehicle.driverId);
                  const route = routes.find(r => r.id === vehicle.routeId);

                  return (
                    <Marker
                      key={vehicle.id}
                      position={[vehicle.currentLocation.lat, vehicle.currentLocation.lng]}
                      icon={createVehicleIcon(vehicle.status)}
                      eventHandlers={{
                        click: () => setSelectedVehicle(vehicle)
                      }}
                    >
                      <Popup>
                        <div className="p-2">
                          <p className="font-bold">{vehicle.registrationNumber}</p>
                          <p className="text-sm text-slate-600">{vehicle.model}</p>
                          {route && (
                            <p className="text-sm text-blue-600 mt-1">Route {route.number} - {route.name}</p>
                          )}
                          {driver && (
                            <p className="text-sm mt-1">Driver: {driver.name}</p>
                          )}
                          {vehicle.status === 'active' && vehicle.speed !== null && vehicle.fuel !== null && (
                            <div className="mt-2 space-y-1 text-sm">
                              <p>Speed: {Math.round(vehicle.speed)} km/h</p>
                              <p>Fuel: {vehicle.fuel}%</p>
                              <p>Status: {vehicle.engineStatus}</p>
                            </div>
                          )}
                          <Badge className="mt-2" variant={vehicle.status === 'active' ? 'default' : 'secondary'}>
                            {vehicle.status}
                          </Badge>
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}

                {/* Draw route lines */}
                {routes.map((route) => {
                  const routeCoordinates: [number, number][] = route.stops.map(stop => [
                    stop.lat,
                    stop.lng
                  ]);

                  return (
                    <Polyline
                      key={route.id}
                      positions={routeCoordinates}
                      color={route.color}
                      weight={3}
                      opacity={0.6}
                    />
                  );
                })}
              </MapContainer>
            </div>

            {/* Selected Vehicle Details */}
            {selectedVehicle && (
              <Card className="mt-4">
                <CardContent className="pt-4">
                  <div className="grid gap-4 md:grid-cols-3">
                    <div>
                      <p className="text-xs text-slate-500">Vehicle</p>
                      <p className="font-medium">{selectedVehicle.registrationNumber}</p>
                      <p className="text-sm text-slate-600">{selectedVehicle.model}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Status</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge>{selectedVehicle.status}</Badge>
                        {selectedVehicle.status === 'active' && selectedVehicle.speed !== null && (
                          <span className="text-sm">{Math.round(selectedVehicle.speed)} km/h</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Fuel & Engine</p>
                      <div className="flex items-center gap-3 mt-1">
                        {selectedVehicle.fuel !== null && (
                          <span className="flex items-center gap-1 text-sm">
                            <Battery className="size-4" />
                            {selectedVehicle.fuel}%
                          </span>
                        )}
                        <span className="flex items-center gap-1 text-sm">
                          <AlertCircle className={`size-4 ${
                            selectedVehicle.engineStatus === 'good' ? 'text-green-500' :
                            selectedVehicle.engineStatus === 'warning' ? 'text-yellow-500' :
                            'text-red-500'
                          }`} />
                          {selectedVehicle.engineStatus}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
