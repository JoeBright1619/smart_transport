import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import type { RouteRead, StopRead, ArrivalEstimate } from '../../../lib/api-types';
import { listRoutes } from '../../../services/routes.service';
import { getArrivals } from '../../../services/arrivals.service';
import { MapPin, Clock, Navigation, Heart, Search } from 'lucide-react';

export function PassengerTracking() {
  const [searchTerm, setSearchTerm] = useState('');
  const [routes, setRoutes] = useState<RouteRead[]>([]);
  const [allStops, setAllStops] = useState<StopRead[]>([]);
  const [selectedStop, setSelectedStop] = useState<string | null>(null);
  const [arrivals, setArrivals] = useState<ArrivalEstimate[]>([]);
  const [favoriteStops, setFavoriteStops] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem('passenger-favourite-stops');
      if (!stored) return [];
      const parsed = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === 'string') : [];
    } catch { return []; }
  });

  useEffect(() => {
    listRoutes({ isActive: true, pageSize: 100 }).then((res) => {
      setRoutes(res.items);
      const stopMap = new Map<string, StopRead>();
      res.items.forEach((route) => route.stops.forEach((s) => stopMap.set(s.id, s)));
      setAllStops(Array.from(stopMap.values()));
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedStop) { setArrivals([]); return; }
    const fetch = () =>
      getArrivals(selectedStop).then((data) =>
        setArrivals([...data].sort((a, b) => (a.etaMinutes ?? 999) - (b.etaMinutes ?? 999)))
      ).catch(() => {});
    fetch();
    const id = setInterval(fetch, 10000);
    return () => clearInterval(id);
  }, [selectedStop]);

  useEffect(() => {
    try { localStorage.setItem('passenger-favourite-stops', JSON.stringify(favoriteStops)); } catch {}
  }, [favoriteStops]);

  const filteredStops = allStops.filter((s) =>
    s.name.toLowerCase().includes(searchTerm.toLowerCase())
  );
  const favoriteStopsList = allStops.filter((s) => favoriteStops.includes(s.id));
  const selectedStopName = allStops.find((s) => s.id === selectedStop)?.name;

  const toggleFavorite = (id: string) =>
    setFavoriteStops((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  return (
    <div className="space-y-6">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-blue-300" />
        <Input
          placeholder="Search for bus stops..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 bg-white/10 border-white/20 text-black placeholder:text-blue-800"
        />
      </div>

      <div className="grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="space-y-6">
          {favoriteStopsList.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Heart className="size-5 text-red-500" /> Favorite Stops
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {favoriteStopsList.map((s) => (
                    <Button key={s.id} variant={selectedStop === s.id ? 'default' : 'outline'}
                      className="w-full justify-start" onClick={() => setSelectedStop(s.id)}>
                      <MapPin className="mr-2 size-4" />{s.name}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Navigation className="size-5 text-blue-600" />
                {searchTerm ? 'Search Results' : 'Nearby Stops'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {filteredStops.map((stop) => {
                  const routesAtStop = routes.filter((r) => r.stops.some((s) => s.id === stop.id));
                  return (
                    <div key={stop.id} onClick={() => setSelectedStop(stop.id)}
                      className={`cursor-pointer rounded-lg border p-3 transition-colors ${selectedStop === stop.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-slate-50'}`}>
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
                            {routesAtStop.map((r) => (
                              <Badge key={r.id} variant="secondary" className="text-xs">{r.number}</Badge>
                            ))}
                          </div>
                        </div>
                        <button onClick={(e) => { e.stopPropagation(); toggleFavorite(stop.id); }} className="ml-2 p-1">
                          <Heart className={`size-4 ${favoriteStops.includes(stop.id) ? 'fill-red-500 text-red-500' : 'text-slate-300'}`} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {selectedStop && arrivals.length > 0 && (
            <Card className="border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Clock className="size-5 text-blue-600" />Next Arrivals at {selectedStopName}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {arrivals.map((a) => {
                    const route = routes.find((r) => r.id === a.routeId);
                    return (
                      <div key={a.vehicleId} className="rounded-lg bg-white p-4 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-sm">{a.registrationNumber}</p>
                            <p className="text-xs text-slate-500">{a.routeName}</p>
                            {route && <Badge style={{ backgroundColor: route.color }} className="mt-2 text-white">Route {route.number}</Badge>}
                          </div>
                          <div className="text-right">
                            {a.etaMinutes !== null && a.etaMinutes < 2
                              ? <span className="text-green-600 font-bold text-sm">Arriving now</span>
                              : a.etaMinutes !== null
                              ? <span className="font-bold text-sm">{a.etaMinutes} min</span>
                              : <span className="text-slate-400 text-sm">Stopped</span>}
                            {a.distanceToStopKm != null && <p className="text-xs text-slate-500">{a.distanceToStopKm.toFixed(1)} km away</p>}
                          </div>
                        </div>
                        {a.seatingCapacity > 0 && (
                          <div className="mt-3 pt-3 border-t">
                            <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                              <span>{a.currentOccupancy} / {a.seatingCapacity} seats taken</span>
                              <span className={a.remainingSeats <= 5 ? 'text-orange-500 font-medium' : 'text-green-600'}>
                                {a.remainingSeats} free
                              </span>
                            </div>
                            <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${a.remainingSeats <= 5 ? 'bg-orange-400' : 'bg-green-500'}`}
                                style={{ width: `${Math.min(100, (a.currentOccupancy / a.seatingCapacity) * 100)}%` }}
                              />
                            </div>
                          </div>
                        )}
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
        </div>
      </div>
    </div>
  );
}
