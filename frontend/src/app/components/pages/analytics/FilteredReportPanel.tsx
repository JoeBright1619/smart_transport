import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { Download, FileDown, FileText, Filter, Loader2 } from 'lucide-react';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import type {
  DailyReportData,
  DriverRead,
  DriverReportData,
  FilteredReportResponse,
  FleetReportData,
  ReportType,
  RouteRead,
  RouteReportData,
  VehicleRead,
} from '../../../lib/api-types';
import { getFilteredReport } from '../../../services/analytics.service';
import { defaultDateRange } from './analytics-helpers';
import { exportFilteredReportPDF } from './analytics-pdf';
import { useAuth } from '../../../lib/auth-context';
import { downloadCsv, buildCsvData } from './filtered-report-helpers';
import {
  TableSkeleton,
  EmptyState,
  RouteReportTable,
  DailyReportChart,
  FleetReportTable,
  DriverReportTable,
} from './FilteredReportTables';

type FilteredReportPanelProps = {
  routes: RouteRead[];
  vehicles: VehicleRead[];
  drivers: DriverRead[];
};

const DEBOUNCE_MS = 400;

const SELECT_CLS = 'h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400';

function FilterSelect({ id, label, value, onChange, children }: Readonly<{
  id: string; label: string; value: string;
  onChange: (v: string) => void; children: ReactNode;
}>) {
  return (
    <div className="space-y-1">
      <Label htmlFor={id} className="text-xs">{label}</Label>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)} className={SELECT_CLS}>
        {children}
      </select>
    </div>
  );
}

export function FilteredReportPanel({ routes, vehicles, drivers }: FilteredReportPanelProps) {
  const { user } = useAuth();
  const initialRange = defaultDateRange();

  const [reportType, setReportType] = useState<ReportType>('route');
  const [dateFrom, setDateFrom] = useState(initialRange.from);
  const [dateTo, setDateTo] = useState(initialRange.to);
  const [selectedRouteId, setSelectedRouteId] = useState('');
  const [selectedVehicleId, setSelectedVehicleId] = useState('');
  const [selectedDriverId, setSelectedDriverId] = useState('');

  const [result, setResult] = useState<FilteredReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getFilteredReport({
        reportType,
        dateFrom,
        dateTo,
        routeId: selectedRouteId || undefined,
        vehicleId: selectedVehicleId || undefined,
        driverId: selectedDriverId || undefined,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report');
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [reportType, dateFrom, dateTo, selectedRouteId, selectedVehicleId, selectedDriverId]);

  // Debounced auto-fetch on filter change
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => { void fetchReport(); }, DEBOUNCE_MS);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [fetchReport]);

  // Reset entity filters on tab change
  function handleTabChange(value: string) {
    setReportType(value as ReportType);
    setSelectedRouteId('');
    setSelectedVehicleId('');
    setSelectedDriverId('');
  }

  function handleExportCsv() {
    if (!result) return;
    const rows = buildCsvData(reportType, result.data);
    downloadCsv(`${reportType}-report-${dateFrom}-to-${dateTo}.csv`, rows);
  }

  async function handleExportPdf() {
    if (!result) return;
    await exportFilteredReportPDF({
      result,
      dateFrom,
      dateTo,
      tenantName: user?.tenantName ?? undefined,
      tenantEmail: user?.tenantEmail ?? undefined,
      tenantAddress: user?.tenantAddress ?? undefined,
      tenantPhone: user?.tenantPhone ?? undefined,
      tenantLogoPath: user?.tenantLogoPath ?? undefined,
    });
  }

  const hasData = result && result.data.length > 0;

  return (
    <Card className="shadow-sm">
      <CardHeader className="border-b pb-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Filter className="size-4 text-slate-500" />
            <CardTitle className="text-base">Custom Reports</CardTitle>
          </div>
          {hasData && (
            <div className="flex gap-2">
              <Button
                id="filtered-report-export-csv"
                variant="outline"
                size="sm"
                onClick={handleExportCsv}
              >
                <Download className="mr-1.5 size-3.5" />
                Export CSV
              </Button>
              <Button
                id="filtered-report-export-pdf"
                variant="outline"
                size="sm"
                onClick={() => void handleExportPdf()}
              >
                <FileDown className="mr-1.5 size-3.5" />
                Export PDF
              </Button>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        <Tabs value={reportType} onValueChange={handleTabChange}>
          <TabsList className="mb-4">
            <TabsTrigger value="route" id="report-tab-route">Route</TabsTrigger>
            <TabsTrigger value="daily" id="report-tab-daily">Daily</TabsTrigger>
            <TabsTrigger value="fleet" id="report-tab-fleet">Fleet</TabsTrigger>
            <TabsTrigger value="driver" id="report-tab-driver">Driver</TabsTrigger>
          </TabsList>

          {/* ── Common date range ── */}
          <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1">
              <Label htmlFor="report-date-from" className="text-xs">From</Label>
              <Input
                id="report-date-from"
                type="date"
                value={dateFrom}
                max={dateTo}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="report-date-to" className="text-xs">To</Label>
              <Input
                id="report-date-to"
                type="date"
                value={dateTo}
                min={dateFrom}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>

            {/* ── Context-sensitive filter ── */}
            <TabsContent value="route" className="m-0 col-span-2">
              <FilterSelect id="report-route-picker" label="Filter by Route" value={selectedRouteId} onChange={setSelectedRouteId}>
                <option value="">All Routes</option>
                {routes.map((r) => <option key={r.id} value={r.id}>Route {r.number} — {r.name}</option>)}
              </FilterSelect>
            </TabsContent>

            <TabsContent value="daily" className="m-0 col-span-2">
              <div className="flex h-9 items-center text-xs text-slate-400 italic">
                Showing daily aggregation for the selected date range
              </div>
            </TabsContent>

            <TabsContent value="fleet" className="m-0 col-span-2">
              <FilterSelect id="report-vehicle-picker" label="Filter by Vehicle" value={selectedVehicleId} onChange={setSelectedVehicleId}>
                <option value="">All Vehicles</option>
                {vehicles.map((v) => <option key={v.id} value={v.id}>{v.registrationNumber} — {v.model}</option>)}
              </FilterSelect>
            </TabsContent>

            <TabsContent value="driver" className="m-0 col-span-2">
              <FilterSelect id="report-driver-picker" label="Filter by Driver" value={selectedDriverId} onChange={setSelectedDriverId}>
                <option value="">All Drivers</option>
                {drivers.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </FilterSelect>
            </TabsContent>
          </div>

          {/* ── Status bar ── */}
          {loading && (
            <div className="mb-3 flex items-center gap-2 text-xs text-slate-500">
              <Loader2 className="size-3.5 animate-spin" />
              Loading report…
            </div>
          )}
          {error && !loading && (
            <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
              {error}
            </div>
          )}

          {/* ── Results ── */}
          <TabsContent value="route">
            {loading ? (
              <TableSkeleton />
            ) : !hasData ? (
              <EmptyState message="No route data matches the selected filters." />
            ) : (
              <RouteReportTable data={result!.data as RouteReportData[]} />
            )}
          </TabsContent>

          <TabsContent value="daily">
            {loading ? (
              <TableSkeleton />
            ) : !hasData ? (
              <EmptyState message="No daily data for the selected date range." />
            ) : (
              <DailyReportChart data={result!.data as DailyReportData[]} />
            )}
          </TabsContent>

          <TabsContent value="fleet">
            {loading ? (
              <TableSkeleton />
            ) : !hasData ? (
              <EmptyState message="No fleet data matches the selected filters." />
            ) : (
              <FleetReportTable data={result!.data as FleetReportData[]} />
            )}
          </TabsContent>

          <TabsContent value="driver">
            {loading ? (
              <TableSkeleton />
            ) : !hasData ? (
              <EmptyState message="No driver data matches the selected filters." />
            ) : (
              <DriverReportTable data={result!.data as DriverReportData[]} />
            )}
          </TabsContent>
        </Tabs>

        {/* Generated-at footer */}
        {result && (
          <p className="mt-4 text-right text-xs text-slate-400">
            <FileText className="mr-1 inline size-3" />
            Generated at {new Date(result.generatedAt).toLocaleString()}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
