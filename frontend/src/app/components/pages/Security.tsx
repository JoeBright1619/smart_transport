import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Shield, FileText, Lock, Eye } from 'lucide-react';

export function Security() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Security & Audit</h1>
        <p className="text-slate-600">Security monitoring and audit trail</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Active Sessions</CardTitle>
            <Shield className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Audit Logs</CardTitle>
            <FileText className="size-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,247</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Failed Logins</CardTitle>
            <Lock className="size-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-slate-500">Last 24 hours</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Data Access</CardTitle>
            <Eye className="size-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">89</div>
            <p className="text-xs text-slate-500">Today</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Audit Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { action: 'User Login', user: 'admin@transport.rw', time: '10 minutes ago', status: 'success' },
              { action: 'Vehicle Data Update', user: 'operator@transport.rw', time: '25 minutes ago', status: 'success' },
              { action: 'Route Modified', user: 'admin@transport.rw', time: '1 hour ago', status: 'success' },
              { action: 'Report Generated', user: 'operator@transport.rw', time: '2 hours ago', status: 'success' },
            ].map((event, index) => (
              <div key={index} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="font-medium text-sm">{event.action}</p>
                  <p className="text-xs text-slate-500">by {event.user}</p>
                </div>
                <div className="text-right">
                  <Badge variant="outline">{event.status}</Badge>
                  <p className="text-xs text-slate-500 mt-1">{event.time}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
