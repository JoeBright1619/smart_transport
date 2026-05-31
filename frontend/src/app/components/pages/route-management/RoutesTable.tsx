import { useState } from 'react';
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
  const [page, setPage] = useState(1);
  const paginatedRoutes = routes.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Routes</CardTitle>
      </CardHeader>
      <CardContent>
        {routes.length === 0 ? (
          <p className="text-sm text-slate-500">No routes found.</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Route Number</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Stops</TableHead>
                  <TableHead>Distance</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
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
                      <TableCell>{route.stops.length} stops</TableCell>
                      <TableCell>{route.distance} km</TableCell>
                      <TableCell>{route.duration} min</TableCell>
                      <TableCell>
                        <Badge variant={route.isActive ? 'default' : 'secondary'}>
                          {route.isActive ? 'Active' : 'Inactive'}
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
                            {route.isActive ? 'Deactivate' : 'Activate'}
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
