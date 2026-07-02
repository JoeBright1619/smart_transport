import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { SearchX } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import type {
  DailyReportData,
  DriverReportData,
  FleetReportData,
  RouteReportData,
} from '../../../lib/api-types';

// ─── Skeleton ────────────────────────────────────────────────────────────────

export function TableSkeleton() {
  return (
    <div className="animate-pulse space-y-2">
      <div className="h-8 rounded bg-slate-200" />
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-6 rounded bg-slate-100" />
      ))}
    </div>
  );
}

// ─── Empty state ─────────────────────────────────────────────────────────────

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-slate-400">
      <SearchX className="size-10" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}

// ─── Result tables ────────────────────────────────────────────────────────────

export function SortableTable<T extends object>({
  columns,
  data,
  formatters,
}: {
  columns: { key: keyof T; label: string }[];
  data: T[];
  formatters?: Partial<Record<keyof T, (v: unknown) => string>>;
}) {
  const [sortKey, setSortKey] = useState<keyof T>(columns[0].key);
  const [asc, setAsc] = useState(true);

  const sorted = [...data].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    const cmp = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv));
    return asc ? cmp : -cmp;
  });

  function handleSort(key: keyof T) {
    if (key === sortKey) setAsc((p) => !p);
    else { setSortKey(key); setAsc(true); }
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full text-sm">
        <thead className="bg-slate-800 text-left text-xs uppercase text-white">
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className="cursor-pointer select-none px-4 py-3 hover:bg-slate-700"
                onClick={() => handleSort(col.key)}
              >
                {col.label}
                {sortKey === col.key ? (asc ? ' ▲' : ' ▼') : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
              {columns.map((col) => {
                const val = row[col.key];
                const fmt = formatters?.[col.key];
                return (
                  <td key={String(col.key)} className="px-4 py-2.5 text-slate-700">
                    {fmt ? fmt(val) : String(val)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Status badge ─────────────────────────────────────────────────────────────

export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: 'bg-emerald-100 text-emerald-700',
    idle: 'bg-amber-100 text-amber-700',
    maintenance: 'bg-red-100 text-red-700',
    offline: 'bg-slate-100 text-slate-600',
  };
  const cls = colors[(status ?? '').toLowerCase()] ?? 'bg-slate-100 text-slate-600';
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${cls}`}>
      {status ?? '—'}
    </span>
  );
}

// ─── Report-type result views ─────────────────────────────────────────────────

export function RouteReportTable({ data }: { data: RouteReportData[] }) {
  const { t } = useTranslation('analytics');
  return (
    <SortableTable
      columns={[
        { key: 'routeName', label: t('reports.columns.route') },
        { key: 'onTimeRate', label: t('reports.columns.onTimeRate') },
        { key: 'avgTripDurationMinutes', label: t('reports.columns.avgDuration') },
        { key: 'totalPassengers', label: t('reports.columns.passengers') },
        { key: 'utilisationPercentage', label: t('reports.columns.utilisation') },
      ]}
      data={data}
      formatters={{
        onTimeRate: (v) => `${Number(v).toFixed(1)}%`,
        utilisationPercentage: (v) => `${Number(v).toFixed(1)}%`,
        totalPassengers: (v) => Number(v).toLocaleString(),
      }}
    />
  );
}

export function DailyReportChart({ data }: { data: DailyReportData[] }) {
  const { t } = useTranslation('analytics');
  const summaryTrips = data.reduce((s, r) => s + r.totalTrips, 0);
  const summaryCompleted = data.reduce((s, r) => s + r.completedTrips, 0);
  const summaryPassengers = data.reduce((s, r) => s + r.totalPassengers, 0);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: t('reports.daily.totalTrips'), value: summaryTrips.toLocaleString() },
          { label: t('reports.daily.completed'), value: summaryCompleted.toLocaleString() },
          { label: t('reports.daily.totalPassengers'), value: summaryPassengers.toLocaleString() },
        ].map(({ label, value }) => (
          <Card key={label} className="bg-gradient-to-br from-slate-800 to-slate-700 text-white">
            <CardContent className="p-4">
              <p className="text-xs text-slate-400">{label}</p>
              <p className="mt-1 text-2xl font-bold">{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{t('reports.daily.tripsPerDay')}</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="completedTrips" fill="#10B981" name={t('reports.daily.completed')} radius={[3, 3, 0, 0]} />
              <Bar dataKey="cancelledTrips" fill="#EF4444" name={t('reports.daily.cancelled')} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

export function FleetReportTable({ data }: { data: FleetReportData[] }) {
  const { t } = useTranslation('analytics');
  const headers = [
    t('reports.columns.registration'),
    t('reports.columns.utilisation'),
    t('reports.columns.maintenanceEvents'),
    t('reports.columns.totalKm'),
    t('reports.columns.status'),
  ];
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full text-sm">
        <thead className="bg-slate-800 text-left text-xs uppercase text-white">
          <tr>
            {headers.map((h) => (
              <th key={h} className="px-4 py-3">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={row.vehicleId ?? i} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
              <td className="px-4 py-2.5 font-medium text-slate-800">{row.registrationNumber}</td>
              <td className="px-4 py-2.5 text-slate-700">{(row.utilisationPercentage ?? 0).toFixed(1)}%</td>
              <td className="px-4 py-2.5 text-slate-700">{row.maintenanceEvents ?? 0}</td>
              <td className="px-4 py-2.5 text-slate-700">{(row.totalKm ?? 0).toLocaleString()}</td>
              <td className="px-4 py-2.5">
                <StatusBadge status={row.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DriverReportTable({ data }: { data: DriverReportData[] }) {
  const { t } = useTranslation('analytics');
  return (
    <SortableTable
      columns={[
        { key: 'driverName', label: t('reports.columns.driver') },
        { key: 'tripsCompleted', label: t('reports.columns.tripsCompleted') },
        { key: 'onTimeRate', label: t('reports.columns.onTimeRate') },
        { key: 'avgTripDurationMinutes', label: t('reports.columns.avgDuration') },
        { key: 'totalPassengers', label: t('reports.columns.passengers') },
      ]}
      data={data}
      formatters={{
        onTimeRate: (v) => `${Number(v).toFixed(1)}%`,
        totalPassengers: (v) => Number(v).toLocaleString(),
      }}
    />
  );
}
