import { CheckCircle, XCircle } from 'lucide-react';
import type { DriverRead, RouteRead, TripRead, TripStatus, VehicleRead } from '../../../lib/api-types';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { formatTripTime, routeLabel } from './dispatch-helpers';

type TripsPanelProps = {
  title: string;
  trips: TripRead[];
  vehiclesById: Map<string, VehicleRead>;
  driversById: Map<string, DriverRead>;
  routesById: Map<string, RouteRead>;
  updatingTripId: string | null;
  onUpdateStatus: (tripId: string, status: TripStatus) => void;
};

export function TripsPanel({
  title,
  trips,
  vehiclesById,
  driversById,
  routesById,
  updatingTripId,
  onUpdateStatus,
}: TripsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {trips.length === 0 ? (
          <div className="rounded-lg border border-dashed p-4 text-sm text-slate-600">No {title.toLowerCase()}.</div>
        ) : (
          trips.map((trip) => (
            <TripCard
              key={trip.id}
              trip={trip}
              vehicle={vehiclesById.get(trip.vehicleId)}
              driver={driversById.get(trip.driverId)}
              route={routesById.get(trip.routeId)}
              disabled={updatingTripId === trip.id}
              onUpdateStatus={onUpdateStatus}
            />
          ))
        )}
      </CardContent>
    </Card>
  );
}

function TripCard({
  trip,
  vehicle,
  driver,
  route,
  disabled,
  onUpdateStatus,
}: {
  trip: TripRead;
  vehicle?: VehicleRead;
  driver?: DriverRead;
  route?: RouteRead;
  disabled: boolean;
  onUpdateStatus: (tripId: string, status: TripStatus) => void;
}) {
  const primaryTime = trip.status === 'active' ? trip.actualStart : trip.scheduledStart;

  return (
    <div className="rounded-lg border p-4">
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          <p className="font-medium">{routeLabel(route)}</p>
          <p className="text-sm text-slate-600">{vehicle?.registrationNumber ?? 'Unknown vehicle'}</p>
          <p className="text-xs text-slate-500">{driver?.name ?? 'Unknown driver'}</p>
        </div>
        <Badge>{trip.status}</Badge>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
        <div>
          <p className="text-xs text-slate-500">{trip.status === 'active' ? 'Started' : 'Scheduled'}</p>
          <p>{formatTripTime(primaryTime)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">End</p>
          <p>{formatTripTime(trip.scheduledEnd)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Passengers</p>
          <p>{trip.passengers}</p>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {trip.delay > 0 && <Badge variant="destructive">Delayed by {trip.delay} min</Badge>}
        {trip.status === 'scheduled' && (
          <Button size="sm" disabled={disabled} onClick={() => onUpdateStatus(trip.id, 'active')}>
            <CheckCircle className="mr-2 size-4" />
            Start Trip
          </Button>
        )}
        {trip.status === 'active' && (
          <Button size="sm" disabled={disabled} onClick={() => onUpdateStatus(trip.id, 'completed')}>
            <CheckCircle className="mr-2 size-4" />
            Complete
          </Button>
        )}
        {(trip.status === 'scheduled' || trip.status === 'active') && (
          <Button size="sm" variant="outline" disabled={disabled} onClick={() => onUpdateStatus(trip.id, 'cancelled')}>
            <XCircle className="mr-2 size-4" />
            Cancel
          </Button>
        )}
      </div>
    </div>
  );
}
