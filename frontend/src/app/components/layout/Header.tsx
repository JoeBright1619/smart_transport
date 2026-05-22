import { useState, useEffect } from 'react';
import { Bell, Search, Cloud } from 'lucide-react';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { listAlerts } from '../../services/alerts.service';

export function Header() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [unacknowledgedCount, setUnacknowledgedCount] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    listAlerts({ isAcknowledged: false, pageSize: 100 })
      .then(res => setUnacknowledgedCount(res.total))
      .catch(() => {});
  }, []);

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <div className="flex flex-1 items-center gap-4">
        <div className="relative w-96">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Search vehicles, routes, drivers..."
            className="pl-10"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm">
          <Cloud className="size-4 text-blue-500" />
          <span className="text-slate-600">24°C, Partly Cloudy</span>
        </div>

        <Button variant="ghost" size="icon" className="relative">
          <Bell className="size-5" />
          {unacknowledgedCount > 0 && (
            <Badge className="absolute -right-1 -top-1 size-5 p-0 flex items-center justify-center text-xs">
              {unacknowledgedCount}
            </Badge>
          )}
        </Button>

        <div className="text-sm">
          <p className="font-medium">Friday, Feb 27, 2026</p>
          <p className="text-slate-500">{currentTime.toLocaleTimeString()}</p>
        </div>
      </div>
    </header>
  );
}
