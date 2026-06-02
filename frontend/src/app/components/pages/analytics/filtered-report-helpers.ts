import type {
  DailyReportData,
  DriverReportData,
  FilteredReportResponse,
  FleetReportData,
  ReportType,
  RouteReportData,
} from '../../../lib/api-types';

export function toCsvRow(values: (string | number)[]): string {
  return values.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(',');
}

export function downloadCsv(filename: string, rows: (string | number)[][]): void {
  const content = rows.map(toCsvRow).join('\n');
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function buildCsvData(
  reportType: ReportType,
  data: FilteredReportResponse['data'],
): (string | number)[][] {
  if (reportType === 'route') {
    const rows = data as RouteReportData[];
    return [
      ['Route Name', 'On-Time Rate (%)', 'Avg Duration (min)', 'Total Passengers', 'Utilisation (%)'],
      ...rows.map((r) => [
        r.routeName,
        r.onTimeRate,
        r.avgTripDurationMinutes,
        r.totalPassengers,
        r.utilisationPercentage,
      ]),
    ];
  }
  if (reportType === 'daily') {
    const rows = data as DailyReportData[];
    return [
      ['Date', 'Total Trips', 'Completed', 'Cancelled', 'Passengers'],
      ...rows.map((r) => [r.date, r.totalTrips, r.completedTrips, r.cancelledTrips, r.totalPassengers]),
    ];
  }
  if (reportType === 'fleet') {
    const rows = data as FleetReportData[];
    return [
      ['Registration', 'Utilisation (%)', 'Maintenance Events', 'Total km', 'Status'],
      ...rows.map((r) => [
        r.registrationNumber,
        r.utilisationPercentage,
        r.maintenanceEvents,
        r.totalKm,
        r.status,
      ]),
    ];
  }
  // driver
  const rows = data as DriverReportData[];
  return [
    ['Driver Name', 'Trips Completed', 'On-Time Rate (%)', 'Avg Duration (min)', 'Total Passengers'],
    ...rows.map((r) => [
      r.driverName,
      r.tripsCompleted,
      r.onTimeRate,
      r.avgTripDurationMinutes,
      r.totalPassengers,
    ]),
  ];
}
