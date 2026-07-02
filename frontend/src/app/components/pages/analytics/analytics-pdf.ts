import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import i18n from '../../../lib/i18n';
import { formatDate, formatDateTime, formatNumber } from '../../../lib/format';
import type {
  AnalyticsData,
  DailyReportData,
  DriverReportData,
  FilteredReportResponse,
  FleetReportData,
  RouteReportData,
} from '../../../lib/api-types';
import type { FleetStatusDatum, RoutePerformanceDatum } from './analytics-helpers';

type ReportInput = {
  data: AnalyticsData;
  routePerformance: RoutePerformanceDatum[];
  fleetStatus: FleetStatusDatum[];
  from: string;
  to: string;
  tenantName?: string;
  tenantEmail?: string;
  tenantAddress?: string;
  tenantPhone?: string;
  tenantLogoPath?: string;
  generatedByName?: string;
};

type TenantReportBranding = {
  name: string;
  email?: string;
  address?: string;
  phone?: string;
  logoPath?: string;
};

// Report content follows the active UI language (decided in Task 5.4).
const rt = (key: string, opts?: Record<string, unknown>): string => i18n.t(`report:${key}`, opts);

const BRAND = '#1E3A5F';
const LIGHT = '#F1F5F9';
const TEXT_MUTED = '#64748B';
const TEXT_DARK = '#0F172A';

// Header ends at this y position; content starts at CONTENT_Y
const HEADER_H = 35;
export const CONTENT_Y = 41;

export const TABLE_STYLES = {
  headStyles: {
    fillColor: BRAND,
    textColor: '#FFFFFF',
    fontStyle: 'bold' as const,
    fontSize: 8.5,
    cellPadding: 3,
    halign: 'left' as const,
  },
  bodyStyles: { fontSize: 8.5, textColor: TEXT_DARK, halign: 'left' as const },
  alternateRowStyles: { fillColor: LIGHT },
  styles: { cellPadding: 2.8, fontSize: 8.5, lineColor: '#94A3B8' as const, lineWidth: 0.2 },
  margin: { left: 8, right: 8 },
  tableLineColor: '#94A3B8',
  tableLineWidth: 0.3,
};

async function loadLogoDataUrl(src: string): Promise<string> {
  const resp = await fetch(src);
  if (!resp.ok) throw new Error(`logo fetch failed: ${resp.status}`);
  const blob = await resp.blob();
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

// ─── Header ──────────────────────────────────────────────────────────────────
// White background; logo left, company name + subtitle centered, period right.
export function pageHeader(
  doc: jsPDF,
  title: string,
  dateFrom: string,
  dateTo: string,
  tenant: TenantReportBranding,
  logoDataUrl?: string,
) {
  const W = doc.internal.pageSize.getWidth();

  // Logo — top-left, sized to sit flush with the text block
  if (logoDataUrl) {
    doc.addImage(logoDataUrl, 'PNG', 12, 14, 22, 13);
  }

  // Company name — centered, bold, brand colour
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(15);
  doc.setTextColor(BRAND);
  doc.text(tenant.name.toUpperCase(), W / 2, 22, { align: 'center' });

  // Report subtitle — centered, smaller
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10.5);
  doc.setTextColor('#334155');
  doc.text(title, W / 2, 29, { align: 'center' });

  // Optional contact line — centered, muted
  const contact = [tenant.address, tenant.phone].filter(Boolean).join('  |  ');
  if (contact) {
    doc.setFontSize(7);
    doc.setTextColor(TEXT_MUTED);
    doc.text(contact, W / 2, 32, { align: 'center' });
  }

  // REPORT PERIOD block — top-right, aligned to match center content
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(6.5);
  doc.setTextColor(TEXT_MUTED);
  doc.text(rt('common.reportPeriod'), W - 14, 17, { align: 'right' });

  doc.setFontSize(8.5);
  doc.setTextColor(TEXT_DARK);
  doc.text(dateFrom, W - 14, 21, { align: 'right' });

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(TEXT_MUTED);
  doc.text('—', W - 14, 26, { align: 'right' });

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.setTextColor(TEXT_DARK);
  doc.text(dateTo, W - 14, 31, { align: 'right' });

  // Divider
  doc.setDrawColor(BRAND);
  doc.setLineWidth(0.7);
  doc.line(12, HEADER_H, W - 12, HEADER_H);

  doc.setTextColor('#000000');
}

// ─── Section title ────────────────────────────────────────────────────────────
// num adds a "1." prefix; text is rendered uppercase with a light rule below.
export function sectionTitle(doc: jsPDF, text: string, y: number, num?: number): number {
  const W = doc.internal.pageSize.getWidth();
  const label = num === undefined ? text.toUpperCase() : `${num}. ${text.toUpperCase()}`;

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9.5);
  doc.setTextColor(TEXT_DARK);
  doc.text(label, 14, y);

  doc.setDrawColor('#CBD5E1');
  doc.setLineWidth(0.25);
  doc.line(14, y + 2, W - 14, y + 2);

  doc.setTextColor('#000000');
  return y + 9;
}


// ─── Page footer loop ─────────────────────────────────────────────────────────
export function stampFooters(doc: jsPDF, tenant: TenantReportBranding, generatedByName: string) {
  const W = doc.internal.pageSize.getWidth();
  const totalPages = doc.getNumberOfPages();
  const year = new Date().getFullYear();
  const now = formatDateTime(new Date(), {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });

  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    const footerY = doc.internal.pageSize.getHeight() - 6;

    // Light rule above footer
    doc.setDrawColor('#E2E8F0');
    doc.setLineWidth(0.2);
    doc.line(14, footerY - 4, W - 14, footerY - 4);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7);
    doc.setTextColor('#94A3B8');

    doc.text(rt('common.footer', { date: now, name: generatedByName, year, tenant: tenant.name }), W / 2, footerY, { align: 'center' });
    doc.text(rt('common.pageOf', { page: p, total: totalPages }), W - 14, footerY, { align: 'right' });
  }
}

// ─── Analytics PDF export ─────────────────────────────────────────────────────
export async function exportAnalyticsPDF({
  data,
  routePerformance,
  fleetStatus,
  from,
  to,
  tenantName,
  tenantEmail,
  tenantAddress,
  tenantPhone,
  tenantLogoPath,
  generatedByName,
}: ReportInput): Promise<void> {
  const tenant: TenantReportBranding = {
    name: tenantName?.trim() || 'Smart Transport',
    email: tenantEmail?.trim() || undefined,
    address: tenantAddress?.trim() || undefined,
    phone: tenantPhone?.trim() || undefined,
    logoPath: tenantLogoPath?.trim() || undefined,
  };

  let logoDataUrl: string | undefined;
  if (tenant.logoPath) {
    try { logoDataUrl = await loadLogoDataUrl(tenant.logoPath); } catch { /* proceed without logo */ }
  }

  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const REPORT_TITLE = rt('analytics.title');

  pageHeader(doc, REPORT_TITLE, from, to, tenant, logoDataUrl);

  let y = CONTENT_Y;
  let sec = 1;

  y = sectionTitle(doc, rt('analytics.dailyPerformance'), y, sec++);

  autoTable(doc, {
    startY: y,
    head: [[
      rt('analytics.colNum'), rt('analytics.colDate'), rt('analytics.colTrips'),
      rt('analytics.colOnTimePct'), rt('analytics.colAvgDelay'), rt('analytics.colPassengers'),
      rt('analytics.colFuelL'), rt('analytics.colRevenueRwf'),
    ]],
    body: data.daily.map((d, i) => [
      i + 1,
      formatDate(d.date),
      d.totalTrips,
      `${d.onTimePercentage}%`,
      d.avgDelay,
      formatNumber(d.totalPassengers),
      formatNumber(Math.round(d.fuelConsumption)),
      formatNumber(Math.round(d.revenue)),
    ]),
    columnStyles: { 0: { cellWidth: 'wrap' } },
    ...TABLE_STYLES,
  });

  const afterDaily: number = (doc as any).lastAutoTable.finalY + 10;
  if (doc.internal.pageSize.getHeight() - afterDaily < 60) {
    doc.addPage();
    pageHeader(doc, REPORT_TITLE, from, to, tenant, logoDataUrl);
    y = CONTENT_Y;
  } else {
    y = afterDaily;
  }

  y = sectionTitle(doc, rt('analytics.routePerformance'), y, sec++);

  autoTable(doc, {
    startY: y,
    head: [[
      rt('analytics.colNum'), rt('analytics.colRouteNo'), rt('analytics.colRouteName'),
      rt('analytics.colTotalTrips'), rt('analytics.colTotalPassengers'), rt('analytics.colAvgPassPerTrip'),
    ]],
    body: routePerformance.map((r, i) => [
      i + 1,
      r.number,
      r.name,
      r.trips,
      formatNumber(r.passengers),
      r.avgPassengers,
    ]),
    columnStyles: { 0: { cellWidth: 'wrap' } },
    ...TABLE_STYLES,
  });

  const afterRoute: number = (doc as any).lastAutoTable.finalY + 10;
  if (doc.internal.pageSize.getHeight() - afterRoute < 50) {
    doc.addPage();
    pageHeader(doc, REPORT_TITLE, from, to, tenant, logoDataUrl);
    y = CONTENT_Y;
  } else {
    y = afterRoute;
  }

  y = sectionTitle(doc, rt('analytics.fleetStatus'), y, sec++);

  const totalVehicles = fleetStatus.reduce((sum, s) => sum + s.value, 0);

  autoTable(doc, {
    startY: y,
    head: [[rt('analytics.colNum'), rt('analytics.colStatus'), rt('analytics.colCount'), rt('analytics.colPercentage')]],
    body: fleetStatus.map((s, i) => [
      i + 1,
      s.name,
      s.value,
      totalVehicles > 0 ? `${((s.value / totalVehicles) * 100).toFixed(1)}%` : '0%',
    ]),
    foot: [['', rt('analytics.total'), totalVehicles, '100%']],
    footStyles: { fillColor: '#E2E8F0', fontStyle: 'bold', fontSize: 8.5, textColor: TEXT_DARK },
    columnStyles: { 0: { cellWidth: 'wrap' } },
    ...TABLE_STYLES,
  });

  stampFooters(doc, tenant, generatedByName ?? tenant.name);
  doc.save(`${slugify(tenant.name)}-analytics-report-${from}-to-${to}.pdf`);
}

function slugify(value: string): string {
  return (
    value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') ||
    'smart-transport'
  );
}

// ─── Filtered-report PDF export ───────────────────────────────────────────────
type FilteredReportInput = {
  result: FilteredReportResponse;
  dateFrom: string;
  dateTo: string;
  tenantName?: string;
  tenantEmail?: string;
  tenantAddress?: string;
  tenantPhone?: string;
  tenantLogoPath?: string;
  generatedByName?: string;
};

export async function exportFilteredReportPDF({
  result,
  dateFrom,
  dateTo,
  tenantName,
  tenantEmail,
  tenantAddress,
  tenantPhone,
  tenantLogoPath,
  generatedByName,
}: FilteredReportInput): Promise<void> {
  const tenant: TenantReportBranding = {
    name: tenantName?.trim() || 'Smart Transport',
    email: tenantEmail?.trim() || undefined,
    address: tenantAddress?.trim() || undefined,
    phone: tenantPhone?.trim() || undefined,
    logoPath: tenantLogoPath?.trim() || undefined,
  };

  let logoDataUrl: string | undefined;
  if (tenant.logoPath) {
    try { logoDataUrl = await loadLogoDataUrl(tenant.logoPath); } catch { /* no logo */ }
  }

  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

  const titleMap: Record<string, string> = {
    route: rt('filtered.titleRoute'),
    daily: rt('filtered.titleDaily'),
    fleet: rt('filtered.titleFleet'),
    driver: rt('filtered.titleDriver'),
  };
  const title = titleMap[result.reportType] ?? rt('filtered.titleDefault');

  pageHeader(doc, title, dateFrom, dateTo, tenant, logoDataUrl);

  let y = CONTENT_Y;
  y = sectionTitle(doc, title, y, 1);

  if (result.reportType === 'route') {
    const rows = result.data as RouteReportData[];
    autoTable(doc, {
      startY: y,
      head: [[
        rt('filtered.colNum'), rt('filtered.colRouteName'), rt('filtered.colOnTimePct'),
        rt('filtered.colAvgDurationMin'), rt('filtered.colPassengers'), rt('filtered.colUtilisationPct'),
      ]],
      body: rows.map((r, i) => [
        i + 1,
        r.routeName,
        `${(r.onTimeRate ?? 0).toFixed(1)}%`,
        r.avgTripDurationMinutes ?? 0,
        formatNumber(r.totalPassengers ?? 0),
        `${(r.utilisationPercentage ?? 0).toFixed(1)}%`,
      ]),
      columnStyles: { 0: { cellWidth: 'wrap' } },
      ...TABLE_STYLES,
    });
  } else if (result.reportType === 'daily') {
    const rows = result.data as DailyReportData[];
    autoTable(doc, {
      startY: y,
      head: [[
        rt('filtered.colNum'), rt('filtered.colDate'), rt('filtered.colTotalTrips'),
        rt('filtered.colCompleted'), rt('filtered.colCancelled'), rt('filtered.colPassengers'),
      ]],
      body: rows.map((r, i) => [
        i + 1,
        formatDate(r.date),
        r.totalTrips,
        r.completedTrips,
        r.cancelledTrips,
        formatNumber(r.totalPassengers ?? 0),
      ]),
      columnStyles: { 0: { cellWidth: 'wrap' } },
      ...TABLE_STYLES,
    });
  } else if (result.reportType === 'fleet') {
    const rows = result.data as FleetReportData[];
    autoTable(doc, {
      startY: y,
      head: [[
        rt('filtered.colNum'), rt('filtered.colRegistration'), rt('filtered.colUtilisationPct'),
        rt('filtered.colMaintenanceEvents'), rt('filtered.colTotalKm'), rt('filtered.colStatus'),
      ]],
      body: rows.map((r, i) => [
        i + 1,
        r.registrationNumber,
        `${(r.utilisationPercentage ?? 0).toFixed(1)}%`,
        r.maintenanceEvents ?? 0,
        formatNumber(r.totalKm ?? 0),
        r.status,
      ]),
      columnStyles: { 0: { cellWidth: 'wrap' } },
      ...TABLE_STYLES,
    });
  } else {
    const rows = result.data as DriverReportData[];
    autoTable(doc, {
      startY: y,
      head: [[
        rt('filtered.colNum'), rt('filtered.colDriver'), rt('filtered.colTripsCompleted'),
        rt('filtered.colOnTimePct'), rt('filtered.colAvgDurationMin'), rt('filtered.colPassengers'),
      ]],
      body: rows.map((r, i) => [
        i + 1,
        r.driverName,
        r.tripsCompleted ?? 0,
        `${(r.onTimeRate ?? 0).toFixed(1)}%`,
        r.avgTripDurationMinutes ?? 0,
        formatNumber(r.totalPassengers ?? 0),
      ]),
      columnStyles: { 0: { cellWidth: 'wrap' } },
      ...TABLE_STYLES,
    });
  }

  // Row count summary line
  const rowCount = (result.data as unknown[]).length;
  const afterTable: number = (doc as any).lastAutoTable.finalY;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.setTextColor(BRAND);
  doc.text(rt('filtered.totalRecords', { count: rowCount }), 14, afterTable + 8);
  doc.setTextColor('#000000');

  stampFooters(doc, tenant, generatedByName ?? tenant.name);
  doc.save(`${slugify(tenant.name)}-${result.reportType}-report-${dateFrom}-to-${dateTo}.pdf`);
}
