import { useEffect, useState } from 'react';
import { Bell, Heart, MapPin, Phone, Route, Save } from 'lucide-react';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { toast } from 'sonner';
import { ApiError } from '../../../lib/api-client';
import type { RouteRead } from '../../../lib/api-types';
import { listRoutes } from '../../../services/routes.service';
import * as passengerService from '../../../services/passenger.service';
import type { PassengerProfile } from '../../../services/passenger.service';

function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? 'bg-emerald-500' : 'bg-slate-300'
      }`}
      aria-label={label}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );
}

export function PassengerProfileSection() {
  const [profile, setProfile] = useState<PassengerProfile | null>(null);
  const [allRoutes, setAllRoutes] = useState<RouteRead[]>([]);
  const [phone, setPhone] = useState('');
  const [selectedRoutes, setSelectedRoutes] = useState<string[]>([]);
  const [selectedStops, setSelectedStops] = useState<string[]>([]);
  const [notifyArrival, setNotifyArrival] = useState(true);
  const [notifyDelay, setNotifyDelay] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    passengerService.getMyProfile().then((p) => {
      setProfile(p);
      setPhone(p.phone ?? '');
      setSelectedRoutes(p.preferredRoutes.map((r) => r.id));
      setSelectedStops(p.preferredStops.map((s) => s.id));
      setNotifyArrival(p.notifyOnArrival);
      setNotifyDelay(p.notifyOnDelay);
    }).catch(() => {});

    listRoutes({ isActive: true, pageSize: 100 }).then((r) => setAllRoutes(r.items)).catch(() => {});
  }, []);

  const allStops = allRoutes.flatMap((r) =>
    r.stops.map((s) => ({ ...s, routeName: r.name }))
  ).filter((s, i, arr) => arr.findIndex((x) => x.id === s.id) === i);

  const toggleRoute = (id: string) =>
    setSelectedRoutes((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const toggleStop = (id: string) =>
    setSelectedStops((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await passengerService.updateMyProfile({
        phone: phone.trim() || null,
        preferredRoutes: selectedRoutes,
        preferredStops: selectedStops,
        notifyOnArrival: notifyArrival,
        notifyOnDelay: notifyDelay,
      });
      setProfile(updated);
      toast.success('Profile saved');
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  if (!profile) {
    return <div className="text-center py-12 text-slate-500 text-sm">Loading profile…</div>;
  }

  return (
    <div className="space-y-4 max-w-xl">
      {/* Basic info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">My Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-xs text-slate-500 mb-1">Name</p>
            <p className="font-medium">{profile.fullName}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Email</p>
            <p className="font-medium">{profile.email}</p>
          </div>
          <div className="space-y-1">
            <Label htmlFor="phone" className="text-xs text-slate-500">Phone</Label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
              <Input
                id="phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+250 7xx xxx xxx"
                className="pl-10"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Favourite routes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Route className="size-4 text-blue-600" />
            Favourite Routes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {allRoutes.length === 0 ? (
            <p className="text-sm text-slate-500">No routes available</p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {allRoutes.map((r) => (
                <label key={r.id} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedRoutes.includes(r.id)}
                    onChange={() => toggleRoute(r.id)}
                    className="rounded"
                  />
                  <span
                    className="inline-block size-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: r.color }}
                  />
                  <span className="text-sm">{r.name} <span className="text-slate-400">#{r.number}</span></span>
                </label>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Favourite stops */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Heart className="size-4 text-red-500" />
            Favourite Stops
          </CardTitle>
        </CardHeader>
        <CardContent>
          {allStops.length === 0 ? (
            <p className="text-sm text-slate-500">No stops available</p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {allStops.map((s) => (
                <label key={s.id} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedStops.includes(s.id)}
                    onChange={() => toggleStop(s.id)}
                    className="rounded"
                  />
                  <MapPin className="size-3.5 text-slate-400 flex-shrink-0" />
                  <span className="text-sm">{s.name}</span>
                </label>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Bell className="size-4 text-amber-500" />
            Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm">Bus arriving at my stops</p>
            <Toggle checked={notifyArrival} onChange={setNotifyArrival} label="Arrival notifications" />
          </div>
          <div className="flex items-center justify-between">
            <p className="text-sm">Delays on my routes</p>
            <Toggle checked={notifyDelay} onChange={setNotifyDelay} label="Delay notifications" />
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSave} disabled={saving} className="w-full">
        <Save className="mr-2 size-4" />
        {saving ? 'Saving…' : 'Save Changes'}
      </Button>
    </div>
  );
}
