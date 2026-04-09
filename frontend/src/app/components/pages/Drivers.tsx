import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Avatar, AvatarFallback } from '../ui/avatar';
import { mockDrivers, mockVehicles } from '../../lib/mock-data';
import { Users, Star, Clock, Award } from 'lucide-react';

export function Drivers() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Driver Management</h1>
        <p className="text-slate-600">Manage driver profiles and performance</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Drivers</CardTitle>
            <Users className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockDrivers.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">On Trip</CardTitle>
            <Clock className="size-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockDrivers.filter(d => d.status === 'on-trip').length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Available</CardTitle>
            <Users className="size-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockDrivers.filter(d => d.status === 'available').length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Avg Rating</CardTitle>
            <Star className="size-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(mockDrivers.reduce((sum, d) => sum + d.rating, 0) / mockDrivers.length).toFixed(1)}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Driver Roster</CardTitle>
            <Button>Add Driver</Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Driver</TableHead>
                <TableHead>License</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Total Trips</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Vehicle</TableHead>
                <TableHead>Cert. Expiry</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockDrivers.map((driver) => {
                const vehicle = mockVehicles.find(v => v.id === driver.vehicleId);
                return (
                  <TableRow key={driver.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar>
                          <AvatarFallback>
                            {driver.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{driver.name}</p>
                          <p className="text-xs text-slate-500">{driver.phone}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">{driver.licenseNumber}</TableCell>
                    <TableCell>{driver.phone}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Star className="size-4 fill-yellow-400 text-yellow-400" />
                        <span className="font-medium">{driver.rating}</span>
                      </div>
                    </TableCell>
                    <TableCell>{driver.totalTrips}</TableCell>
                    <TableCell>
                      <Badge variant={
                        driver.status === 'on-trip' ? 'default' :
                        driver.status === 'available' ? 'secondary' : 'outline'
                      }>
                        {driver.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{vehicle?.registrationNumber || '-'}</TableCell>
                    <TableCell className="text-sm">
                      {new Date(driver.certificationExpiry).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
