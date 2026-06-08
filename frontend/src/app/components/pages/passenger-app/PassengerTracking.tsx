import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import type { GlobalStopRead, ArrivalEstimate } from '../../../lib/api-types';
import { getPublicStops, getCrossTenantArrivals } from '../../../services/arrivals.service';
import { getMyProfile, updateMyProfile } from '../../../services/passenger.service';
import { useAuth } from '../../../lib/auth-context';
import { MapPin, Clock, Navigation, Heart, Search, Building2 } from 'lucide-react';

export function PassengerTracking() {
  const { user } = useAuth();
  const isPassenger = user?.role === 'passenger';
  const [preferredStopIds, setPreferredStopIds] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [allStops, setAllStops] = useState<GlobalStopRead[]>([]);
  const [selectedStop, setSelectedStop] = useState<string | null>(null);
  const [arrivals, setArrivals] = useState<ArrivalEstimate[]>([]);
  const [countdown, setCountdown] = useState(10);

  useEffect(() => {
    getPublicStops().then(setAllStops).catch(() => {});
  }, []);

  useEffect(() => {
    if (!isPassenger) return;
    getMyProfile()
      .then((p) => setPreferredStopIds(p.preferredStops.map((s) => s.id)))
      .catch(() => {});
  }, [isPassenger]);

  useEffect(() => {
    if (!selectedStop) { setArrivals([]); return; }
    const fetch = () =>
      getCrossTenantArrivals(selectedStop)
        .then((data) => {
          setArrivals([...data].sort((a, b) => (a.etaMinutes ?? 999) - (b.etaMinutes ?? 999)));
          setCountdown(10);
        })
        .catch(() => {});
    fetch();
    const id = setInterval(fetch, 10000);
    return () => clearInterval(id);
  }, [selectedStop]);

  useEffect(() => {
    if (!selectedStop) return;
    const tick = setInterval(() => setCountdown((c) => (c > 0 ? c - 1 : 0)), 1000);
    return () => clearInterval(tick);
  }, [selectedStop]);

  const filteredStops = allStops.filter((s) =>
    s.name.toLowerCase().includes(searchTerm.toLowerCase())
  );
  const favoriteStopsList = allStops.filter((s) => preferredStopIds.includes(s.id));
  const selectedStopData = allStops.find((s) => s.id === selectedStop);

  const toggleFavorite = async (id: string) => {
    const newIds = preferredStopIds.includes(id)
      ? preferredStopIds.filter((x) => x !== id)
      : [...preferredStopIds, id];
    setPreferredStopIds(newIds);
    try {
      await updateMyProfile({ preferredStops: newIds });
    } catch {
      setPreferredStopIds(preferredStopIds);
    }
  };

  const operatorSummary = arrivals.reduce<Record<string, Set<string>>>((acc, a) => {
    if (!acc[a.tenantName]) acc[a.tenantName] = new Set();
    acc[a.tenantName].add(a.routeNumber);
    return acc;
  }, {});

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
                {filteredStops.map((stop) => (
                  <div key={stop.id} onClick={() => setSelectedStop(stop.id)}
                    className={`cursor-pointer rounded-lg border p-3 transition-colors ${selectedStop === stop.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-slate-50'}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <MapPin className="size-4 text-slate-400" />
                        <p className="font-medium">{stop.name}</p>
                      </div>
                      {isPassenger && (
                        <button
                          onClick={(e) => { e.stopPropagation(); void toggleFavorite(stop.id); }}
                          className="ml-2 p-1"
                        >
                          <Heart className={`size-4 ${preferredStopIds.includes(stop.id) ? 'fill-red-500 text-red-500' : 'text-slate-300'}`} />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          {selectedStopData && arrivals.length > 0 && (
            <Card>
              <CardContent className="pt-4 pb-3">
                <p className="font-semibold text-sm mb-2">{selectedStopData.name}</p>
                {Object.entries(operatorSummary).map(([tenant, routes]) => (
                  <div key={tenant} className="flex items-start gap-2 mt-1.5">
                    <Building2 className="size-3.5 text-slate-400 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-slate-700">{tenant}</p>
                      <div className="flex flex-wrap gap-1 mt-0.5">
                        {[...routes].map((r) => (
                          <Badge key={r} variant="secondary" className="text-xs">Route {r}</Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {selectedStop && arrivals.length > 0 && (
            <Card className="border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Clock className="size-5 text-blue-600" />Next Arrivals at {selectedStopData?.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {arrivals.map((a) => (
                    <div key={a.vehicleId} className="rounded-lg bg-white p-4 shadow-sm">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-sm">{a.registrationNumber}</p>
                          <p className="text-xs text-slate-500">{a.routeName}</p>
                          <div className="flex items-center gap-1.5 mt-1.5">
                            <Badge variant="secondary" className="text-xs">Route {a.routeNumber}</Badge>
                            <span className="flex items-center gap-1 text-xs text-slate-400">
                              <Building2 className="size-3" />{a.tenantName}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          {a.etaMinutes !== null && a.etaMinutes < 2
                            ? <span className="text-green-600 font-bold text-sm">Arriving now</span>
                            : a.etaMinutes !== null
                            ? <span className="font-bold text-sm">{a.etaMinutes} min</span>
                            : <span className="text-slate-400 text-sm">Stopped</span>}
                          {a.distanceToStopKm != null && (
                            <p className="text-xs text-slate-500">{a.distanceToStopKm.toFixed(1)} km away</p>
                          )}
                        </div>
                      </div>
                      {a.seatingCapacity > 0 && (
                        <div className="mt-3 pt-3 border-t space-y-2">
                          <div className="flex items-center justify-between text-xs text-slate-500">
                            <span>{a.currentOccupancy} / {a.seatingCapacity} seats taken</span>
                            {a.remainingSeats === 0 ? (
                              <span className="font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
                                Bus is full
                              </span>
                            ) : a.remainingSeats < 10 ? (
                              <span className="font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
                                Nearly full ({a.remainingSeats} left)
                              </span>
                            ) : (
                              <span className="font-semibold text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
                                {a.remainingSeats} seats free
                              </span>
                            )}
                          </div>
                          <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                a.remainingSeats === 0 ? 'bg-red-500' : a.remainingSeats < 10 ? 'bg-amber-400' : 'bg-green-500'
                              }`}
                              style={{ width: `${Math.min(100, (a.currentOccupancy / a.seatingCapacity) * 100)}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {selectedStop && arrivals.length === 0 && (
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="pt-6 pb-5 text-center space-y-1">
                <p className="text-sm text-slate-600">No buses currently approaching this stop.</p>
                <p className="text-xs text-slate-400">
                  Auto-refreshes every 10 seconds · next refresh in{' '}
                  <span className="font-semibold text-blue-600">{countdown}s</span>
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
