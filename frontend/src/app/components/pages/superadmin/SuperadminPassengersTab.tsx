import { useState, useEffect, useCallback } from 'react';
import { Search, UserX, UserCheck, FileText } from 'lucide-react';
import type { UserRead } from '../../../lib/api-types';
import * as superadminService from '../../../services/superadmin.service';
import { PassengerReportModal } from './PassengerReportModal';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../../ui/table';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

export function SuperadminPassengersTab() {
  const { t } = useTranslation('admin');
  const [passengers, setPassengers] = useState<UserRead[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [reportPassenger, setReportPassenger] = useState<UserRead | null>(null);

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
      toast.error(t('passengers.failedLoad'));
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
      toast.success(t('passengers.suspendedToast'));
    } catch {
      toast.error(t('passengers.failedSuspend'));
    } finally {
      setActionId(null);
    }
  };

  const handleReactivate = async (id: string) => {
    setActionId(id);
    try {
      const updated = await superadminService.reactivatePassenger(id);
      setPassengers((prev) => prev.map((p) => (p.id === id ? updated : p)));
      toast.success(t('passengers.reactivatedToast'));
    } catch {
      toast.error(t('passengers.failedReactivate'));
    } finally {
      setActionId(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('passengers.title')}</CardTitle>
        <CardDescription>
          {t('passengers.desc')}
        </CardDescription>
        <div className="relative mt-2 max-w-sm">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder={t('passengers.searchPlaceholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <p className="text-sm text-slate-500">{t('passengers.loading')}</p>
        ) : passengers.length === 0 ? (
          <p className="text-sm text-slate-500">{t('passengers.noPassengers')}</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('passengers.colName')}</TableHead>
                <TableHead>{t('passengers.colEmail')}</TableHead>
                <TableHead>{t('passengers.colPhone')}</TableHead>
                <TableHead>{t('passengers.colRegistered')}</TableHead>
                <TableHead>{t('passengers.colStatus')}</TableHead>
                <TableHead className="text-right">{t('passengers.colActions')}</TableHead>
                <TableHead></TableHead>
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
                        {isSuspended ? t('passengers.suspended') : t('passengers.active')}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {confirmId === p.id ? (
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="destructive" disabled={isBusy}
                            onClick={() => void handleSuspend(p.id)}>
                            <UserX className="mr-1 size-3" />{t('passengers.confirmSuspend')}
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => setConfirmId(null)}>
                            {t('passengers.cancel')}
                          </Button>
                        </div>
                      ) : (
                        <div className="flex justify-end gap-2">
                          {!isSuspended && (
                            <Button size="sm" variant="outline" disabled={isBusy}
                              onClick={() => setConfirmId(p.id)}>
                              <UserX className="mr-1 size-3" />{t('passengers.suspend')}
                            </Button>
                          )}
                          {isSuspended && (
                            <Button size="sm" disabled={isBusy}
                              onClick={() => void handleReactivate(p.id)}>
                              <UserCheck className="mr-1 size-3" />{t('passengers.reactivate')}
                            </Button>
                          )}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button size="sm" variant="ghost"
                        onClick={() => setReportPassenger(p)}>
                        <FileText className="mr-1 size-3" />{t('passengers.report')}
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>

      {reportPassenger && (
        <PassengerReportModal
          passenger={reportPassenger}
          open={true}
          onClose={() => setReportPassenger(null)}
        />
      )}
    </Card>
  );
}
