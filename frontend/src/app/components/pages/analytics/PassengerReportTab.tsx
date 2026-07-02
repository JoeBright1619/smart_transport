import { useCallback, useEffect, useState } from 'react';
import { Download, Info, Loader2, User } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { messageForError } from '../../../lib/error-messages';
import { Button } from '../../ui/button';
import { Card, CardContent } from '../../ui/card';
import { Label } from '../../ui/label';
import type { PassengerReportResponse, PassengerTripRecord, UserRead } from '../../../lib/api-types';
import { getPassengerReport } from '../../../services/analytics.service';
import { listUsers } from '../../../services/users.service';
import { buildPassengerCsvData, downloadCsv } from './filtered-report-helpers';
import { EmptyState, TableSkeleton } from './FilteredReportTables';

// ─── Passenger-specific sub-components ───────────────────────────────────────

function OnTimeBadge({ onTime }: Readonly<{ onTime: boolean }>) {
  const { t } = useTranslation('analytics');
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${onTime ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
      {onTime ? t('reports.passenger.onTime') : t('reports.passenger.late')}
    </span>
  );
}

function PassengerReportTable({ report }: Readonly<{ report: PassengerReportResponse }>) {
  const { t } = useTranslation('analytics');
  if (report.message && report.data.length === 0) {
    return (
      <div className="flex items-start gap-2 rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">
        <Info className="mt-0.5 size-4 shrink-0" />
        <span>{report.message}</span>
      </div>
    );
  }
  const total = report.data.length;
  const onTimeRate = total > 0 ? ((report.data.filter((r) => r.onTime).length / total) * 100).toFixed(1) : '0.0';
  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        {[{ label: t('reports.passenger.totalTrips'), value: total.toLocaleString() }, { label: t('reports.passenger.onTimeRate'), value: `${onTimeRate}%` }].map(({ label, value }) => (
          <Card key={label} className="bg-gradient-to-br from-slate-800 to-slate-700 text-white">
            <CardContent className="p-4"><p className="text-xs text-slate-400">{label}</p><p className="mt-1 text-2xl font-bold">{value}</p></CardContent>
          </Card>
        ))}
      </div>
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-800 text-left text-xs uppercase text-white">
            <tr>{[t('reports.passenger.colDate'), t('reports.passenger.colRoute'), t('reports.passenger.colBoarding'), t('reports.passenger.colAlighting'), t('reports.passenger.colDeparture'), t('reports.passenger.colOnTime')].map((h) => <th key={h} className="px-4 py-3">{h}</th>)}</tr>
          </thead>
          <tbody>
            {report.data.map((row: PassengerTripRecord, i: number) => (
              <tr key={row.tripId ?? i} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                <td className="px-4 py-2.5 text-slate-700">{row.tripDate}</td>
                <td className="px-4 py-2.5 font-medium text-slate-800">{row.routeName}</td>
                <td className="px-4 py-2.5 text-slate-700">{row.boardingStop ?? '—'}</td>
                <td className="px-4 py-2.5 text-slate-700">{row.alightingStop ?? '—'}</td>
                <td className="px-4 py-2.5 text-xs text-slate-500">{row.scheduledDeparture ?? '—'} / {row.actualDeparture ?? '—'}</td>
                <td className="px-4 py-2.5"><OnTimeBadge onTime={row.onTime} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

type Props = Readonly<{ dateFrom: string; dateTo: string }>;

const SELECT_CLS =
  'h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400';

export function PassengerReportTab({ dateFrom, dateTo }: Props) {
  const { t } = useTranslation('analytics');
  const [passengers, setPassengers] = useState<UserRead[]>([]);
  const [loadingPassengers, setLoadingPassengers] = useState(true);
  const [selectedId, setSelectedId] = useState('');

  const [report, setReport] = useState<PassengerReportResponse | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load all passengers once on mount
  useEffect(() => {
    listUsers({ role: 'passenger', pageSize: 100 })
      .then((res) => setPassengers(res.items))
      .catch(() => setPassengers([]))
      .finally(() => setLoadingPassengers(false));
  }, []);

  const fetchReport = useCallback(async (passengerId: string) => {
    if (!passengerId) { setReport(null); return; }
    setLoadingReport(true);
    setError(null);
    try {
      const data = await getPassengerReport({ passengerId, dateFrom, dateTo });
      setReport(data);
    } catch (err) {
      setError(messageForError(err));
      setReport(null);
    } finally {
      setLoadingReport(false);
    }
  }, [dateFrom, dateTo]);

  // Re-fetch when dates change (if a passenger is already selected)
  useEffect(() => {
    if (selectedId) void fetchReport(selectedId);
  }, [selectedId, fetchReport]);

  function handleSelect(id: string) {
    setSelectedId(id);
    setReport(null);
  }

  function handleExportCsv() {
    if (!report || report.data.length === 0) return;
    const rows = buildPassengerCsvData(report.data);
    downloadCsv(`passenger-${report.passengerId}-report.csv`, rows);
  }

  const selectedPassenger = passengers.find((p) => p.id === selectedId);

  return (
    <div className="space-y-4">
      {/* Passenger picker */}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1">
          <Label htmlFor="passenger-picker" className="text-xs">{t('reports.passenger.selectPassenger')}</Label>
          {loadingPassengers ? (
            <div className="flex h-9 items-center gap-2 text-xs text-slate-400">
              <Loader2 className="size-3.5 animate-spin" /> {t('reports.passenger.loadingPassengers')}
            </div>
          ) : (
            <select
              id="passenger-picker"
              value={selectedId}
              onChange={(e) => handleSelect(e.target.value)}
              className={SELECT_CLS}
            >
              <option value="">{t('reports.passenger.choosePassenger')}</option>
              {passengers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.fullName ?? p.email ?? p.id}
                </option>
              ))}
            </select>
          )}
        </div>

        {report && report.data.length > 0 && (
          <div className="flex items-end">
            <Button variant="outline" size="sm" onClick={handleExportCsv}>
              <Download className="mr-1.5 size-3.5" />
              {t('reports.exportCsv')}
            </Button>
          </div>
        )}
      </div>

      {/* Passenger identity banner */}
      {selectedPassenger && (
        <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
          <User className="size-4 shrink-0 text-slate-400" />
          <span>
            <span className="font-medium text-slate-800">
              {selectedPassenger.fullName ?? selectedPassenger.email}
            </span>
            {' · '}
            {selectedPassenger.email}
          </span>
        </div>
      )}

      {/* Status / error */}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Results */}
      {!selectedId ? (
        <EmptyState message={t('reports.passenger.selectToView')} />
      ) : loadingReport ? (
        <TableSkeleton />
      ) : report ? (
        <PassengerReportTable report={report} />
      ) : null}
    </div>
  );
}
