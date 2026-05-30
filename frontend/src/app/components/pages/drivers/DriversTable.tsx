import { Star, Trash2 } from 'lucide-react';
import type { DriverRead, DriverStatus, VehicleRead } from '../../../lib/api-types';
import { Avatar, AvatarFallback } from '../../ui/avatar';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { driverInitials, statusBadgeVariant, statusLabels } from './driver-helpers';

type DriversTableProps = {
  drivers: DriverRead[];
  vehiclesById: Map<string, VehicleRead>;
  updatingDriverId: string | null;
  onUpdateStatus: (driverId: string, status: DriverStatus) => void;
  onDeleteDriver: (driver: DriverRead) => void;
};

export function DriversTable({
  drivers,
  vehiclesById,
  updatingDriverId,
  onUpdateStatus,
  onDeleteDriver,
}: DriversTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Driver Roster</CardTitle>
      </CardHeader>
      <CardContent>
        {drivers.length === 0 ? (
          <div className="rounded-md border border-dashed p-8 text-center text-sm text-slate-600">
            No drivers found.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Driver</TableHead>
                <TableHead>License</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Total Trips</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Vehicle</TableHead>
                <TableHead>Cert. Expiry</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {drivers.map((driver) => (
                <DriverTableRow
                  key={driver.id}
                  driver={driver}
                  vehicle={driver.vehicleId ? vehiclesById.get(driver.vehicleId) : undefined}
                  disabled={updatingDriverId === driver.id}
                  onUpdateStatus={onUpdateStatus}
                  onDeleteDriver={onDeleteDriver}
                />
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function DriverTableRow({
  driver,
  vehicle,
  disabled,
  onUpdateStatus,
  onDeleteDriver,
}: {
  driver: DriverRead;
  vehicle?: VehicleRead;
  disabled: boolean;
  onUpdateStatus: (driverId: string, status: DriverStatus) => void;
  onDeleteDriver: (driver: DriverRead) => void;
}) {
  return (
    <TableRow>
      <TableCell>
        <div className="flex items-center gap-3">
          <Avatar>
            <AvatarFallback>{driverInitials(driver.name)}</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium">{driver.name}</p>
            <p className="text-xs text-slate-500">{driver.phone}</p>
          </div>
        </div>
      </TableCell>
      <TableCell className="font-mono text-sm">{driver.licenseNumber}</TableCell>
      <TableCell>{driver.phone}</TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          <Star className="size-4 fill-yellow-400 text-yellow-400" />
          <span className="font-medium">{driver.rating.toFixed(1)}</span>
        </div>
      </TableCell>
      <TableCell>{driver.totalTrips}</TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <Badge variant={statusBadgeVariant(driver.status)}>{statusLabels[driver.status]}</Badge>
          <Select
            value={driver.status}
            disabled={disabled}
            onValueChange={(status: DriverStatus) => onUpdateStatus(driver.id, status)}
          >
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="available">Available</SelectItem>
              <SelectItem value="off-duty">Off Duty</SelectItem>
              <SelectItem value="on-trip" disabled>
                On Trip — set by active trip
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </TableCell>
      <TableCell>{vehicle?.registrationNumber ?? '-'}</TableCell>
      <TableCell className="text-sm">
        {new Date(driver.certificationExpiry).toLocaleDateString()}
      </TableCell>
      <TableCell>
        <Button variant="ghost" size="icon" disabled={disabled} onClick={() => onDeleteDriver(driver)}>
          <Trash2 className="size-4 text-red-500" />
        </Button>
      </TableCell>
    </TableRow>
  );
}
