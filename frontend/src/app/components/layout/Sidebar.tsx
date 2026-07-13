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
  Activity,
  PhoneCall,
  ListChecks,
} from 'lucide-react';
import { cn } from '../ui/utils';
import { useAuth } from '../../lib/auth-context';
import { Button } from '../ui/button';
import { useTranslation } from 'react-i18next';

const navigation = [
  {
    labelKey: 'nav.analyticsPlatform',
    href: '/superadmin/analytics',
    icon: Activity,
    roles: ['superadmin'],
  },
  {
    labelKey: 'nav.tenants',
    href: '/superadmin/tenants',
    icon: Building2,
    roles: ['superadmin'],
  },
  { labelKey: 'nav.dashboard', href: '/', icon: LayoutDashboard, roles: ['admin', 'operator', 'dispatcher'] },
  { labelKey: 'nav.tracking', href: '/tracking', icon: MapPin, roles: ['admin', 'operator', 'dispatcher'] },
  { labelKey: 'nav.fleet', href: '/fleet', icon: Bus, roles: ['admin', 'operator'] },
  { labelKey: 'nav.routes', href: '/routes', icon: Route, roles: ['admin', 'operator'] },
  { labelKey: 'nav.arrivals', href: '/arrivals', icon: Clock, roles: ['admin', 'operator', 'dispatcher'] },
  { labelKey: 'nav.passengerApp', href: '/passenger', icon: Smartphone, roles: ['admin', 'passenger'] },
  { labelKey: 'nav.operators', href: '/operators', icon: PhoneCall, roles: ['passenger'] },
  { labelKey: 'nav.dispatch', href: '/dispatch', icon: UserCog, roles: ['admin', 'dispatcher'] },
  { labelKey: 'nav.trips', href: '/trips', icon: ListChecks, roles: ['admin', 'operator', 'dispatcher'] },
  { labelKey: 'nav.drivers', href: '/drivers', icon: Users, roles: ['admin', 'operator'] },
  { labelKey: 'nav.maintenance', href: '/maintenance', icon: Wrench, roles: ['admin', 'operator'] },
  { labelKey: 'nav.analytics', href: '/analytics', icon: BarChart3, roles: ['admin', 'operator'] },
  { labelKey: 'nav.alerts', href: '/alerts', icon: Bell, roles: ['admin', 'operator', 'dispatcher'] },
  { labelKey: 'nav.administration', href: '/admin', icon: Settings, roles: ['admin'] },
  { labelKey: 'nav.security', href: '/security', icon: Shield, roles: ['admin'] },
];

export function Sidebar() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  const filteredNavigation = navigation.filter(item =>
    user && item.roles.includes(user.role)
  );
  const tenantLabel = user?.tenantName ?? 'Rwanda Transport';
  const roleLabel = user
    ? user.role.charAt(0).toUpperCase() + user.role.slice(1)
    : 'Fleet Management';

  return (
    <div className="flex h-screen w-64 flex-col bg-slate-900 text-white">
      <div className="flex h-16 items-center gap-2.5 border-b border-slate-800 px-4">
        {user?.tenantLogoPath ? (
          <img
            src={user.tenantLogoPath}
            alt=""
            className="size-7 shrink-0 rounded-md object-cover"
          />
        ) : (
          <Bus className="size-7 shrink-0 text-blue-400" />
        )}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold leading-tight">{tenantLabel}</p>
          <p className="text-xs text-slate-400">{roleLabel}</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto p-4 sidebar-scroll">
        <div className="space-y-1">
          {filteredNavigation.map((item) => {
            const isActive =
            location.pathname === item.href ||
            location.pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                )}
              >
                <item.icon className="size-5" />
                {t(item.labelKey)}
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
            {t('nav.logout')}
          </Button>
        </div>
      )}
    </div>
  );
}
