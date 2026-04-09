import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { mockRoutes } from '../../lib/mock-data';
import { Route as RouteIcon, MapPin, Clock, Edit, Trash2 } from 'lucide-react';
import { CreateRouteModal } from './route-management/CreateRouteModal.tsx';
import { RouteManagementTools } from './route-management/RouteManagementTools.tsx';

export function RouteManagement() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Route Management</h1>
          <p className="text-slate-600">Manage bus routes and stops</p>
        </div>
        <CreateRouteModal />
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Routes</CardTitle>
            <RouteIcon className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockRoutes.length}</div>
            <p className="text-xs text-slate-500">Active routes</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Distance</CardTitle>
            <MapPin className="size-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockRoutes.reduce((sum, r) => sum + r.distance, 0).toFixed(1)} km
            </div>
            <p className="text-xs text-slate-500">Combined length</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Avg Duration</CardTitle>
            <Clock className="size-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(mockRoutes.reduce((sum, r) => sum + r.duration, 0) / mockRoutes.length)} min
            </div>
            <p className="text-xs text-slate-500">Average route time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Stops</CardTitle>
            <MapPin className="size-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockRoutes.reduce((sum, r) => sum + r.stops.length, 0)}
            </div>
            <p className="text-xs text-slate-500">Across all routes</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Routes</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Route Number</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Stops</TableHead>
                <TableHead>Distance</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockRoutes.map((route) => (
                <TableRow key={route.id}>
                  <TableCell>
                    <Badge style={{ backgroundColor: route.color }} className="text-white">
                      {route.number}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-medium">{route.name}</TableCell>
                  <TableCell>{route.stops.length} stops</TableCell>
                  <TableCell>{route.distance} km</TableCell>
                  <TableCell>{route.duration} min</TableCell>
                  <TableCell>
                    <Badge variant={route.active ? 'default' : 'secondary'}>
                      {route.active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon">
                        <Edit className="size-4" />
                      </Button>
                      <Button variant="ghost" size="icon">
                        <Trash2 className="size-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <RouteManagementTools />

      <div className="grid gap-4 md:grid-cols-2">
        {mockRoutes.map((route) => (
          <Card key={route.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge style={{ backgroundColor: route.color }} className="text-white">
                    {route.number}
                  </Badge>
                  <CardTitle className="text-base">{route.name}</CardTitle>
                </div>
                <Button variant="outline" size="sm">Edit</Button>
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
                  <p className="text-xs font-medium text-slate-600 mb-2">Route Stops:</p>
                  <div className="space-y-1">
                    {route.stops.map((stop, index) => (
                      <div key={stop.id} className="flex items-center gap-2 text-sm">
                        <span className="flex size-5 items-center justify-center rounded-full bg-slate-100 text-xs">
                          {index + 1}
                        </span>
                        <span>{stop.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
