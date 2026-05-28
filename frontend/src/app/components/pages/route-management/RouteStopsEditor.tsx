import { Trash2 } from 'lucide-react';
import type { Dispatch, SetStateAction } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { createEmptyStop, type RouteFormState, type RouteFormStop } from './route-helpers';

// Fix leaflet marker icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
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

export function RouteStopsEditor({ stops, setForm }: RouteStopsEditorProps) {
  const updateStop = (
    key: string,
    field: 'name' | 'lat' | 'lng',
    value: string,
  ) => {
    setForm((current) => ({
      ...current,
      stops: current.stops.map((stop) =>
        stop.key === key
          ? { ...stop, [field]: field === 'name' ? value : Number(value) }
          : stop,
      ),
    }));
  };

  const removeStop = (key: string) => {
    setForm((current) => ({
      ...current,
      stops: current.stops
        .filter((stop) => stop.key !== key)
        .map((stop, index) => ({ ...stop, order: index + 1 })),
    }));
  };

  const addStop = () => {
    setForm((current) => ({
      ...current,
      stops: [...current.stops, createEmptyStop(current.stops.length + 1)],
    }));
  };

  const handleMapClick = (lat: number, lng: number) => {
    setForm((current) => {
      const newStop = createEmptyStop(current.stops.length + 1);
      newStop.lat = Number(lat.toFixed(6));
      newStop.lng = Number(lng.toFixed(6));
      newStop.name = `Stop ${current.stops.length + 1}`;
      return {
        ...current,
        stops: [...current.stops, newStop],
      };
    });
  };

  const handleMarkerDragEnd = (key: string, e: L.DragEndEvent) => {
    const marker = e.target;
    const position = marker.getLatLng();
    if (window.confirm("Are you sure you want to update this stop's location?")) {
      updateStop(key, 'lat', position.lat.toFixed(6));
      updateStop(key, 'lng', position.lng.toFixed(6));
    } else {
      // Re-render to snap marker back if cancelled
      setForm((current) => ({ ...current }));
    }
  };

  // Calculate map center based on existing stops or default to Kigali
  const defaultCenter: [number, number] = [-1.9403, 30.0605];
  const validStops = stops.filter(s => s.lat !== 0 && s.lng !== 0);
  const center = validStops.length > 0 ? [validStops[0].lat, validStops[0].lng] : defaultCenter;

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>Stops</Label>
          <Button type="button" variant="outline" size="sm" onClick={addStop}>
            Add stop
          </Button>
        </div>
        <div className="max-h-[400px] space-y-3 overflow-y-auto pr-2">
          {stops.map((stop, index) => (
            <div key={stop.key} className="grid gap-2 rounded-lg border p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="flex size-6 items-center justify-center rounded-full bg-slate-100 text-xs font-medium">
                    {index + 1}
                  </div>
                  <Label className="text-xs text-slate-500">Name</Label>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="size-6"
                  disabled={stops.length === 1}
                  onClick={() => removeStop(stop.key)}
                >
                  <Trash2 className="size-3 text-red-500" />
                </Button>
              </div>
              <Input
                placeholder="Stop name"
                value={stop.name}
                onChange={(event) => updateStop(stop.key, 'name', event.target.value)}
                required
              />
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label className="text-[10px] text-slate-500">Lat</Label>
                  <Input
                    type="number"
                    step="0.000001"
                    placeholder="Latitude"
                    value={stop.lat}
                    onChange={(event) => updateStop(stop.key, 'lat', event.target.value)}
                    required
                    className="h-8 text-xs"
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-slate-500">Lng</Label>
                  <Input
                    type="number"
                    step="0.000001"
                    placeholder="Longitude"
                    value={stop.lng}
                    onChange={(event) => updateStop(stop.key, 'lng', event.target.value)}
                    required
                    className="h-8 text-xs"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col space-y-3">
        <Label>Route Map (Click to add stop)</Label>
        <div className="flex-1 overflow-hidden rounded-lg border min-h-[400px]">
          <MapContainer center={center as [number, number]} zoom={13} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapEvents onMapClick={handleMapClick} />
            {stops.map((stop, index) => {
              if (stop.lat === 0 && stop.lng === 0) return null;
              return (
                <Marker
                  key={stop.key}
                  position={[stop.lat, stop.lng]}
                  draggable={true}
                  eventHandlers={{
                    dragend: (e) => handleMarkerDragEnd(stop.key, e),
                  }}
                >
                  <Popup>
                    {index + 1}. {stop.name || 'Unnamed Stop'}
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
