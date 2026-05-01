import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';
import { Label } from '../../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../ui/select';

type VehicleLite = { id: string; registrationNumber: string; status: string };

export function CreateRouteAssignmentTab(props: {
  vehicles: VehicleLite[];
  assignedVehicleId: string;
  onAssignedVehicleIdChange: (value: string) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Assign route to vehicles</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Assigned vehicle (prototype)</Label>
          <Select value={props.assignedVehicleId} onValueChange={props.onAssignedVehicleIdChange}>
            <SelectTrigger>
              <SelectValue placeholder="Select a vehicle" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="unassigned">Unassigned</SelectItem>
              {props.vehicles.map((v) => (
                <SelectItem key={v.id} value={v.id}>
                  {v.registrationNumber} ({v.status})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-slate-500">
            In production, assignment checks capacity, schedule conflicts, maintenance windows, and depot proximity.
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <p className="font-medium">Assignment rules (preview)</p>
          <ul className="mt-2 space-y-1 text-sm text-slate-600">
            <li>- Only active vehicles can be assigned</li>
            <li>- Conflict detection for overlapping schedules</li>
            <li>- Priority for vehicles with lowest delay history</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
