import React, { useMemo } from 'react';
import { toast } from 'sonner';
import { Download, Upload, Wand2 } from 'lucide-react';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../../ui/dialog';
import { mockRoutes } from '../../../lib/mock-data';

function RouteTemplatesDialog() {
  const templates = useMemo(() => mockRoutes.slice(0, 8), []);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Route templates</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Route library templates</DialogTitle>
          <DialogDescription>
            Prototype library to speed up planning. In production you can save, tag, and share templates by depot or operator.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-3 md:grid-cols-2">
          {templates.map((r) => (
            <div key={r.id} className="rounded-lg border p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Badge style={{ backgroundColor: r.color }} className="text-white">{r.number}</Badge>
                    <p className="font-medium">{r.name}</p>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    {r.stops.length} stops • {r.distance} km • {r.duration} min
                  </p>
                </div>
                <Button size="sm" variant="outline" onClick={() => toast.message('Apply template to new draft (prototype)')}>
                  Use
                </Button>
              </div>
            </div>
          ))}
        </div>
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
            <p className="font-medium flex items-center gap-2">
              <Upload className="size-4" />
              Import
            </p>
            <p className="text-sm text-slate-600 mt-1">Upload a route file or paste route definition.</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => toast.message('Upload file (prototype)')}>Upload file</Button>
              <Button variant="ghost" onClick={() => toast.message('Paste data (prototype)')}>Paste data</Button>
            </div>
          </div>
          <div className="rounded-lg border p-4">
            <p className="font-medium flex items-center gap-2">
              <Download className="size-4" />
              Export
            </p>
            <p className="text-sm text-slate-600 mt-1">Share with planning tools or backup the route library.</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => toast.success('Exported GeoJSON (prototype)')}>Export GeoJSON</Button>
              <Button variant="outline" onClick={() => toast.success('Exported CSV (prototype)')}>Export CSV</Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function RouteManagementTools() {
  const suggestions = [
    {
      title: 'Balance headways by demand',
      detail: 'Increase frequency during 6–9 AM and 4–7 PM based on passenger demand trends.',
    },
    {
      title: 'Add recovery time at termini',
      detail: 'Introduce a short layover to stabilize on-time performance and support driver changeovers.',
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
          <RouteTemplatesDialog />
          <RouteImportExportDialog />
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-600">Route performance analytics</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-600 space-y-1">
            <p>- Delay hotspots by segment</p>
            <p>- Dwell time per stop</p>
            <p>- Passenger demand overlays</p>
            <p>- Incident correlation</p>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-600 flex items-center gap-2">
              <Wand2 className="size-4" />
              Optimization suggestions
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            {suggestions.map((s) => (
              <div key={s.title} className="rounded-lg border p-3">
                <p className="font-medium text-sm">{s.title}</p>
                <p className="text-xs text-slate-600 mt-1">{s.detail}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
}

