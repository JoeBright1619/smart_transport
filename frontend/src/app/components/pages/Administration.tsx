import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Settings, Database, Users, Shield } from 'lucide-react';

export function Administration() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">System Administration</h1>
        <p className="text-slate-600">System configuration and management</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="cursor-pointer hover:shadow-lg transition-shadow">
          <CardHeader>
            <Users className="size-10 text-blue-600 mb-2" />
            <CardTitle>User Management</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600">
              Manage user accounts, roles, and permissions
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow">
          <CardHeader>
            <Database className="size-10 text-green-600 mb-2" />
            <CardTitle>Data Management</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600">
              Configure vehicles, routes, and operational data
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow">
          <CardHeader>
            <Settings className="size-10 text-purple-600 mb-2" />
            <CardTitle>System Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600">
              General system configuration and preferences
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow">
          <CardHeader>
            <Shield className="size-10 text-red-600 mb-2" />
            <CardTitle>Security Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600">
              Configure security policies and authentication
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
