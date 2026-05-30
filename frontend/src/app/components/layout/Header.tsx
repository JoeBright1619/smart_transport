import { useState, useEffect, useCallback } from 'react';
import { Bell } from 'lucide-react';
import { useNavigate } from 'react-router';
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
import type { AlertRead, AlertSeverity } from '../../lib/api-types';

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

export function Header() {
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [alerts, setAlerts] = useState<AlertRead[]>([]);
  const [unacknowledgedCount, setUnacknowledgedCount] = useState(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchAlerts = useCallback(() => {
    listAlerts({ isAcknowledged: false, pageSize: 5 })
      .then(res => {
        setAlerts(res.items);
        setUnacknowledgedCount(res.total);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30_000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  function handleAcknowledge(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    acknowledgeAlert(id).then(fetchAlerts).catch(() => {});
  }

  return (
    <header className="flex h-16 items-center justify-end border-b bg-white px-6 gap-4">
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="size-5" />
            {unacknowledgedCount > 0 && (
              <Badge className="absolute -right-1 -top-1 size-5 p-0 flex items-center justify-center text-xs">
                {unacknowledgedCount > 99 ? '99+' : unacknowledgedCount}
              </Badge>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-80">
          <DropdownMenuLabel className="flex items-center justify-between">
            <span>Notifications</span>
            {unacknowledgedCount > 0 && (
              <span className="text-xs font-normal text-slate-500">{unacknowledgedCount} unread</span>
            )}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          {alerts.length === 0 ? (
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
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="justify-center text-sm text-blue-600 font-medium cursor-pointer"
            onClick={() => { navigate('/alerts'); setOpen(false); }}
          >
            View all alerts
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <div className="text-sm text-right">
        <p className="font-medium">
          {currentTime.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
        <p className="text-slate-500">{currentTime.toLocaleTimeString()}</p>
      </div>
    </header>
  );
}
