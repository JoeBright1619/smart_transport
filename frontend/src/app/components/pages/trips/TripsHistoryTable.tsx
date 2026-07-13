import { useTranslation } from 'react-i18next';
import type { DriverRead, RouteRead, TripRead, VehicleRead } from '../../../lib/api-types';
import { formatDateTime } from '../../../lib/format';
import { Badge } from '../../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TablePagination } from '../../ui/table-pagination';
import { delayBadgeVariant, formatDurationMinutes, tripStatusBadgeVariant } from './trips-helpers';

type TripsHistoryTableProps = {
  trips: TripRead[];
  total: number;
  page: number;
  pageSize: number;
  vehiclesById: Map<string, VehicleRead>;
  driversById: Map<string, DriverRead>;
  routesById: Map<string, RouteRead>;
  onPageChange: (page: number) => void;
};

export function TripsHistoryTable({
  trips,
  total,
  page,
  pageSize,
  vehiclesById,
  driversById,
  routesById,
  onPageChange,
}: TripsHistoryTableProps) {
  const { t } = useTranslation('trips');
  const dash = t('table.unknown');

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('table.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        {trips.length === 0 ? (
          <div className="rounded-md border border-dashed p-8 text-center text-sm text-slate-600">
            {t('table.noTrips')}
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('table.route')}</TableHead>
                    <TableHead>{t('table.vehicle')}</TableHead>
                    <TableHead>{t('table.driver')}</TableHead>
                    <TableHead>{t('table.status')}</TableHead>
                    <TableHead>{t('table.actualStart')}</TableHead>
                    <TableHead>{t('table.actualEnd')}</TableHead>
                    <TableHead>{t('table.passengers')}</TableHead>
                    <TableHead>{t('table.departure')}</TableHead>
                    <TableHead>{t('table.delay')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trips.map((trip) => {
                    const route = routesById.get(trip.routeId);
                    const vehicle = vehiclesById.get(trip.vehicleId);
                    const driver = driversById.get(trip.driverId);
                    return (
                      <TableRow key={trip.id}>
                        <TableCell className="font-medium">
                          {route ? `${route.number} · ${route.name}` : dash}
                        </TableCell>
                        <TableCell>{vehicle?.registrationNumber ?? dash}</TableCell>
                        <TableCell>{driver?.name ?? dash}</TableCell>
                        <TableCell>
                          <Badge variant={tripStatusBadgeVariant(trip.status)}>
                            {t(`status.${trip.status}`)}
                          </Badge>
                        </TableCell>
                        <TableCell className="whitespace-nowrap">
                          {trip.actualStart ? formatDateTime(trip.actualStart) : dash}
                        </TableCell>
                        <TableCell className="whitespace-nowrap">
                          {trip.actualEnd ? formatDateTime(trip.actualEnd) : dash}
                        </TableCell>
                        <TableCell>{trip.passengers}</TableCell>
                        <TableCell>
                          {trip.actualStart ? (
                            <Badge variant={delayBadgeVariant(trip.startDelayStatus)}>
                              {t(`minutes.${trip.startDelayStatus}`, {
                                duration: formatDurationMinutes(trip.startDelay),
                              })}
                            </Badge>
                          ) : (
                            dash
                          )}
                        </TableCell>
                        <TableCell>
                          {trip.status === 'completed' ? (
                            <Badge variant={delayBadgeVariant(trip.delayStatus)}>
                              {t(`minutes.${trip.delayStatus}`, {
                                duration: formatDurationMinutes(trip.delay),
                              })}
                            </Badge>
                          ) : (
                            dash
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
            <TablePagination page={page} pageSize={pageSize} total={total} onPageChange={onPageChange} />
          </>
        )}
      </CardContent>
    </Card>
  );
}
