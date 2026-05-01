import React from 'react';
import { Map } from 'lucide-react';
import { Badge } from '../../../ui/badge';
import { Button } from '../../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';

export function CreateRouteMapTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Map className="size-4" />
          Route map drawing
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="rounded-lg border border-dashed p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Map canvas (prototype)</p>
              <p className="text-sm text-slate-600">
                Draw the route polyline, snap to roads, and place stops along the corridor.
              </p>
            </div>
            <Badge variant="secondary">GIS Mock</Badge>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="rounded-lg bg-slate-50 p-3 text-sm">
              <p className="font-medium">Draw</p>
              <p className="text-xs text-slate-600">Polyline / freehand</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3 text-sm">
              <p className="font-medium">Snap</p>
              <p className="text-xs text-slate-600">Road network</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3 text-sm">
              <p className="font-medium">Measure</p>
              <p className="text-xs text-slate-600">Distance / ETA</p>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Drawing controls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start">Start drawing</Button>
              <Button variant="outline" className="w-full justify-start">Add waypoint</Button>
              <Button variant="outline" className="w-full justify-start">Snap to roads</Button>
              <Button variant="outline" className="w-full justify-start">Clear draft</Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Validation (preview)</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600">
              Checks for missing stops, disconnected segments, and overlap with restricted corridors.
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  );
}
