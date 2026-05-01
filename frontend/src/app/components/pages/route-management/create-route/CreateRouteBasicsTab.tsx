import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';
import { Input } from '../../../ui/input';
import { Label } from '../../../ui/label';
import { Textarea } from '../../../ui/textarea';

export function CreateRouteBasicsTab(props: {
  draftNumber: string;
  draftName: string;
  draftDescription: string;
  onDraftNumberChange: (value: string) => void;
  onDraftNameChange: (value: string) => void;
  onDraftDescriptionChange: (value: string) => void;
  stopCount: number;
  estimatedDistanceKm: number;
  estimatedDurationMin: number;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-base">Route details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="routeNumber">Route number</Label>
              <Input
                id="routeNumber"
                value={props.draftNumber}
                onChange={(e) => props.onDraftNumberChange(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="routeName">Route name</Label>
              <Input
                id="routeName"
                value={props.draftName}
                onChange={(e) => props.onDraftNameChange(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="routeDescription">Description</Label>
            <Textarea
              id="routeDescription"
              value={props.draftDescription}
              onChange={(e) => props.onDraftDescriptionChange(e.target.value)}
              rows={4}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Calculated estimates</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600">Stops</span>
            <span className="font-medium">{props.stopCount}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600">Estimated distance</span>
            <span className="font-medium">{props.estimatedDistanceKm} km</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600">Estimated duration</span>
            <span className="font-medium">{props.estimatedDurationMin} min</span>
          </div>
          <p className="text-xs text-slate-500">
            Prototype calculation based on stop count. In production this is computed from GIS, traffic, and dwell times.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
