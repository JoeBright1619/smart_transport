import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { mockTrips, mockVehicles, mockDrivers, mockRoutes } from '../../lib/mock-data';
import { UserCog, Clock, CheckCircle, XCircle } from 'lucide-react';

export function Dispatch() {
  const activeTrips = mockTrips.filter(t => t.status === 'active');
  const scheduledTrips = mockTrips.filter(t => t.status === 'scheduled');
  const availableVehicles = mockVehicles.filter(v => v.status === 'idle');
  const availableDrivers = mockDrivers.filter(d => d.status === 'available');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dispatch Management</h1>
        <p className="text-slate-600">Centralized trip assignment and dispatch control</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Active Trips</CardTitle>
            <CheckCircle className="size-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeTrips.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Scheduled</CardTitle>
            <Clock className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scheduledTrips.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Available Vehicles</CardTitle>
            <UserCog className="size-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{availableVehicles.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Available Drivers</CardTitle>
            <UserCog className="size-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{availableDrivers.length}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Active Trips</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {activeTrips.map(trip => {
              const vehicle = mockVehicles.find(v => v.id === trip.vehicleId);
              const driver = mockDrivers.find(d => d.id === trip.driverId);
              const route = mockRoutes.find(r => r.id === trip.routeId);
              
              return (
                <div key={trip.id} className="rounded-lg border p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium">{route?.name}</p>
                      <p className="text-sm text-slate-600">{vehicle?.registrationNumber}</p>
                      <p className="text-xs text-slate-500">{driver?.name}</p>
                    </div>
                    <Badge>{trip.status}</Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm mt-3">
                    <div>
                      <p className="text-xs text-slate-500">Started</p>
                      <p>{new Date(trip.actualStart!).toLocaleTimeString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Passengers</p>
                      <p>{trip.passengers}</p>
                    </div>
                  </div>
                  {trip.delay > 0 && (
                    <Badge variant="destructive" className="mt-2">
                      Delayed by {trip.delay} min
                    </Badge>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Available Resources</CardTitle>
              <Button>Assign Trip</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium mb-2">Available Vehicles</p>
                <div className="space-y-2">
                  {availableVehicles.map(vehicle => (
                    <div key={vehicle.id} className="flex items-center justify-between rounded-lg border p-2">
                      <span className="text-sm">{vehicle.registrationNumber}</span>
                      <Badge variant="secondary">Idle</Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm font-medium mb-2">Available Drivers</p>
                <div className="space-y-2">
                  {availableDrivers.map(driver => (
                    <div key={driver.id} className="flex items-center justify-between rounded-lg border p-2">
                      <span className="text-sm">{driver.name}</span>
                      <Badge variant="secondary">Available</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
