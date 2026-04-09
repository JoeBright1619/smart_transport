import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { mockMaintenanceRecords, mockVehicles } from '../../lib/mock-data';
import { Wrench, Calendar, DollarSign, CheckCircle } from 'lucide-react';

export function Maintenance() {
  const scheduled = mockMaintenanceRecords.filter(m => m.status === 'scheduled').length;
  const inProgress = mockMaintenanceRecords.filter(m => m.status === 'in-progress').length;
  const completed = mockMaintenanceRecords.filter(m => m.status === 'completed').length;
  const totalCost = mockMaintenanceRecords.reduce((sum, m) => sum + m.cost, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Maintenance Management</h1>
        <p className="text-slate-600">Vehicle maintenance tracking and scheduling</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Scheduled</CardTitle>
            <Calendar className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scheduled}</div>
            <p className="text-xs text-slate-500">Upcoming services</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">In Progress</CardTitle>
            <Wrench className="size-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{inProgress}</div>
            <p className="text-xs text-slate-500">Currently servicing</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Completed</CardTitle>
            <CheckCircle className="size-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completed}</div>
            <p className="text-xs text-slate-500">This period</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Cost</CardTitle>
            <DollarSign className="size-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(totalCost / 1000).toFixed(0)}K</div>
            <p className="text-xs text-slate-500">RWF</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Maintenance Records</CardTitle>
            <Button>Schedule Maintenance</Button>
          </div>
        </CardHeader>
        <CardContent>
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
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockMaintenanceRecords.map((record) => {
                const vehicle = mockVehicles.find(v => v.id === record.vehicleId);
                return (
                  <TableRow key={record.id}>
                    <TableCell className="font-medium">{vehicle?.registrationNumber}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{record.type}</Badge>
                    </TableCell>
                    <TableCell>{record.description}</TableCell>
                    <TableCell>{new Date(record.scheduledDate).toLocaleDateString()}</TableCell>
                    <TableCell>
                      {record.completedDate 
                        ? new Date(record.completedDate).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell>{record.cost.toLocaleString()}</TableCell>
                    <TableCell>
                      <Badge variant={
                        record.status === 'completed' ? 'default' :
                        record.status === 'in-progress' ? 'secondary' : 'outline'
                      }>
                        {record.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {record.nextDue 
                        ? new Date(record.nextDue).toLocaleDateString()
                        : '-'}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
