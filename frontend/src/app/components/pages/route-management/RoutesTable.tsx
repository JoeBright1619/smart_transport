import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Trash2 } from 'lucide-react';
import type { RouteRead, RouteUpdate } from '../../../lib/api-types';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TablePagination } from '../../ui/table-pagination';
import { EditRouteModal } from './EditRouteModal';

const PAGE_SIZE = 10;

type RoutesTableProps = {
  routes: RouteRead[];
  updatingRouteId: string | null;
  onUpdateRoute: (routeId: string, patch: RouteUpdate) => Promise<void>;
  onDeleteRoute: (route: RouteRead) => Promise<void>;
};

export function RoutesTable({
  routes,
  updatingRouteId,
  onUpdateRoute,
  onDeleteRoute,
}: RoutesTableProps) {
  const { t } = useTranslation('routes');
  const [page, setPage] = useState(1);
  const paginatedRoutes = routes.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('routes')}</CardTitle>
      </CardHeader>
      <CardContent>
        {routes.length === 0 ? (
          <p className="text-sm text-slate-500">{t('noRoutes')}</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('colRouteNumber')}</TableHead>
                  <TableHead>{t('colName')}</TableHead>
                  <TableHead>{t('colStops')}</TableHead>
                  <TableHead>{t('colDistance')}</TableHead>
                  <TableHead>{t('colDuration')}</TableHead>
                  <TableHead>{t('colStatus')}</TableHead>
                  <TableHead>{t('colActions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedRoutes.map((route) => {
                  const disabled = updatingRouteId === route.id;
                  return (
                    <TableRow key={route.id} className={route.isActive ? undefined : 'bg-slate-50/70 opacity-70'}>
                      <TableCell>
                        <Badge style={{ backgroundColor: route.color }} className="text-white">
                          {route.number}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium">
                        <span className={route.isActive ? undefined : 'text-slate-500'}>{route.name}</span>
                      </TableCell>
                      <TableCell>{t('stopsCount', { count: route.stops.length })}</TableCell>
                      <TableCell>{t('km', { value: route.distance })}</TableCell>
                      <TableCell>{t('min', { value: route.duration })}</TableCell>
                      <TableCell>
                        <Badge variant={route.isActive ? 'default' : 'secondary'}>
                          {route.isActive ? t('active') : t('inactive')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={disabled}
                            onClick={() => void onUpdateRoute(route.id, { isActive: !route.isActive })}
                          >
                            {route.isActive ? t('deactivate') : t('activate')}
                          </Button>
                          <EditRouteModal
                            route={route}
                            onUpdateRoute={onUpdateRoute}
                            disabled={disabled}
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            disabled={disabled}
                            onClick={() => void onDeleteRoute(route)}
                          >
                            <Trash2 className="size-4 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            <TablePagination
              page={page}
              pageSize={PAGE_SIZE}
              total={routes.length}
              onPageChange={setPage}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
