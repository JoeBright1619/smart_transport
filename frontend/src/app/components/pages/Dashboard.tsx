import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Bus, Clock, AlertTriangle, CheckCircle, TrendingUp, Users } from 'lucide-react';
import { mockVehicles, mockTrips, mockAlerts, mockAnalytics } from '../../lib/mock-data';
import { Link } from 'react-router';

export function Dashboard() {
  const activeVehicles = mockVehicles.filter(v => v.status === 'active').length;
  const totalVehicles = mockVehicles.length;
  const activeTrips = mockTrips.filter(t => t.status === 'active').length;
  const delayedTrips = mockTrips.filter(t => t.delay > 0).length;
  const criticalAlerts = mockAlerts.filter(a => a.severity === 'critical' && !a.acknowledged).length;

  const todayAnalytics = mockAnalytics[mockAnalytics.length - 1];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Fleet Dashboard</h1>
        <p className="text-slate-600">Real-time overview of your transport operations</p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Active Vehicles</CardTitle>
            <Bus className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeVehicles}/{totalVehicles}</div>
            <p className="text-xs text-slate-500">
              {Math.round((activeVehicles / totalVehicles) * 100)}% fleet utilization
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Active Trips</CardTitle>
            <Clock className="size-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeTrips}</div>
            <p className="text-xs text-slate-500">
              {delayedTrips} trips delayed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">On-Time Performance</CardTitle>
            <CheckCircle className="size-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{todayAnalytics.onTimePercentage}%</div>
            <p className="text-xs text-slate-500">
              Avg delay: {todayAnalytics.avgDelay} min
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Today's Passengers</CardTitle>
            <Users className="size-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{todayAnalytics.totalPassengers.toLocaleString()}</div>
            <p className="text-xs text-slate-500">
              {todayAnalytics.totalTrips} trips completed
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Alerts</CardTitle>
              <Link to="/alerts">
                <Button variant="ghost" size="sm">View All</Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockAlerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="flex items-start gap-3 rounded-lg border p-3">
                  <AlertTriangle className={`size-5 ${
                    alert.severity === 'critical' ? 'text-red-500' :
                    alert.severity === 'high' ? 'text-orange-500' :
                    alert.severity === 'medium' ? 'text-yellow-500' :
                    'text-blue-500'
                  }`} />
                  <div className="flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium text-sm">{alert.title}</p>
                      <Badge variant={alert.acknowledged ? 'secondary' : 'default'} className="text-xs">
                        {alert.severity}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-600 mt-1">{alert.message}</p>
                    <p className="text-xs text-slate-400 mt-1">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Fleet Status */}
        <Card>
          <CardHeader>
            <CardTitle>Fleet Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockVehicles.slice(0, 6).map((vehicle) => (
                <div key={vehicle.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div className="flex items-center gap-3">
                    <div className={`size-2 rounded-full ${
                      vehicle.status === 'active' ? 'bg-green-500' :
                      vehicle.status === 'idle' ? 'bg-yellow-500' :
                      vehicle.status === 'maintenance' ? 'bg-red-500' :
                      'bg-slate-400'
                    }`} />
                    <div>
                      <p className="font-medium text-sm">{vehicle.registrationNumber}</p>
                      <p className="text-xs text-slate-500">{vehicle.model}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge variant={vehicle.status === 'active' ? 'default' : 'secondary'}>
                      {vehicle.status}
                    </Badge>
                    {vehicle.status === 'active' && (
                      <p className="text-xs text-slate-500 mt-1">{vehicle.speed} km/h</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <Link to="/fleet">
              <Button variant="outline" className="mt-4 w-full">View Full Fleet</Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Link to="/tracking">
              <Button variant="outline" className="w-full justify-start">
                <Bus className="mr-2 size-4" />
                Track Vehicles
              </Button>
            </Link>
            <Link to="/dispatch">
              <Button variant="outline" className="w-full justify-start">
                <Clock className="mr-2 size-4" />
                Dispatch Control
              </Button>
            </Link>
            <Link to="/analytics">
              <Button variant="outline" className="w-full justify-start">
                <TrendingUp className="mr-2 size-4" />
                View Analytics
              </Button>
            </Link>
            <Link to="/maintenance">
              <Button variant="outline" className="w-full justify-start">
                <AlertTriangle className="mr-2 size-4" />
                Maintenance Log
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
