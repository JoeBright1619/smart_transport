import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { mockAlerts } from '../../lib/mock-data';
import { AlertTriangle, Clock, CheckCircle, XCircle, Bell } from 'lucide-react';

export function Alerts() {
  const [alerts, setAlerts] = useState(mockAlerts);

  const acknowledgeAlert = (id: string) => {
    setAlerts(alerts.map(alert =>
      alert.id === id ? { ...alert, acknowledged: true } : alert
    ));
  };

  const unacknowledgedAlerts = alerts.filter(a => !a.acknowledged);
  const acknowledgedAlerts = alerts.filter(a => a.acknowledged);

  const criticalAlerts = unacknowledgedAlerts.filter(a => a.severity === 'critical');
  const highAlerts = unacknowledgedAlerts.filter(a => a.severity === 'high');

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'delay':
        return <Clock className="size-5" />;
      case 'breakdown':
        return <XCircle className="size-5" />;
      case 'maintenance':
        return <AlertTriangle className="size-5" />;
      default:
        return <Bell className="size-5" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-500';
      case 'high':
        return 'text-orange-500';
      case 'medium':
        return 'text-yellow-500';
      default:
        return 'text-blue-500';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Alerts & Notifications</h1>
        <p className="text-slate-600">System alerts and event notifications</p>
      </div>

      {/* Alert Summary */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Unread</CardTitle>
            <Bell className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{unacknowledgedAlerts.length}</div>
            <p className="text-xs text-slate-500">Pending review</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Critical</CardTitle>
            <AlertTriangle className="size-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{criticalAlerts.length}</div>
            <p className="text-xs text-slate-500">Immediate action required</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">High Priority</CardTitle>
            <AlertTriangle className="size-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{highAlerts.length}</div>
            <p className="text-xs text-slate-500">Requires attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Acknowledged</CardTitle>
            <CheckCircle className="size-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{acknowledgedAlerts.length}</div>
            <p className="text-xs text-slate-500">Resolved or reviewed</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="unacknowledged" className="space-y-4">
        <TabsList>
          <TabsTrigger value="unacknowledged">
            Unread ({unacknowledgedAlerts.length})
          </TabsTrigger>
          <TabsTrigger value="acknowledged">
            Acknowledged ({acknowledgedAlerts.length})
          </TabsTrigger>
          <TabsTrigger value="all">
            All Alerts ({alerts.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="unacknowledged" className="space-y-4">
          {criticalAlerts.length > 0 && (
            <Card className="border-red-200 bg-red-50">
              <CardHeader>
                <CardTitle className="text-red-700 flex items-center gap-2">
                  <AlertTriangle className="size-5" />
                  Critical Alerts
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {criticalAlerts.map(alert => (
                  <div key={alert.id} className="rounded-lg bg-white p-4 shadow-sm">
                    <div className="flex items-start gap-3">
                      <div className={getSeverityColor(alert.severity)}>
                        {getAlertIcon(alert.type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="font-medium">{alert.title}</p>
                            <p className="text-sm text-slate-600 mt-1">{alert.message}</p>
                            <p className="text-xs text-slate-400 mt-2">
                              {new Date(alert.timestamp).toLocaleString()}
                            </p>
                          </div>
                          <Badge variant="destructive">{alert.severity}</Badge>
                        </div>
                        <Button
                          size="sm"
                          className="mt-3"
                          onClick={() => acknowledgeAlert(alert.id)}
                        >
                          Acknowledge
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Other Unread Alerts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {unacknowledgedAlerts.filter(a => a.severity !== 'critical').map(alert => (
                <div key={alert.id} className="rounded-lg border p-4">
                  <div className="flex items-start gap-3">
                    <div className={getSeverityColor(alert.severity)}>
                      {getAlertIcon(alert.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-medium">{alert.title}</p>
                          <p className="text-sm text-slate-600 mt-1">{alert.message}</p>
                          <p className="text-xs text-slate-400 mt-2">
                            {new Date(alert.timestamp).toLocaleString()}
                          </p>
                        </div>
                        <Badge variant={
                          alert.severity === 'high' ? 'destructive' :
                          alert.severity === 'medium' ? 'default' : 'secondary'
                        }>
                          {alert.severity}
                        </Badge>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-3"
                        onClick={() => acknowledgeAlert(alert.id)}
                      >
                        Acknowledge
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
              {unacknowledgedAlerts.filter(a => a.severity !== 'critical').length === 0 && (
                <div className="text-center py-8 text-slate-500">
                  <CheckCircle className="size-12 mx-auto mb-3 text-green-500" />
                  <p>All alerts have been acknowledged</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="acknowledged" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Acknowledged Alerts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {acknowledgedAlerts.map(alert => (
                <div key={alert.id} className="rounded-lg border bg-slate-50 p-4">
                  <div className="flex items-start gap-3">
                    <div className="text-slate-400">
                      {getAlertIcon(alert.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-medium text-slate-700">{alert.title}</p>
                          <p className="text-sm text-slate-600 mt-1">{alert.message}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <p className="text-xs text-slate-400">
                              {new Date(alert.timestamp).toLocaleString()}
                            </p>
                            <CheckCircle className="size-3 text-green-600" />
                            <span className="text-xs text-green-600">Acknowledged</span>
                          </div>
                        </div>
                        <Badge variant="outline">{alert.severity}</Badge>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {acknowledgedAlerts.length === 0 && (
                <div className="text-center py-8 text-slate-500">
                  <p>No acknowledged alerts</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="all" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>All Alerts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.map(alert => (
                <div key={alert.id} className={`rounded-lg border p-4 ${alert.acknowledged ? 'bg-slate-50' : ''}`}>
                  <div className="flex items-start gap-3">
                    <div className={alert.acknowledged ? 'text-slate-400' : getSeverityColor(alert.severity)}>
                      {getAlertIcon(alert.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className={`font-medium ${alert.acknowledged ? 'text-slate-700' : ''}`}>
                            {alert.title}
                          </p>
                          <p className="text-sm text-slate-600 mt-1">{alert.message}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <p className="text-xs text-slate-400">
                              {new Date(alert.timestamp).toLocaleString()}
                            </p>
                            {alert.acknowledged && (
                              <>
                                <CheckCircle className="size-3 text-green-600" />
                                <span className="text-xs text-green-600">Acknowledged</span>
                              </>
                            )}
                          </div>
                        </div>
                        <Badge variant={alert.acknowledged ? 'outline' :
                          alert.severity === 'critical' ? 'destructive' :
                          alert.severity === 'high' ? 'destructive' : 'default'
                        }>
                          {alert.severity}
                        </Badge>
                      </div>
                      {!alert.acknowledged && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="mt-3"
                          onClick={() => acknowledgeAlert(alert.id)}
                        >
                          Acknowledge
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
