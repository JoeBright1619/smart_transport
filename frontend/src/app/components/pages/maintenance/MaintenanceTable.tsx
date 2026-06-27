import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { MaintenanceRead, MaintenanceStatus, VehicleRead } from '../../../lib/api-types';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TablePagination } from '../../ui/table-pagination';
import { formatDate, statusBadgeVariant } from './maintenance-helpers';

const PAGE_SIZE = 10;

type MaintenanceTableProps = {
  records: MaintenanceRead[];
  vehiclesById: Map<string, VehicleRead>;
  updatingRecordId: string | null;
  onUpdateStatus: (record: MaintenanceRead, status: MaintenanceStatus) => void;
};

export function MaintenanceTable({
  records,
  vehiclesById,
  updatingRecordId,
  onUpdateStatus,
}: MaintenanceTableProps) {
  const { t } = useTranslation('maintenance');
  const [page, setPage] = useState(1);
  const paginatedRecords = records.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('table.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        {records.length === 0 ? (
          <div className="rounded-md border border-dashed p-8 text-center text-sm text-slate-600">
            {t('table.noRecords')}
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('table.vehicle')}</TableHead>
                  <TableHead>{t('table.type')}</TableHead>
                  <TableHead>{t('table.description')}</TableHead>
                  <TableHead>{t('table.scheduledDate')}</TableHead>
                  <TableHead>{t('table.completedDate')}</TableHead>
                  <TableHead>{t('table.cost')}</TableHead>
                  <TableHead>{t('table.status')}</TableHead>
                  <TableHead>{t('table.nextDue')}</TableHead>
                  <TableHead>{t('table.actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedRecords.map((record) => (
                  <MaintenanceTableRow
                    key={record.id}
                    record={record}
                    vehicle={vehiclesById.get(record.vehicleId)}
                    disabled={updatingRecordId === record.id}
                    onUpdateStatus={onUpdateStatus}
                  />
                ))}
              </TableBody>
            </Table>
            <TablePagination
              page={page}
              pageSize={PAGE_SIZE}
              total={records.length}
              onPageChange={setPage}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}

function MaintenanceTableRow({
  record,
  vehicle,
  disabled,
  onUpdateStatus,
}: {
  record: MaintenanceRead;
  vehicle?: VehicleRead;
  disabled: boolean;
  onUpdateStatus: (record: MaintenanceRead, status: MaintenanceStatus) => void;
}) {
  const { t } = useTranslation('maintenance');
  return (
    <TableRow>
      <TableCell className="font-medium">{vehicle?.registrationNumber ?? t('table.unknownVehicle')}</TableCell>
      <TableCell>
        <Badge variant="outline">{t(`maintenanceType.${record.type}`)}</Badge>
      </TableCell>
      <TableCell>{record.description}</TableCell>
      <TableCell>{formatDate(record.scheduledDate)}</TableCell>
      <TableCell>{formatDate(record.completedDate)}</TableCell>
      <TableCell>{record.cost.toLocaleString()}</TableCell>
      <TableCell>
        <Badge variant={statusBadgeVariant(record.status)}>{t(`maintenanceStatus.${record.status}`)}</Badge>
      </TableCell>
      <TableCell>{formatDate(record.nextDue)}</TableCell>
      <TableCell>
        <div className="flex flex-wrap gap-2">
          {record.status === 'scheduled' && (
            <Button size="sm" variant="outline" disabled={disabled} onClick={() => onUpdateStatus(record, 'in-progress')}>
              {t('table.start')}
            </Button>
          )}
          {record.status === 'in-progress' && (
            <Button size="sm" disabled={disabled} onClick={() => onUpdateStatus(record, 'completed')}>
              {t('table.complete')}
            </Button>
          )}
        </div>
      </TableCell>
    </TableRow>
  );
}
