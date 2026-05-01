import React from 'react';
import { GitBranch } from 'lucide-react';
import { Badge } from '../../../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';

export function CreateRouteVersionsTab(props: {
  stopCount: number;
  estimatedDistanceKm: number;
  estimatedDurationMin: number;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <GitBranch className="size-4" />
          Route version control
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <p className="font-medium">v1.0 (Draft)</p>
            <Badge variant="secondary">Current</Badge>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Current draft: {props.stopCount} stops, {props.estimatedDistanceKm} km, ~{props.estimatedDurationMin} min.
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <p className="font-medium">v0.9</p>
            <Badge variant="secondary">Archived</Badge>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Prototype baseline route definition and initial timetable profile.
          </p>
        </div>
        <p className="text-xs text-slate-500">
          In production: approvals, change logs, rollback, and audit trail for compliance.
        </p>
      </CardContent>
    </Card>
  );
}
