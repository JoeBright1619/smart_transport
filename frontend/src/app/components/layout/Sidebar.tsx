import { Link, useLocation } from 'react-router';
import {
  LayoutDashboard,
  MapPin,
  Route,
  Bus,
  Users,
  Wrench,
  BarChart3,
  Bell,
  Settings,
  Clock,
  Smartphone,
  UserCog,
  Shield,
  LogOut,
  Building2,
} from 'lucide-react';
import { cn } from '../ui/utils';
import { useAuth } from '../../lib/auth-context';
import { Button } from '../ui/button';
import React from 'react';

const navigation = [
  {
    name: 'Platform Admin',
    href: '/superadmin',
    icon: Building2,
    roles: ['superadmin'],
  },
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, roles: ['admin', 'operator', 'dispatcher'] },
  { name: 'Vehicle Tracking', href: '/tracking', icon: MapPin, roles: ['admin', 'operator', 'dispatcher'] },
  { name: 'Fleet Management', href: '/fleet', icon: Bus, roles: ['admin', 'operator'] },
  { name: 'Route Management', href: '/routes', icon: Route, roles: ['admin', 'operator'] },
  { name: 'Arrival Times', href: '/arrivals', icon: Clock, roles: ['admin', 'operator', 'dispatcher'] },
  { name: 'Passenger App', href: '/passenger', icon: Smartphone, roles: ['admin', 'passenger'] },
  { name: 'Dispatch', href: '/dispatch', icon: UserCog, roles: ['admin', 'dispatcher'] },
  { name: 'Drivers', href: '/drivers', icon: Users, roles: ['admin', 'operator'] },
  { name: 'Maintenance', href: '/maintenance', icon: Wrench, roles: ['admin', 'operator'] },
  { name: 'Analytics', href: '/analytics', icon: BarChart3, roles: ['admin', 'operator'] },
  { name: 'Alerts', href: '/alerts', icon: Bell, roles: ['admin', 'operator', 'dispatcher'] },
  { name: 'Administration', href: '/admin', icon: Settings, roles: ['admin'] },
  { name: 'Security & Audit', href: '/security', icon: Shield, roles: ['admin'] },
];

export function Sidebar() {
  const location = useLocation();
  const { user, logout } = useAuth();

  const filteredNavigation = navigation.filter(item =>
    user && item.roles.includes(user.role)
  );
  const tenantLabel = user?.tenantName ?? 'Rwanda Transport';
  const roleLabel = user
    ? user.role.charAt(0).toUpperCase() + user.role.slice(1)
    : 'Fleet Management';

  return (
    <div className="flex h-screen w-64 flex-col bg-slate-900 text-white">
      <div className="flex h-16 items-center gap-2 border-b border-slate-800 px-6">
        <Bus className="size-8 text-blue-400" />
        <div>
          <h1 className="font-bold">{tenantLabel}</h1>
          <p className="text-xs text-slate-400">{roleLabel}</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto p-4 sidebar-scroll">
        <div className="space-y-1">
          {filteredNavigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                )}
              >
                <item.icon className="size-5" />
                {item.name}
              </Link>
            );
          })}
        </div>
      </nav>

      {user && (
        <div className="border-t border-slate-800 p-4">
          <div className="mb-3 rounded-lg bg-slate-800 p-3">
            <p className="text-sm font-medium">{user.fullName}</p>
            <p className="text-xs text-slate-400">{user.email}</p>
            <p className="mt-1 text-xs font-medium text-blue-400">
              {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={logout}
          >
            <LogOut className="mr-2 size-4" />
            Logout
          </Button>
        </div>
      )}
    </div>
  );
}
