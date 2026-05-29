import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import type { RouteRead, StopRead, ArrivalEstimate } from '../../lib/api-types';
import { listRoutes } from '../../services/routes.service';
import { getArrivals } from '../../services/arrivals.service';
import { MapPin, Clock, Navigation, Heart, Search, Bus } from 'lucide-react';
import { useAuth } from '../../lib/auth-context';

const FAVORITE_STOPS_STORAGE_KEY = 'passenger-favourite-stops';

function loadFavoriteStops(): string[] {
  try {
    const stored = localStorage.getItem(FAVORITE_STOPS_STORAGE_KEY);
    if (!stored) return [];

    const parsed = JSON.parse(stored);
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === 'string') : [];
  } catch {
    return [];
  }
}

export function PassengerApp() {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [routes, setRoutes] = useState<RouteRead[]>([]);
  const [allStops, setAllStops] = useState<StopRead[]>([]);
  const [selectedStop, setSelectedStop] = useState<string | null>(null);
  const [arrivals, setArrivals] = useState<ArrivalEstimate[]>([]);
  const [favoriteStops, setFavoriteStops] = useState<string[]>(loadFavoriteStops);

  useEffect(() => {
    listRoutes({ isActive: true, pageSize: 100 })
      .then(res => {
        setRoutes(res.items);
        const stopMap = new Map<string, StopRead>();
        res.items.forEach(route => {
          route.stops.forEach(stop => stopMap.set(stop.id, stop));
        });
        setAllStops(Array.from(stopMap.values()));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedStop) {
      setArrivals([]);
      return;
    }

    const fetchArrivals = () => {
      getArrivals(selectedStop)
        .then(data => {
          const sorted = [...data].sort((a, b) => {
            if (a.etaMinutes === null) return 1;
            if (b.etaMinutes === null) return -1;
            return (a.etaMinutes ?? 0) - (b.etaMinutes ?? 0);
          });
          setArrivals(sorted);
        })
        .catch(() => {});
    };

    fetchArrivals();
    const interval = setInterval(fetchArrivals, 10000);
    return () => clearInterval(interval);
  }, [selectedStop]);

  useEffect(() => {
    try {
      localStorage.setItem(FAVORITE_STOPS_STORAGE_KEY, JSON.stringify(favoriteStops));
    } catch {
      // Ignore storage failures; favourites still work for the current session.
    }
  }, [favoriteStops]);

  const filteredStops = allStops.filter(stop =>
    stop.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const favoriteStopsList = allStops.filter(s => favoriteStops.includes(s.id));
  const selectedStopName = allStops.find(s => s.id === selectedStop)?.name;
  const tenantName = user?.tenantName ?? 'Transport System';
  const tenantContact = user?.tenantPhone ?? user?.tenantEmail;

  const toggleFavorite = (stopId: string) => {
    setFavoriteStops(prev =>
      prev.includes(stopId) ? prev.filter(id => id !== stopId) : [...prev, stopId]
    );
  };

  return (
    <div className="max-w-5xl mx-auto pb-20 px-4 space-y-6">
      {/* Passenger App Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold">{tenantName}</h1>
            <p className="text-sm text-blue-100">Passenger service updates</p>
          </div>
          <Bus className="size-10" />
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-blue-300" />
          <Input
            placeholder="Search for bus stops..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-blue-200"
          />
        </div>
      </div>

      {/* Main content: stops list + side panel */}
      <div className="grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        {/* Left: Favorite & Nearby Stops */}
        <div className="space-y-6">
          {/* Favorite Stops */}
          {favoriteStopsList.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Heart className="size-5 text-red-500" />
                  Favorite Stops
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {favoriteStopsList.map(stop => (
                    <Button
                      key={stop.id}
                      variant={selectedStop === stop.id ? 'default' : 'outline'}
                      className="w-full justify-start"
                      onClick={() => setSelectedStop(stop.id)}
                    >
                      <MapPin className="mr-2 size-4" />
                      {stop.name}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Nearby Stops */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Navigation className="size-5 text-blue-600" />
                {searchTerm ? 'Search Results' : 'Nearby Stops'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {filteredStops.map(stop => {
                  const routesAtStop = routes.filter(r =>
                    r.stops.some(s => s.id === stop.id)
                  );
                  const isFavorite = favoriteStops.includes(stop.id);

                  return (
                    <div
                      key={stop.id}
                      onClick={() => setSelectedStop(stop.id)}
                      className={`cursor-pointer rounded-lg border p-3 transition-colors ${
                        selectedStop === stop.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <MapPin className="size-4 text-slate-400" />
                            <p className="font-medium">{stop.name}</p>
                          </div>
                          <p className="text-xs text-slate-500 mt-1 ml-6">
                            {routesAtStop.length} route{routesAtStop.length !== 1 ? 's' : ''} available
                          </p>
                          <div className="flex flex-wrap gap-1 mt-2 ml-6">
                            {routesAtStop.map(route => (
                              <Badge key={route.id} variant="secondary" className="text-xs">
                                {route.number}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <button
                          onClick={(e) => { e.stopPropagation(); toggleFavorite(stop.id); }}
                          className="ml-2 p-1"
                        >
                          <Heart className={`size-4 ${isFavorite ? 'fill-red-500 text-red-500' : 'text-slate-300'}`} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Next Arrivals + Service Info */}
        <div className="space-y-6">
          {/* Arrival Times for Selected Stop */}
          {selectedStop && arrivals.length > 0 && (
            <Card className="border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Clock className="size-5 text-blue-600" />
                  Next Arrivals at {selectedStopName}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {arrivals.map((arrival) => {
                    const route = routes.find(r => r.id === arrival.routeId);

                    return (
                      <div key={arrival.vehicleId} className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="mb-3 flex items-center gap-2">
                          <span className="size-2 rounded-full bg-green-500 animate-pulse" />
                          <span className="text-xs font-medium text-green-700">Live</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-sm">{arrival.registrationNumber}</p>
                            <p className="text-xs text-slate-500">{arrival.routeName}</p>
                            {route && (
                              <Badge style={{ backgroundColor: route.color }} className="mt-2 text-white">
                                Route {route.number}
                              </Badge>
                            )}
                          </div>
                          <div className="text-right">
                            {arrival.etaMinutes !== null && arrival.etaMinutes < 2 ? (
                              <span className="text-green-600 font-bold text-sm">Arriving now</span>
                            ) : arrival.etaMinutes !== null ? (
                              <span className="font-bold text-sm">{arrival.etaMinutes} min</span>
                            ) : (
                              <span className="text-slate-400 text-sm">Stopped</span>
                            )}
                            {arrival.distanceToStopKm != null && (
                              <p className="text-xs text-slate-500">{arrival.distanceToStopKm.toFixed(1)} km away</p>
                            )}
                          </div>
                        </div>
                        <div className="mt-3 flex items-center justify-between border-t pt-3">
                          <span className="text-xs text-slate-500">
                            {route ? `~${route.duration} min trip` : 'Route timing unavailable'}
                          </span>
                          <Badge variant={arrival.status === 'active' ? 'default' : 'secondary'}>
                            {arrival.status === 'active' ? 'approaching' : arrival.status}
                          </Badge>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {selectedStop && arrivals.length === 0 && (
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="pt-6 text-center text-sm text-slate-500">
                No vehicles currently approaching this stop.
              </CardContent>
            </Card>
          )}

          {/* Quick Info / Service Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Service Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <Clock className="size-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="font-medium">Operating Hours</p>
                  <p className="text-xs text-slate-600">Monday - Sunday: 5:00 AM - 11:00 PM</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <MapPin className="size-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium">Service Contact</p>
                  <p className="text-xs text-slate-600">
                    {tenantContact ?? 'Contact your transport operator for service information.'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
