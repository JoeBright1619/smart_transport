import { useState } from 'react';
import type { MaintenanceRead, MaintenanceStatus, VehicleRead } from '../../../lib/api-types';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TablePagination } from '../../ui/table-pagination';
import { formatDate, statusBadgeVariant, statusLabels } from './maintenance-helpers';

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
  const [page, setPage] = useState(1);
  const paginatedRecords = records.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Maintenance Records</CardTitle>
      </CardHeader>
      <CardContent>
        {records.length === 0 ? (
          <div className="rounded-md border border-dashed p-8 text-center text-sm text-slate-600">
            No maintenance records found.
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Vehicle</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Scheduled Date</TableHead>
                  <TableHead>Completed Date</TableHead>
                  <TableHead>Cost (RWF)</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Next Due</TableHead>
                  <TableHead>Actions</TableHead>
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
  return (
    <TableRow>
      <TableCell className="font-medium">{vehicle?.registrationNumber ?? 'Unknown vehicle'}</TableCell>
      <TableCell>
        <Badge variant="outline">{record.type}</Badge>
      </TableCell>
      <TableCell>{record.description}</TableCell>
      <TableCell>{formatDate(record.scheduledDate)}</TableCell>
      <TableCell>{formatDate(record.completedDate)}</TableCell>
      <TableCell>{record.cost.toLocaleString()}</TableCell>
      <TableCell>
        <Badge variant={statusBadgeVariant(record.status)}>{statusLabels[record.status]}</Badge>
      </TableCell>
      <TableCell>{formatDate(record.nextDue)}</TableCell>
      <TableCell>
        <div className="flex flex-wrap gap-2">
          {record.status === 'scheduled' && (
            <Button size="sm" variant="outline" disabled={disabled} onClick={() => onUpdateStatus(record, 'in-progress')}>
              Start
            </Button>
          )}
          {record.status === 'in-progress' && (
            <Button size="sm" disabled={disabled} onClick={() => onUpdateStatus(record, 'completed')}>
              Complete
            </Button>
          )}
        </div>
      </TableCell>
    </TableRow>
  );
}
