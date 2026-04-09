import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { mockStops, mockRoutes, mockVehicles } from '../../lib/mock-data';
import { Clock, MapPin, Navigation } from 'lucide-react';

export function ArrivalTimes() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Arrival Time Estimation</h1>
        <p className="text-slate-600">Real-time ETA at all bus stops</p>
      </div>

      <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
        {mockStops.slice(0, 6).map(stop => {
          const routesAtStop = mockRoutes.filter(r => r.stops.some(s => s.id === stop.id));
          
          return (
            <Card key={stop.id}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <MapPin className="size-5 text-blue-600" />
                  {stop.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {routesAtStop.map(route => {
                  const vehicle = mockVehicles.find(v => v.routeId === route.id && v.status === 'active');
                  const eta = vehicle ? Math.floor(Math.random() * 15) + 3 : null;
                  
                  return (
                    <div key={route.id} className="flex items-center justify-between rounded-lg border p-3">
                      <div className="flex items-center gap-3">
                        <Badge style={{ backgroundColor: route.color }} className="text-white">
                          {route.number}
                        </Badge>
                        <div>
                          <p className="font-medium text-sm">{route.name}</p>
                          {vehicle && (
                            <p className="text-xs text-slate-500">{vehicle.registrationNumber}</p>
                          )}
                        </div>
                      </div>
                      {eta ? (
                        <div className="flex items-center gap-2">
                          <Clock className="size-4 text-blue-600" />
                          <div className="text-right">
                            <p className="text-lg font-bold text-blue-600">{eta}</p>
                            <p className="text-xs text-slate-500">minutes</p>
                          </div>
                        </div>
                      ) : (
                        <Badge variant="outline">No active vehicle</Badge>
                      )}
                    </div>
                  );
                })}
                {routesAtStop.length === 0 && (
                  <p className="text-sm text-slate-500 text-center py-4">No routes at this stop</p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
