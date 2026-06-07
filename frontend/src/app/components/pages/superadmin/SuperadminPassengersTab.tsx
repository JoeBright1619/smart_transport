import { useState, useEffect, useCallback } from 'react';
import { Search, UserX, UserCheck } from 'lucide-react';
import type { UserRead } from '../../../lib/api-types';
import * as superadminService from '../../../services/superadmin.service';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../../ui/table';
import { toast } from 'sonner';

export function SuperadminPassengersTab() {
  const [passengers, setPassengers] = useState<UserRead[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(searchTerm), 300);
    return () => clearTimeout(t);
  }, [searchTerm]);

  const loadPassengers = useCallback(async () => {
    setLoading(true);
    try {
      const { items } = await superadminService.listPassengers({
        search: debouncedSearch || undefined,
        pageSize: 100,
      });
      setPassengers(items);
    } catch {
      toast.error('Failed to load passengers');
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch]);

  useEffect(() => { void loadPassengers(); }, [loadPassengers]);

  const handleSuspend = async (id: string) => {
    setConfirmId(null);
    setActionId(id);
    try {
      const updated = await superadminService.suspendPassenger(id);
      setPassengers((prev) => prev.map((p) => (p.id === id ? updated : p)));
      toast.success('Passenger suspended');
    } catch {
      toast.error('Failed to suspend passenger');
    } finally {
      setActionId(null);
    }
  };

  const handleReactivate = async (id: string) => {
    setActionId(id);
    try {
      const updated = await superadminService.reactivatePassenger(id);
      setPassengers((prev) => prev.map((p) => (p.id === id ? updated : p)));
      toast.success('Passenger reactivated');
    } catch {
      toast.error('Failed to reactivate passenger');
    } finally {
      setActionId(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Passengers</CardTitle>
        <CardDescription>
          Platform-wide passenger accounts. Suspend blocks login; Reactivate restores access.
        </CardDescription>
        <div className="relative mt-2 max-w-sm">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Search by name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <p className="text-sm text-slate-500">Loading passengers…</p>
        ) : passengers.length === 0 ? (
          <p className="text-sm text-slate-500">No passengers found.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Registered</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {passengers.map((p) => {
                const isBusy = actionId === p.id;
                const isSuspended = p.isDeleted;
                return (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">{p.fullName}</TableCell>
                    <TableCell>{p.email}</TableCell>
                    <TableCell>{p.phone ?? '—'}</TableCell>
                    <TableCell>{new Date(p.createdAt).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Badge variant={isSuspended ? 'destructive' : 'default'}>
                        {isSuspended ? 'Suspended' : 'Active'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {confirmId === p.id ? (
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="destructive" disabled={isBusy}
                            onClick={() => void handleSuspend(p.id)}>
                            <UserX className="mr-1 size-3" />Confirm suspend
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => setConfirmId(null)}>
                            Cancel
                          </Button>
                        </div>
                      ) : (
                        <div className="flex justify-end gap-2">
                          {!isSuspended && (
                            <Button size="sm" variant="outline" disabled={isBusy}
                              onClick={() => setConfirmId(p.id)}>
                              <UserX className="mr-1 size-3" />Suspend
                            </Button>
                          )}
                          {isSuspended && (
                            <Button size="sm" disabled={isBusy}
                              onClick={() => void handleReactivate(p.id)}>
                              <UserCheck className="mr-1 size-3" />Reactivate
                            </Button>
                          )}
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
