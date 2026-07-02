import { useState } from 'react';
import { Pencil, Star, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { DriverRead, DriverStatus, DriverUpdate, VehicleRead } from '../../../lib/api-types';
import { formatDate } from '../../../lib/format';
import { EditDriverDialog } from './EditDriverDialog';
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
import { TablePagination } from '../../ui/table-pagination';
import { driverInitials, statusBadgeVariant } from './driver-helpers';

const PAGE_SIZE = 10;

type DriversTableProps = {
  drivers: DriverRead[];
  vehiclesById: Map<string, VehicleRead>;
  updatingDriverId: string | null;
  onUpdateStatus: (driverId: string, status: DriverStatus) => void;
  onEditDriver: (driverId: string, patch: DriverUpdate) => Promise<void>;
  onDeleteDriver: (driver: DriverRead) => void;
};

export function DriversTable({
  drivers,
  vehiclesById,
  updatingDriverId,
  onUpdateStatus,
  onEditDriver,
  onDeleteDriver,
}: DriversTableProps) {
  const { t } = useTranslation('drivers');
  const [page, setPage] = useState(1);
  const [editingDriver, setEditingDriver] = useState<DriverRead | null>(null);
  const paginatedDrivers = drivers.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('table.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        {drivers.length === 0 ? (
          <div className="rounded-md border border-dashed p-8 text-center text-sm text-slate-600">
            {t('table.noDrivers')}
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('table.driver')}</TableHead>
                  <TableHead>{t('table.license')}</TableHead>
                  <TableHead>{t('table.phone')}</TableHead>
                  <TableHead>{t('table.rating')}</TableHead>
                  <TableHead>{t('table.totalTrips')}</TableHead>
                  <TableHead>{t('table.status')}</TableHead>
                  <TableHead>{t('table.vehicle')}</TableHead>
                  <TableHead>{t('table.certExpiry')}</TableHead>
                  <TableHead>{t('table.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedDrivers.map((driver) => (
                  <DriverTableRow
                    key={driver.id}
                    driver={driver}
                    vehicle={driver.vehicleId ? vehiclesById.get(driver.vehicleId) : undefined}
                    disabled={updatingDriverId === driver.id}
                    onUpdateStatus={onUpdateStatus}
                    onOpenEdit={setEditingDriver}
                    onDeleteDriver={onDeleteDriver}
                  />
                ))}
              </TableBody>
            </Table>
            <TablePagination
              page={page}
              pageSize={PAGE_SIZE}
              total={drivers.length}
              onPageChange={setPage}
            />
          </>
        )}
      </CardContent>

      {editingDriver && (
        <EditDriverDialog
          driver={editingDriver}
          open={editingDriver !== null}
          onOpenChange={(open) => { if (!open) setEditingDriver(null); }}
          onSave={onEditDriver}
        />
      )}
    </Card>
  );
}

function DriverTableRow({
  driver,
  vehicle,
  disabled,
  onUpdateStatus,
  onOpenEdit,
  onDeleteDriver,
}: {
  driver: DriverRead;
  vehicle?: VehicleRead;
  disabled: boolean;
  onUpdateStatus: (driverId: string, status: DriverStatus) => void;
  onOpenEdit: (driver: DriverRead) => void;
  onDeleteDriver: (driver: DriverRead) => void;
}) {
  const { t } = useTranslation('drivers');
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
          <Badge variant={statusBadgeVariant(driver.status)}>{t(`driverStatus.${driver.status}`)}</Badge>
          <Select
            value={driver.status}
            disabled={disabled}
            onValueChange={(status: DriverStatus) => onUpdateStatus(driver.id, status)}
          >
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="available">{t('driverStatus.available')}</SelectItem>
              <SelectItem value="off-duty">{t('driverStatus.off-duty')}</SelectItem>
              <SelectItem value="on-trip" disabled>
                {t('table.onTripOption')}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </TableCell>
      <TableCell>{vehicle?.registrationNumber ?? '-'}</TableCell>
      <TableCell className="text-sm">
        {formatDate(driver.certificationExpiry)}
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" disabled={disabled} onClick={() => onOpenEdit(driver)}>
            <Pencil className="size-4 text-slate-500" />
          </Button>
          <Button variant="ghost" size="icon" disabled={disabled} onClick={() => onDeleteDriver(driver)}>
            <Trash2 className="size-4 text-red-500" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
}
