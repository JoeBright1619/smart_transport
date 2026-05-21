import React, { useMemo } from 'react';
import { toast } from 'sonner';
import { Download, Upload, Wand2 } from 'lucide-react';
import type { RouteRead } from '../../../lib/api-types';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../ui/dialog';

function RouteTemplatesDialog({ routes }: { routes: RouteRead[] }) {
  const templates = useMemo(() => routes.slice(0, 8), [routes]);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Route templates</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Route library templates</DialogTitle>
          <DialogDescription>
            Use existing backend routes as templates for planning.
          </DialogDescription>
        </DialogHeader>
        {templates.length === 0 ? (
          <p className="text-sm text-slate-500">No route templates available.</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {templates.map((route) => (
              <div key={route.id} className="rounded-lg border p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge style={{ backgroundColor: route.color }} className="text-white">
                        {route.number}
                      </Badge>
                      <p className="font-medium">{route.name}</p>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {route.stops.length} stops - {route.distance} km - {route.duration} min
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toast.message('Template application is not wired yet')}
                  >
                    Use
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
        <DialogFooter>
          <Button variant="outline">Manage templates</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function RouteImportExportDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Import / Export</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Import / Export route data</DialogTitle>
          <DialogDescription>
            Prototype import/export actions. Formats typically include GeoJSON, CSV, and GTFS shapes.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border p-4">
            <p className="flex items-center gap-2 font-medium">
              <Upload className="size-4" />
              Import
            </p>
            <p className="mt-1 text-sm text-slate-600">Upload a route file or paste route definition.</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => toast.message('Upload file is not wired yet')}>
                Upload file
              </Button>
              <Button variant="ghost" onClick={() => toast.message('Paste data is not wired yet')}>
                Paste data
              </Button>
            </div>
          </div>
          <div className="rounded-lg border p-4">
            <p className="flex items-center gap-2 font-medium">
              <Download className="size-4" />
              Export
            </p>
            <p className="mt-1 text-sm text-slate-600">Share with planning tools or backup the route library.</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => toast.success('Exported GeoJSON preview')}>
                Export GeoJSON
              </Button>
              <Button variant="outline" onClick={() => toast.success('Exported CSV preview')}>
                Export CSV
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function RouteManagementTools({ routes }: { routes: RouteRead[] }) {
  const suggestions = [
    {
      title: 'Balance headways by demand',
      detail: 'Increase frequency during peak windows based on passenger demand trends.',
    },
    {
      title: 'Add recovery time at termini',
      detail: 'Introduce a short layover to stabilize on-time performance.',
    },
    {
      title: 'Reduce stop clustering',
      detail: 'Merge low-usage adjacent stops in dense corridors to reduce dwell time.',
    },
  ];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Route tools</CardTitle>
          <p className="text-sm text-slate-600">Templates, import/export, and optimization previews for planning.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <RouteTemplatesDialog routes={routes} />
          <RouteImportExportDialog />
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-600">Route performance analytics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm text-slate-600">
            <p>- Delay hotspots by segment</p>
            <p>- Dwell time per stop</p>
            <p>- Passenger demand overlays</p>
            <p>- Incident correlation</p>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm text-slate-600">
              <Wand2 className="size-4" />
              Optimization suggestions
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            {suggestions.map((suggestion) => (
              <div key={suggestion.title} className="rounded-lg border p-3">
                <p className="text-sm font-medium">{suggestion.title}</p>
                <p className="mt-1 text-xs text-slate-600">{suggestion.detail}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
}
