import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { MapPin, Plus, RefreshCw, Trash2 } from 'lucide-react';
import type { Dispatch, SetStateAction } from 'react';
import { MapContainer, Marker, Popup, TileLayer, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { GlobalStopRead } from '../../../lib/api-types';
import * as routesService from '../../../services/routes.service';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { type RouteFormState, type RouteFormStop } from './route-helpers';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const globalStopIcon = L.divIcon({
  className: '',
  html: '<div style="width:14px;height:14px;border-radius:9999px;background:#94a3b8;border:2px solid white;box-shadow:0 1px 4px rgb(15 23 42 / 0.35);"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

const routeStopIcon = L.divIcon({
  className: '',
  html: '<div style="width:22px;height:22px;border-radius:9999px;background:#2563eb;border:3px solid white;box-shadow:0 2px 8px rgb(37 99 235 / 0.45);"></div>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

const draftStopIcon = L.divIcon({
  className: '',
  html: '<div style="width:30px;height:30px;border-radius:9999px;background:#f97316;border:4px solid white;box-shadow:0 3px 10px rgb(249 115 22 / 0.5);position:relative;"><div style="position:absolute;inset:6px;border-radius:9999px;background:white;"></div></div>',
  iconSize: [30, 30],
  iconAnchor: [15, 15],
});

function MapEvents({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

type RouteStopsEditorProps = {
  stops: RouteFormStop[];
  setForm: Dispatch<SetStateAction<RouteFormState>>;
};

type NewStopForm = {
  name: string;
  lat: string;
  lng: string;
};

const createFormKey = () => globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;

function toRouteFormStop(stop: GlobalStopRead, order: number): RouteFormStop {
  return {
    key: createFormKey(),
    stopId: stop.id,
    name: stop.name,
    lat: stop.lat,
    lng: stop.lng,
    order,
  };
}

export function RouteStopsEditor({ stops, setForm }: RouteStopsEditorProps) {
  const { t } = useTranslation('routes');
  const [globalStops, setGlobalStops] = useState<GlobalStopRead[]>([]);
  const [loadingStops, setLoadingStops] = useState(true);
  const [stopError, setStopError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [creating, setCreating] = useState(false);
  const [newStop, setNewStop] = useState<NewStopForm>({ name: '', lat: '', lng: '' });

  const selectedStopIds = useMemo(() => new Set(stops.map((stop) => stop.stopId)), [stops]);

  const filteredStops = useMemo(() => {
    const term = search.trim().toLowerCase();
    return globalStops.filter((stop) => {
      const isSelected = selectedStopIds.has(stop.id);
      const matchesSearch = !term || stop.name.toLowerCase().includes(term);
      return !isSelected && matchesSearch;
    });
  }, [globalStops, search, selectedStopIds]);

  const loadStops = async () => {
    setLoadingStops(true);
    setStopError(null);

    try {
      setGlobalStops(await routesService.listStops());
    } catch (error) {
      setStopError(error instanceof Error ? error.message : t('unableLoadStops'));
    } finally {
      setLoadingStops(false);
    }
  };

  useEffect(() => {
    void loadStops();
  }, []);

  const addStopToRoute = (stop: GlobalStopRead) => {
    setForm((current) => {
      if (current.stops.some((item) => item.stopId === stop.id)) {
        return current;
      }

      return {
        ...current,
        stops: [...current.stops, toRouteFormStop(stop, current.stops.length + 1)],
      };
    });
  };

  const removeStop = (key: string) => {
    setForm((current) => ({
      ...current,
      stops: current.stops
        .filter((stop) => stop.key !== key)
        .map((stop, index) => ({ ...stop, order: index + 1 })),
    }));
  };

  const handleCreateStop = async () => {
    setCreating(true);
    setStopError(null);

    try {
      const created = await routesService.createStop({
        name: newStop.name.trim(),
        lat: Number(newStop.lat),
        lng: Number(newStop.lng),
      });

      setGlobalStops((current) => [...current, created].sort((a, b) => a.name.localeCompare(b.name)));
      addStopToRoute(created);
      setNewStop({ name: '', lat: '', lng: '' });
      setSearch('');
    } catch (error) {
      setStopError(error instanceof Error ? error.message : t('unableCreateStop'));
    } finally {
      setCreating(false);
    }
  };

  const handleMapClick = (lat: number, lng: number) => {
    setNewStop((current) => ({
      ...current,
      lat: lat.toFixed(6),
      lng: lng.toFixed(6),
    }));
  };

  const defaultCenter: [number, number] = [-1.9403, 30.0605];
  const mapAnchor = stops[0] ?? globalStops[0];
  const center: [number, number] = mapAnchor ? [mapAnchor.lat, mapAnchor.lng] : defaultCenter;

  const draftPosition =
    newStop.lat && newStop.lng
      ? ([Number(newStop.lat), Number(newStop.lng)] as [number, number])
      : null;

  return (
    <div className="grid gap-4 md:grid-cols-[minmax(280px,0.9fr)_minmax(360px,1.1fr)]">
      <div className="space-y-3 md:max-h-[calc(100vh-17rem)] md:overflow-y-auto md:pr-2">
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <Label>{t('routeStops')}</Label>
            <Button type="button" variant="outline" size="sm" onClick={loadStops} disabled={loadingStops}>
              <RefreshCw className="mr-2 size-3" />
              {t('refresh')}
            </Button>
          </div>

          <div className="max-h-44 space-y-2 overflow-y-auto rounded-md border p-2 md:max-h-[22vh]">
            {stops.length === 0 ? (
              <p className="px-2 py-6 text-center text-sm text-slate-500">{t('selectOrCreate')}</p>
            ) : (
              stops.map((stop, index) => (
                <div key={stop.key} className="flex items-center justify-between gap-3 rounded-md border bg-white p-2">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <div className="flex size-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-medium text-blue-700">
                        {index + 1}
                      </div>
                      <p className="truncate text-sm font-medium">{stop.name}</p>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {stop.lat.toFixed(6)}, {stop.lng.toFixed(6)}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-8 shrink-0"
                    onClick={() => removeStop(stop.key)}
                  >
                    <Trash2 className="size-4 text-red-500" />
                  </Button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="stopSearch">{t('addExistingStop')}</Label>
          <Input
            id="stopSearch"
            placeholder={t('searchStops')}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <div className="max-h-32 overflow-y-auto rounded-md border md:max-h-[18vh]">
            {loadingStops ? (
              <p className="p-3 text-sm text-slate-500">{t('loadingStops')}</p>
            ) : filteredStops.length === 0 ? (
              <p className="p-3 text-sm text-slate-500">{t('noAvailableStops')}</p>
            ) : (
              filteredStops.map((stop) => (
                <button
                  key={stop.id}
                  type="button"
                  className="flex w-full items-center justify-between gap-3 border-b px-3 py-2 text-left text-sm last:border-b-0 hover:bg-slate-50"
                  onClick={() => addStopToRoute(stop)}
                >
                  <span className="truncate">{stop.name}</span>
                  <Plus className="size-4 shrink-0 text-slate-500" />
                </button>
              ))
            )}
          </div>
        </div>

        <div className="space-y-3 rounded-md border p-3">
          <div className="flex items-center gap-2">
            <MapPin className="size-4 text-slate-500" />
            <Label>{t('createNewStop')}</Label>
          </div>
          <Input
            placeholder={t('stopName')}
            value={newStop.name}
            onChange={(event) => setNewStop((current) => ({ ...current, name: event.target.value }))}
          />
          <div className="grid grid-cols-2 gap-2">
            <Input
              type="number"
              step="0.000001"
              placeholder={t('latitude')}
              value={newStop.lat}
              onChange={(event) => setNewStop((current) => ({ ...current, lat: event.target.value }))}
            />
            <Input
              type="number"
              step="0.000001"
              placeholder={t('longitude')}
              value={newStop.lng}
              onChange={(event) => setNewStop((current) => ({ ...current, lng: event.target.value }))}
            />
          </div>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            disabled={creating || !newStop.name.trim() || !newStop.lat || !newStop.lng}
            onClick={handleCreateStop}
          >
            {creating ? t('creating') : t('createAndAddStop')}
          </Button>
          {draftPosition && (
            <p className="text-xs text-slate-500">
              {t('newStopMarker', { lat: draftPosition[0].toFixed(6), lng: draftPosition[1].toFixed(6) })}
            </p>
          )}
          {stopError && <p className="text-sm text-red-600">{stopError}</p>}
        </div>
      </div>

      <div className="flex flex-col space-y-3">
        <Label>{t('stopsMap')}</Label>
        <div className="h-[320px] overflow-hidden rounded-lg border md:h-[calc(100vh-17rem)] md:min-h-[360px] md:max-h-[620px]">
          <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapEvents onMapClick={handleMapClick} />
            {draftPosition && (
              <Marker position={draftPosition} icon={draftStopIcon}>
                <Popup>{t('newStopLocation')}</Popup>
              </Marker>
            )}
            {globalStops.map((stop) => {
              const selectedIndex = stops.findIndex((routeStop) => routeStop.stopId === stop.id);
              const selected = selectedIndex >= 0;

              return (
                <Marker
                  key={stop.id}
                  position={[stop.lat, stop.lng]}
                  icon={selected ? routeStopIcon : globalStopIcon}
                >
                  <Popup>
                    {selected ? `${selectedIndex + 1}. ` : ''}
                    {stop.name}
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
