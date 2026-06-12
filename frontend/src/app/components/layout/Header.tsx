import { useState, useEffect, useCallback, useRef } from 'react';
import { Bell, MapPin, UserCircle } from 'lucide-react';
import { Link, useNavigate } from 'react-router';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { listAlerts, acknowledgeAlert } from '../../services/alerts.service';
import { getMyNotifications } from '../../services/passenger.service';
import type { AlertRead, AlertSeverity, PassengerNotification } from '../../lib/api-types';
import { useAuth } from '../../lib/auth-context';

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const SEVERITY_CLASS: Record<AlertSeverity, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-slate-100 text-slate-600',
};

const STAFF_ROLES = new Set(['admin', 'operator', 'dispatcher']);

export function Header() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isStaff = user?.role ? STAFF_ROLES.has(user.role) : false;
  const isPassenger = user?.role === 'passenger';

  const [currentTime, setCurrentTime] = useState(new Date());
  const [open, setOpen] = useState(false);

  // Staff alerts state
  const [alerts, setAlerts] = useState<AlertRead[]>([]);
  const [unacknowledgedCount, setUnacknowledgedCount] = useState(0);

  // Passenger notifications state + session-level "seen" tracking (vehicleId:stopName)
  const [passengerNotifs, setPassengerNotifs] = useState<PassengerNotification[]>([]);
  const seenRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Staff: poll tenant alerts
  const fetchAlerts = useCallback(() => {
    if (!isStaff) return;
    listAlerts({ isAcknowledged: false, pageSize: 5 })
      .then(res => { setAlerts(res.items); setUnacknowledgedCount(res.total); })
      .catch(() => {});
  }, [isStaff]);

  useEffect(() => {
    fetchAlerts();
    const id = setInterval(fetchAlerts, 30_000);
    return () => clearInterval(id);
  }, [fetchAlerts]);

  // Passenger: poll favourite-stop notifications, filtering out already-seen bus+stop pairs
  const fetchPassengerNotifs = useCallback(() => {
    if (!isPassenger) return;
    getMyNotifications().then((raw) => {
      // Build the set of keys currently returned by the API
      const currentKeys = new Set(
        raw.flatMap((n) => n.arrivals.map((a) => `${n.stopName}:${a.vehicleId}`))
      );
      // Evict keys that are no longer approaching (bus arrived / left)
      seenRef.current.forEach((k) => { if (!currentKeys.has(k)) seenRef.current.delete(k); });
      // Strip seen buses from the result
      const filtered = raw
        .map((n) => ({
          ...n,
          arrivals: n.arrivals.filter((a) => !seenRef.current.has(`${n.stopName}:${a.vehicleId}`)),
        }))
        .filter((n) => n.arrivals.length > 0);
      setPassengerNotifs(filtered);
    }).catch(() => {});
  }, [isPassenger]);

  const clearPassengerNotifs = () => {
    passengerNotifs.forEach((n) =>
      n.arrivals.forEach((a) => seenRef.current.add(`${n.stopName}:${a.vehicleId}`))
    );
    setPassengerNotifs([]);
  };

  useEffect(() => {
    fetchPassengerNotifs();
    const id = setInterval(fetchPassengerNotifs, 30_000);
    return () => clearInterval(id);
  }, [fetchPassengerNotifs]);

  function handleAcknowledge(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    acknowledgeAlert(id).then(fetchAlerts).catch(() => {});
  }

  const badgeCount = isPassenger ? passengerNotifs.length : unacknowledgedCount;
  const viewAllPath = isPassenger ? '/passenger-notifications' : '/alerts';

  return (
    <header className="flex h-16 items-center justify-end border-b bg-white px-6 gap-4">
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="size-5" />
            {badgeCount > 0 && (
              <Badge className="absolute -right-1 -top-1 size-5 p-0 flex items-center justify-center text-xs">
                {badgeCount > 99 ? '99+' : badgeCount}
              </Badge>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-80">
          <DropdownMenuLabel className="flex items-center justify-between">
            <span>Notifications</span>
            {badgeCount > 0 && (
              <span className="text-xs font-normal text-slate-500">{badgeCount} active</span>
            )}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />

          {isPassenger ? (
            passengerNotifs.length === 0 ? (
              <div className="px-3 py-4 text-sm text-slate-500 text-center">
                No buses approaching your favourite stops
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between px-3 py-1.5">
                  <span className="text-xs text-slate-400">{passengerNotifs.length} stop{passengerNotifs.length !== 1 ? 's' : ''} with approaching buses</span>
                  <button
                    onClick={clearPassengerNotifs}
                    className="text-xs text-slate-500 hover:text-slate-700 underline"
                  >
                    Clear all
                  </button>
                </div>
                {passengerNotifs.slice(0, 5).map((n) => {
                  const first = n.arrivals[0];
                  return (
                    <DropdownMenuItem
                      key={n.stopName}
                      className="flex flex-col items-start gap-0.5 px-3 py-2.5 cursor-pointer"
                      onClick={() => { navigate('/passenger-notifications'); setOpen(false); }}
                    >
                      <div className="flex items-center gap-1.5 w-full">
                        <MapPin className="size-3.5 text-slate-400 shrink-0" />
                        <span className="font-medium text-sm leading-tight line-clamp-1">{n.stopName}</span>
                      </div>
                      {first && (
                        <div className="flex w-full items-center justify-between text-xs text-slate-500 pl-5">
                          <span className="line-clamp-1">{first.registrationNumber} · {first.routeName}</span>
                          <span className="shrink-0 ml-2 font-semibold text-blue-600">
                            {first.etaMinutes != null && first.etaMinutes < 2
                              ? 'Now'
                              : first.etaMinutes != null
                              ? `${first.etaMinutes} min`
                              : 'Stopped'}
                          </span>
                        </div>
                      )}
                    </DropdownMenuItem>
                  );
                })}
              </>
            )
          ) : isStaff ? (
            alerts.length === 0 ? (
              <div className="px-3 py-4 text-sm text-slate-500 text-center">No new alerts</div>
            ) : (
              alerts.map(alert => (
                <DropdownMenuItem
                  key={alert.id}
                  className="flex flex-col items-start gap-1 px-3 py-2.5 cursor-pointer"
                  onClick={() => { navigate('/alerts'); setOpen(false); }}
                >
                  <div className="flex w-full items-center justify-between gap-2">
                    <span className="font-medium text-sm leading-tight line-clamp-1">{alert.title}</span>
                    <span className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${SEVERITY_CLASS[alert.severity]}`}>
                      {alert.severity}
                    </span>
                  </div>
                  <div className="flex w-full items-center justify-between text-xs text-slate-400">
                    <span className="line-clamp-1">{alert.message}</span>
                    <button
                      className="shrink-0 ml-2 hover:text-slate-600 underline"
                      onClick={(e) => handleAcknowledge(alert.id, e)}
                    >
                      Dismiss
                    </button>
                  </div>
                  <span className="text-xs text-slate-300">{relativeTime(alert.createdAt)}</span>
                </DropdownMenuItem>
              ))
            )
          ) : (
            <div className="px-3 py-4 text-sm text-slate-500 text-center">No notifications</div>
          )}

          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="justify-center text-sm text-blue-600 font-medium cursor-pointer"
            onClick={() => { navigate(viewAllPath); setOpen(false); }}
          >
            View all alerts
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Link to="/profile">
        <Button variant="ghost" size="icon" title="My Profile">
          <UserCircle className="size-5" />
        </Button>
      </Link>

      <div className="text-sm text-right">
        <p className="font-medium">
          {currentTime.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
        <p className="text-slate-500">{currentTime.toLocaleTimeString()}</p>
      </div>
    </header>
  );
}
