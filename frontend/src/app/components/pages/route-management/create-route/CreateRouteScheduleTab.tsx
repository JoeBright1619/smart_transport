import React from 'react';
import { Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';
import { Input } from '../../../ui/input';
import { Label } from '../../../ui/label';

export function CreateRouteScheduleTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Route schedule configuration</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Start time</Label>
          <Input value="05:00" readOnly />
        </div>
        <div className="space-y-2">
          <Label>End time</Label>
          <Input value="23:00" readOnly />
        </div>
        <div className="space-y-2">
          <Label>Peak headway</Label>
          <Input value="10 min" readOnly />
        </div>
        <div className="md:col-span-3 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
          <p className="font-medium flex items-center gap-2">
            <Clock className="size-4" />
            Prototype schedule editor
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Define weekday/weekend profiles, frequency bands, dispatch blocks, and operator shift constraints.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

