import type { RouteRead } from '../../../lib/api-types';
import { Badge } from '../../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { EditRouteModal } from './EditRouteModal';
import type { RouteUpdate } from '../../../lib/api-types';

type RouteCardsGridProps = {
  routes: RouteRead[];
  updatingRouteId: string | null;
  onUpdateRoute: (routeId: string, patch: RouteUpdate) => Promise<void>;
};

export function RouteCardsGrid({ routes, updatingRouteId, onUpdateRoute }: RouteCardsGridProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {routes.map((route) => (
        <Card key={route.id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge style={{ backgroundColor: route.color }} className="text-white">
                  {route.number}
                </Badge>
                <CardTitle className="text-base">{route.name}</CardTitle>
              </div>
              <div className="flex gap-2">
                <Badge variant={route.isActive ? 'default' : 'secondary'}>
                  {route.isActive ? 'Active' : 'Inactive'}
                </Badge>
                <EditRouteModal
                  route={route}
                  onUpdateRoute={onUpdateRoute}
                  disabled={updatingRouteId === route.id}
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Distance:</span>
                <span className="font-medium">{route.distance} km</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Est. Duration:</span>
                <span className="font-medium">{route.duration} minutes</span>
              </div>
              <div className="border-t pt-3">
                <p className="mb-2 text-xs font-medium text-slate-600">Route Stops:</p>
                <div className="space-y-1">
                  {route.stops.map((stop, index) => (
                    <div key={stop.id} className="flex items-center gap-2 text-sm">
                      <span className="flex size-5 items-center justify-center rounded-full bg-slate-100 text-xs">
                        {index + 1}
                      </span>
                      <span>{stop.name}</span>
                      <span className="text-xs text-slate-400">
                        {stop.lat.toFixed(4)}, {stop.lng.toFixed(4)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
