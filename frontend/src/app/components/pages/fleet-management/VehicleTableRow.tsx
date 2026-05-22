import { Trash2 } from 'lucide-react';
import type { DriverRead, RouteRead, VehicleRead, VehicleStatus, VehicleUpdate } from '../../../lib/api-types';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { TableCell, TableRow } from '../../ui/table';
import {
  formatLocation,
  formatRelativeTime,
  fuelBarClass,
  unassignedValue,
  vehicleStatuses,
} from './fleet-helpers';

type VehicleTableRowProps = {
  vehicle: VehicleRead;
  drivers: DriverRead[];
  routes: RouteRead[];
  disabled: boolean;
  updateVehicle: (vehicleId: string, patch: VehicleUpdate) => Promise<void>;
  deleteVehicle: (vehicle: VehicleRead) => Promise<void>;
};

export function VehicleTableRow({
  vehicle,
  drivers,
  routes,
  disabled,
  updateVehicle,
  deleteVehicle,
}: VehicleTableRowProps) {
  const fuel = vehicle.fuel ?? 0;

  return (
    <TableRow>
      <TableCell className="font-medium">{vehicle.registrationNumber}</TableCell>
      <TableCell>{vehicle.model}</TableCell>
      <TableCell>{vehicle.capacity}</TableCell>
      <TableCell>
        <Select
          value={vehicle.status}
          disabled={disabled}
          onValueChange={(value) => void updateVehicle(vehicle.id, { status: value as VehicleStatus })}
        >
          <SelectTrigger size="sm" className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {vehicleStatuses.map((status) => (
              <SelectItem key={status} value={status}>
                {status}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </TableCell>
      <TableCell>
        <AssignmentSelect
          value={vehicle.driverId}
          items={drivers.map((driver) => ({ id: driver.id, label: driver.name }))}
          disabled={disabled}
          onChange={(driverId) => void updateVehicle(vehicle.id, { driverId })}
        />
      </TableCell>
      <TableCell>
        <AssignmentSelect
          value={vehicle.routeId}
          items={routes.map((route) => ({ id: route.id, label: route.number }))}
          disabled={disabled}
          onChange={(routeId) => void updateVehicle(vehicle.id, { routeId })}
          widthClass="w-32"
        />
      </TableCell>
      <TableCell>{formatLocation(vehicle)}</TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <div className="h-2 w-16 rounded-full bg-slate-200">
            <div className={`h-full rounded-full ${fuelBarClass(vehicle.fuel)}`} style={{ width: `${fuel}%` }} />
          </div>
          <span className="text-sm">{fuel}%</span>
        </div>
      </TableCell>
      <TableCell>
        <Badge
          variant={
            vehicle.engineStatus === 'good'
              ? 'default'
              : vehicle.engineStatus === 'warning'
                ? 'outline'
                : 'destructive'
          }
        >
          {vehicle.engineStatus}
        </Badge>
      </TableCell>
      <TableCell>{formatRelativeTime(vehicle.lastUpdate)}</TableCell>
      <TableCell>
        <Button variant="ghost" size="icon" disabled={disabled} onClick={() => void deleteVehicle(vehicle)}>
          <Trash2 className="size-4" />
        </Button>
      </TableCell>
    </TableRow>
  );
}

function AssignmentSelect({
  value,
  items,
  disabled,
  onChange,
  widthClass = 'w-40',
}: {
  value: string | null;
  items: Array<{ id: string; label: string }>;
  disabled: boolean;
  onChange: (value: string | null) => void;
  widthClass?: string;
}) {
  return (
    <Select
      value={value ?? unassignedValue}
      disabled={disabled}
      onValueChange={(nextValue) => onChange(nextValue === unassignedValue ? null : nextValue)}
    >
      <SelectTrigger size="sm" className={widthClass}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={unassignedValue}>Unassigned</SelectItem>
        {items.map((item) => (
          <SelectItem key={item.id} value={item.id}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
