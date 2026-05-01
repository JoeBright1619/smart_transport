import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { mockVehicles, mockDrivers, mockTrips, mockRoutes } from '../../lib/mock-data';
import { Search, Bus, Users, Route as RouteIcon, BarChart, Edit, Eye } from 'lucide-react';

export function FleetManagement() {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredVehicles = mockVehicles.filter(v =>
    v.registrationNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.model.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const stats = {
    totalVehicles: mockVehicles.length,
    activeVehicles: mockVehicles.filter(v => v.status === 'active').length,
    idleVehicles: mockVehicles.filter(v => v.status === 'idle').length,
    maintenanceVehicles: mockVehicles.filter(v => v.status === 'maintenance').length,
    avgFuel: Math.round(mockVehicles.reduce((sum, v) => sum + v.fuel, 0) / mockVehicles.length),
    totalCapacity: mockVehicles.reduce((sum, v) => sum + v.capacity, 0),
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Fleet Management</h1>
        <p className="text-slate-600">Comprehensive fleet monitoring and control</p>
      </div>

      {/* Fleet Statistics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Vehicles</CardTitle>
            <Bus className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalVehicles}</div>
            <p className="text-xs text-slate-500">Total capacity: {stats.totalCapacity} passengers</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Active Vehicles</CardTitle>
            <div className="size-2 rounded-full bg-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.activeVehicles}</div>
            <p className="text-xs text-slate-500">{Math.round((stats.activeVehicles / stats.totalVehicles) * 100)}% of fleet</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Idle Vehicles</CardTitle>
            <div className="size-2 rounded-full bg-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.idleVehicles}</div>
            <p className="text-xs text-slate-500">Available for dispatch</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Maintenance</CardTitle>
            <div className="size-2 rounded-full bg-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.maintenanceVehicles}</div>
            <p className="text-xs text-slate-500">Under service</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="vehicles" className="space-y-4">
        <TabsList>
          <TabsTrigger value="vehicles">
            <Bus className="mr-2 size-4" />
            Vehicles
          </TabsTrigger>
          <TabsTrigger value="utilization">
            <BarChart className="mr-2 size-4" />
            Utilization
          </TabsTrigger>
        </TabsList>

        <TabsContent value="vehicles" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Vehicle Fleet</CardTitle>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      placeholder="Search vehicles..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-64 pl-10"
                    />
                  </div>
                  <Button>Add Vehicle</Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Registration</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Capacity</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Driver</TableHead>
                    <TableHead>Route</TableHead>
                    <TableHead>Fuel</TableHead>
                    <TableHead>Engine</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredVehicles.map((vehicle) => {
                    const driver = mockDrivers.find(d => d.id === vehicle.driverId);
                    const route = mockRoutes.find(r => r.id === vehicle.routeId);

                    return (
                      <TableRow key={vehicle.id}>
                        <TableCell className="font-medium">{vehicle.registrationNumber}</TableCell>
                        <TableCell>{vehicle.model}</TableCell>
                        <TableCell>{vehicle.capacity}</TableCell>
                        <TableCell>
                          <Badge variant={vehicle.status === 'active' ? 'default' : 'secondary'}>
                            {vehicle.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{driver?.name || '-'}</TableCell>
                        <TableCell>{route ? `${route.number}` : '-'}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-16 rounded-full bg-slate-200">
                              <div
                                className={`h-full rounded-full ${
                                  vehicle.fuel > 50 ? 'bg-green-500' :
                                  vehicle.fuel > 25 ? 'bg-yellow-500' : 'bg-red-500'
                                }`}
                                style={{ width: `${vehicle.fuel}%` }}
                              />
                            </div>
                            <span className="text-sm">{vehicle.fuel}%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={
                            vehicle.engineStatus === 'good' ? 'default' :
                            vehicle.engineStatus === 'warning' ? 'outline' : 'destructive'
                          }>
                            {vehicle.engineStatus}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Button variant="ghost" size="icon">
                              <Eye className="size-4" />
                            </Button>
                            <Button variant="ghost" size="icon">
                              <Edit className="size-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="utilization" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Fleet Utilization</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {mockVehicles.map((vehicle) => {
                  const trips = mockTrips.filter(t => t.vehicleId === vehicle.id);
                  const utilization = trips.length > 0 ? Math.min(100, trips.length * 15) : 0;

                  return (
                    <div key={vehicle.id}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">{vehicle.registrationNumber}</span>
                        <span className="text-sm text-slate-600">{utilization}%</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-200">
                        <div
                          className="h-full rounded-full bg-blue-600"
                          style={{ width: `${utilization}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Average Fuel Levels</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockVehicles.map((vehicle) => (
                    <div key={vehicle.id}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">{vehicle.registrationNumber}</span>
                        <span className="text-sm text-slate-600">{vehicle.fuel}%</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-200">
                        <div
                          className={`h-full rounded-full ${
                            vehicle.fuel > 50 ? 'bg-green-500' :
                            vehicle.fuel > 25 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${vehicle.fuel}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
