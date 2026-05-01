import React, { useMemo, useState } from 'react';
import { toast } from 'sonner';
import { Plus, Route as RouteIcon } from 'lucide-react';
import { Button } from '../../ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../../ui/dialog';
import { ScrollArea } from '../../ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { mockStops, mockVehicles } from '../../../lib/mock-data';
import { CreateRouteBasicsTab } from './create-route/CreateRouteBasicsTab.tsx';
import { CreateRouteMapTab } from './create-route/CreateRouteMapTab.tsx';
import { CreateRouteStopsTab, type RouteDraftStop } from './create-route/CreateRouteStopsTab.tsx';
import { CreateRouteScheduleTab } from './create-route/CreateRouteScheduleTab.tsx';
import { CreateRouteAssignmentTab } from './create-route/CreateRouteAssignmentTab.tsx';
import { CreateRouteVersionsTab } from './create-route/CreateRouteVersionsTab.tsx';

function buildInitialStops(): RouteDraftStop[] {
  return mockStops.slice(0, 5).map((s) => ({ id: s.id, name: s.name }));
}

export function CreateRouteModal() {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('basics');

  const [draftNumber, setDraftNumber] = useState('R-');
  const [draftName, setDraftName] = useState('New Kigali Corridor');
  const [draftDescription, setDraftDescription] = useState('Prototype route draft for planning and operational review.');
  const [draftStops, setDraftStops] = useState<RouteDraftStop[]>(buildInitialStops());
  const [assignedVehicleId, setAssignedVehicleId] = useState<string>('unassigned');

  const estimatedDistanceKm = useMemo(() => {
    const segments = Math.max(draftStops.length - 1, 0);
    return Number((segments * 2.4).toFixed(1));
  }, [draftStops.length]);

  const estimatedDurationMin = useMemo(() => {
    const segments = Math.max(draftStops.length - 1, 0);
    const dwell = draftStops.length * 2;
    return Math.max(10, Math.round(segments * 5 + dwell));
  }, [draftStops.length]);

  const handleSaveDraft = () => {
    toast.success('Route draft saved (prototype)');
    setOpen(false);
    setActiveTab('basics');
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 size-4" />
          Create New Route
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RouteIcon className="size-5" />
            Create New Route (Prototype)
          </DialogTitle>
          <DialogDescription>
            Build a route draft: define route details, draw the path, manage stops, set schedule, assign vehicles, and track versions.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full flex-wrap justify-start">
            <TabsTrigger value="basics">Basics</TabsTrigger>
            <TabsTrigger value="map">Map</TabsTrigger>
            <TabsTrigger value="stops">Stops</TabsTrigger>
            <TabsTrigger value="schedule">Schedule</TabsTrigger>
            <TabsTrigger value="assignment">Assignment</TabsTrigger>
            <TabsTrigger value="versions">Versions</TabsTrigger>
          </TabsList>

          <ScrollArea className="h-[60vh] pr-4">
            <TabsContent value="basics">
              <CreateRouteBasicsTab
                draftNumber={draftNumber}
                draftName={draftName}
                draftDescription={draftDescription}
                onDraftNumberChange={setDraftNumber}
                onDraftNameChange={setDraftName}
                onDraftDescriptionChange={setDraftDescription}
                estimatedDistanceKm={estimatedDistanceKm}
                estimatedDurationMin={estimatedDurationMin}
                stopCount={draftStops.length}
              />
            </TabsContent>

            <TabsContent value="map">
              <CreateRouteMapTab />
            </TabsContent>

            <TabsContent value="stops">
              <CreateRouteStopsTab draftStops={draftStops} onDraftStopsChange={setDraftStops} />
            </TabsContent>

            <TabsContent value="schedule">
              <CreateRouteScheduleTab />
            </TabsContent>

            <TabsContent value="assignment">
              <CreateRouteAssignmentTab
                vehicles={mockVehicles.slice(0, 12)}
                assignedVehicleId={assignedVehicleId}
                onAssignedVehicleIdChange={setAssignedVehicleId}
              />
            </TabsContent>

            <TabsContent value="versions">
              <CreateRouteVersionsTab
                stopCount={draftStops.length}
                estimatedDistanceKm={estimatedDistanceKm}
                estimatedDurationMin={estimatedDurationMin}
              />
            </TabsContent>
          </ScrollArea>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Close</Button>
          <Button onClick={handleSaveDraft}>Save Draft Route</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
