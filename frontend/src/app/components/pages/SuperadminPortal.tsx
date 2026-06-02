import { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { Building2, Bus, RefreshCw, Users, UserCheck, Activity, Info } from 'lucide-react';
import type { SuperadminAnalytics, TenantRead, TenantDetail } from '../../lib/api-types';
import { setStoredToken } from '../../lib/api-client';
import * as superadminService from '../../services/superadmin.service';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Skeleton } from '../ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { toast } from 'sonner';
import React from 'react';

export function SuperadminPortal() {
  const [analytics, setAnalytics] = useState<SuperadminAnalytics | null>(null);
  const [tenants, setTenants] = useState<TenantRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { tab } = useParams<{ tab: string }>();
  const navigate = useNavigate();
  const [actionTenantId, setActionTenantId] = useState<string | null>(null);
  const [selectedTenant, setSelectedTenant] = useState<TenantDetail | null>(null);
  const [tenantDetailActive, setTenantDetailActive] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const activeTab = tenantDetailActive ? 'tenant-detail' : (tab ?? 'analytics');

  const loadPortal = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [analyticsData, tenantData] = await Promise.all([
        superadminService.getSuperadminAnalytics(),
        superadminService.listTenants({ pageSize: 100 }),
      ]);

      setAnalytics(analyticsData);
      setTenants(tenantData.items);
    } catch (fetchError) {
      setError(
        fetchError instanceof Error ? fetchError.message : 'Unable to load platform data',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPortal();
  }, [loadPortal]);

  const handleToggleActive = async (tenant: TenantRead, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setActionTenantId(tenant.id);

    try {
      const updated = await superadminService.updateTenant(tenant.id, {
        isActive: !tenant.isActive,
      });
      setTenants((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      if (selectedTenant?.id === tenant.id) {
        setSelectedTenant(prev => prev ? { ...prev, isActive: updated.isActive } : prev);
      }
      toast.success(
        updated.isActive ? `${updated.name} reactivated` : `${updated.name} suspended`,
      );
    } catch (toggleError) {
      toast.error(
        toggleError instanceof Error ? toggleError.message : 'Failed to update tenant',
      );
    } finally {
      setActionTenantId(null);
    }
  };

  const handleImpersonate = async (tenant: TenantRead, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setActionTenantId(tenant.id);

    try {
      const { accessToken } = await superadminService.impersonateTenant(tenant.id);
      setStoredToken(accessToken);
      toast.success(`Impersonating ${tenant.name}`);
      window.location.assign('/');
    } catch (impersonateError) {
      toast.error(
        impersonateError instanceof Error
          ? impersonateError.message
          : 'Failed to impersonate tenant admin',
      );
      setActionTenantId(null);
    }
  };

  const handleSelectTenant = async (tenantId: string) => {
    setTenantDetailActive(true);
    setLoadingDetail(true);
    try {
      const detail = await superadminService.getTenant(tenantId);
      setSelectedTenant(detail);
    } catch (err) {
      toast.error('Failed to load tenant details');
    } finally {
      setLoadingDetail(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, index) => (
            <Card key={index}>
              <CardContent className="p-6">
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Platform Administration</h1>
          <p className="text-slate-600">Manage tenants and view platform-wide metrics</p>
        </div>
        <Card>
          <CardContent className="flex flex-col items-start gap-4 p-6">
            <p className="font-medium text-red-700">Unable to load platform data</p>
            <p className="text-sm text-slate-600">{error}</p>
            <Button onClick={() => void loadPortal()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Platform Administration</h1>
          <p className="text-slate-600">Manage tenants and view platform-wide metrics</p>
        </div>
        <Button variant="outline" onClick={() => void loadPortal()}>
          <RefreshCw className="mr-2 size-4" />
          Refresh
        </Button>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={(value) => {
          if (value === 'tenant-detail') return;
          setTenantDetailActive(false);
          navigate(`/superadmin/${value}`);
        }}
        className="space-y-4"
      >
        <TabsList>
          <TabsTrigger value="analytics">
            <Activity className="mr-2 size-4" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="tenants">
            <Building2 className="mr-2 size-4" />
            Tenants
          </TabsTrigger>
          <TabsTrigger value="tenant-detail" disabled={!selectedTenant && !loadingDetail}>
            <Info className="mr-2 size-4" />
            Tenant Detail
          </TabsTrigger>
        </TabsList>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">Total Tenants</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Building2 className="size-4 text-blue-600" />
                  <span className="text-2xl font-bold">{analytics?.totalTenants ?? 0}</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">Active Tenants</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <UserCheck className="size-4 text-emerald-600" />
                  <span className="text-2xl font-bold">{analytics?.activeTenants ?? 0}</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">Total Vehicles</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Bus className="size-4 text-indigo-600" />
                  <span className="text-2xl font-bold">{analytics?.totalVehicles ?? 0}</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">Trips Today</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics?.totalTripsToday ?? 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">Passengers Today</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Users className="size-4 text-purple-600" />
                  <span className="text-2xl font-bold">
                    {(analytics?.totalPassengersToday ?? 0).toLocaleString()}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="tenants" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Tenants</CardTitle>
              <CardDescription>Click on a row to view full details.</CardDescription>
            </CardHeader>
            <CardContent>
              {tenants.length === 0 ? (
                <p className="text-sm text-slate-500">No tenants registered on the platform.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Contact</TableHead>
                      <TableHead>Users</TableHead>
                      <TableHead>Vehicles</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tenants.map((tenant) => {
                      const isBusy = actionTenantId === tenant.id;

                      return (
                        <TableRow
                          key={tenant.id}
                          className="cursor-pointer hover:bg-slate-50"
                          onClick={() => void handleSelectTenant(tenant.id)}
                        >
                          <TableCell className="font-medium">{tenant.name}</TableCell>
                          <TableCell>{tenant.contactEmail}</TableCell>
                          <TableCell>{tenant.userCount}</TableCell>
                          <TableCell>{tenant.vehicleCount}</TableCell>
                          <TableCell>
                            <Badge variant={tenant.isActive ? 'default' : 'secondary'}>
                              {tenant.isActive ? 'Active' : 'Suspended'}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={isBusy || !tenant.isActive}
                                onClick={(e) => void handleImpersonate(tenant, e)}
                              >
                                Impersonate
                              </Button>
                              <Button
                                size="sm"
                                variant={tenant.isActive ? 'destructive' : 'default'}
                                disabled={isBusy}
                                onClick={(e) => void handleToggleActive(tenant, e)}
                              >
                                {tenant.isActive ? 'Suspend' : 'Reactivate'}
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tenant-detail" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Tenant Detail</CardTitle>
              <CardDescription>Detailed view of the selected tenant.</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingDetail ? (
                <Skeleton className="h-40 w-full" />
              ) : selectedTenant ? (
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-slate-500">Name</h4>
                      <p className="text-lg font-medium">{selectedTenant.name}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-slate-500">Contact Email</h4>
                      <p>{selectedTenant.contactEmail}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-slate-500">Status</h4>
                      <Badge variant={selectedTenant.isActive ? 'default' : 'secondary'} className="mt-1">
                        {selectedTenant.isActive ? 'Active' : 'Suspended'}
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-slate-500">Created At</h4>
                      <p>{new Date(selectedTenant.createdAt).toLocaleString()}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-slate-500">Updated At</h4>
                      <p>{new Date(selectedTenant.updatedAt).toLocaleString()}</p>
                    </div>
                    <div className="flex gap-4 pt-2">
                      <div>
                        <h4 className="text-sm font-medium text-slate-500">Users</h4>
                        <p className="text-xl font-bold">{selectedTenant.userCount}</p>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-slate-500">Vehicles</h4>
                        <p className="text-xl font-bold">{selectedTenant.vehicleCount}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-slate-500">Select a tenant from the Tenants tab to view details.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
