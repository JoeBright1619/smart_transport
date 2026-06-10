import type { Dispatch, FormEvent, SetStateAction } from 'react';
import { useEffect, useState } from 'react';
import { Search } from 'lucide-react';
import type { DriverRead, RouteRead, VehicleRead, VehicleUpdate } from '../../../lib/api-types';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Input } from '../../ui/input';
import { Table, TableBody, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TablePagination } from '../../ui/table-pagination';
import { AddVehicleDialog } from './AddVehicleDialog';
import type { FleetFormState } from './useFleetManagement';
import { VehicleTableRow } from './VehicleTableRow';

const PAGE_SIZE = 10;

type VehicleFleetTableProps = {
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  vehicles: VehicleRead[];
  drivers: DriverRead[];
  routes: RouteRead[];
  updatingVehicleId: string | null;
  updateVehicle: (vehicleId: string, patch: VehicleUpdate) => Promise<void>;
  deleteVehicle: (vehicle: VehicleRead) => Promise<void>;
  dialogOpen: boolean;
  setDialogOpen: (open: boolean) => void;
  form: FleetFormState;
  setForm: Dispatch<SetStateAction<FleetFormState>>;
  submitting: boolean;
  createVehicle: (event: FormEvent) => void;
};

export function VehicleFleetTable({
  searchTerm,
  setSearchTerm,
  vehicles,
  drivers,
  routes,
  updatingVehicleId,
  updateVehicle,
  deleteVehicle,
  dialogOpen,
  setDialogOpen,
  form,
  setForm,
  submitting,
  createVehicle,
}: VehicleFleetTableProps) {
  const [page, setPage] = useState(1);

  // Reset to first page whenever the filtered list changes
  useEffect(() => { setPage(1); }, [searchTerm]);

  const paginatedVehicles = vehicles.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <CardTitle>Vehicle Fleet</CardTitle>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="Search vehicles..."
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                className="w-full pl-10 sm:w-64"
              />
            </div>
            <AddVehicleDialog
              open={dialogOpen}
              onOpenChange={setDialogOpen}
              form={form}
              setForm={setForm}
              submitting={submitting}
              onSubmit={createVehicle}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {vehicles.length === 0 ? (
          <p className="text-sm text-slate-500">No vehicles found.</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Registration</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Seats</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Driver</TableHead>
                  <TableHead>Route</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Fuel</TableHead>
                  <TableHead>Engine</TableHead>
                  <TableHead>Updated</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedVehicles.map((vehicle) => (
                  <VehicleTableRow
                    key={vehicle.id}
                    vehicle={vehicle}
                    drivers={drivers}
                    routes={routes}
                    disabled={updatingVehicleId === vehicle.id}
                    updateVehicle={updateVehicle}
                    deleteVehicle={deleteVehicle}
                  />
                ))}
              </TableBody>
            </Table>
            <TablePagination
              page={page}
              pageSize={PAGE_SIZE}
              total={vehicles.length}
              onPageChange={setPage}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
