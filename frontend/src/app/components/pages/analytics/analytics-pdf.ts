import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { AnalyticsData } from '../../../lib/api-types';
import { formatRevenue } from './analytics-helpers';
import type { RoutePerformanceDatum, FleetStatusDatum } from './analytics-helpers';

type ReportInput = {
  data: AnalyticsData;
  routePerformance: RoutePerformanceDatum[];
  fleetStatus: FleetStatusDatum[];
  from: string;
  to: string;
};

const BRAND = '#1E3A5F';
const LIGHT = '#F1F5F9';

function pageHeader(doc: jsPDF, title: string, dateRange: string) {
  const pageWidth = doc.internal.pageSize.getWidth();

  // Banner
  doc.setFillColor(BRAND);
  doc.rect(0, 0, pageWidth, 26, 'F');

  doc.setTextColor('#FFFFFF');
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('Smart Transport', 14, 11);

  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.text(title, 14, 19);

  doc.setFontSize(8);
  doc.text(`Period: ${dateRange}`, pageWidth - 14, 11, { align: 'right' });
  doc.text(`Generated: ${new Date().toLocaleDateString()}`, pageWidth - 14, 19, { align: 'right' });

  doc.setTextColor('#000000');
}

function sectionTitle(doc: jsPDF, text: string, y: number): number {
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(BRAND);
  doc.text(text, 14, y);
  doc.setDrawColor(BRAND);
  doc.setLineWidth(0.4);
  doc.line(14, y + 1.5, doc.internal.pageSize.getWidth() - 14, y + 1.5);
  doc.setTextColor('#000000');
  return y + 8;
}

function summaryBox(doc: jsPDF, summary: AnalyticsData['summary'], y: number): number {
  const pageWidth = doc.internal.pageSize.getWidth();
  const colW = (pageWidth - 28) / 3;

  const items = [
    ['Total Trips', summary.totalTrips.toLocaleString()],
    ['On-Time Performance', `${summary.onTimePercentage}%`],
    ['Average Delay', `${summary.avgDelay} min`],
    ['Total Passengers', summary.totalPassengers.toLocaleString()],
    ['Total Revenue', formatRevenue(summary.totalRevenue)],
    ['Fuel Consumption', `${summary.totalFuelConsumption.toLocaleString()} L`],
  ];

  items.forEach(([label, value], i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 14 + col * colW;
    const boxY = y + row * 18;

    doc.setFillColor(LIGHT);
    doc.roundedRect(x, boxY, colW - 4, 15, 2, 2, 'F');

    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor('#64748B');
    doc.text(label, x + 4, boxY + 5);

    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor('#0F172A');
    doc.text(value, x + 4, boxY + 12);
  });

  doc.setTextColor('#000000');
  return y + Math.ceil(items.length / 3) * 18 + 4;
}

export function exportAnalyticsPDF({
  data,
  routePerformance,
  fleetStatus,
  from,
  to,
}: ReportInput): void {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const dateRange = `${from} — ${to}`;

  // ── Page 1 ──────────────────────────────────────────────────────────────────
  pageHeader(doc, 'Analytics & Performance Report', dateRange);

  let y = 34;
  y = sectionTitle(doc, 'Summary Metrics', y);
  y = summaryBox(doc, data.summary, y);

  y = sectionTitle(doc, 'Daily Performance', y);

  autoTable(doc, {
    startY: y,
    head: [['Date', 'Trips', 'On-Time %', 'Avg Delay (min)', 'Passengers', 'Fuel (L)', 'Revenue (RWF)']],
    body: data.daily.map((d) => [
      new Date(d.date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
      d.totalTrips,
      `${d.onTimePercentage}%`,
      d.avgDelay,
      d.totalPassengers.toLocaleString(),
      d.fuelConsumption.toLocaleString(),
      d.revenue.toLocaleString(),
    ]),
    headStyles: { fillColor: BRAND, textColor: '#FFFFFF', fontStyle: 'bold', fontSize: 8 },
    bodyStyles: { fontSize: 8 },
    alternateRowStyles: { fillColor: LIGHT },
    margin: { left: 14, right: 14 },
    tableLineColor: '#E2E8F0',
    tableLineWidth: 0.1,
  });

  // ── Route Performance ────────────────────────────────────────────────────────
  // @ts-expect-error jspdf-autotable extends jsPDF at runtime
  const afterDailyTable: number = (doc as any).lastAutoTable.finalY + 10;
  const spaceLeft = doc.internal.pageSize.getHeight() - afterDailyTable;

  if (spaceLeft < 60) {
    doc.addPage();
    pageHeader(doc, 'Analytics & Performance Report', dateRange);
    y = 34;
  } else {
    y = afterDailyTable;
  }

  y = sectionTitle(doc, 'Route Performance', y);

  autoTable(doc, {
    startY: y,
    head: [['Route No.', 'Route Name', 'Total Trips', 'Total Passengers', 'Avg Passengers / Trip']],
    body: routePerformance.map((r) => [
      r.number,
      r.name,
      r.trips,
      r.passengers.toLocaleString(),
      r.avgPassengers,
    ]),
    headStyles: { fillColor: BRAND, textColor: '#FFFFFF', fontStyle: 'bold', fontSize: 8 },
    bodyStyles: { fontSize: 8 },
    alternateRowStyles: { fillColor: LIGHT },
    margin: { left: 14, right: 14 },
    tableLineColor: '#E2E8F0',
    tableLineWidth: 0.1,
  });

  // ── Fleet Status ─────────────────────────────────────────────────────────────
  // @ts-expect-error jspdf-autotable extends jsPDF at runtime
  const afterRouteTable: number = (doc as any).lastAutoTable.finalY + 10;
  const spaceLeft2 = doc.internal.pageSize.getHeight() - afterRouteTable;

  if (spaceLeft2 < 50) {
    doc.addPage();
    pageHeader(doc, 'Analytics & Performance Report', dateRange);
    y = 34;
  } else {
    y = afterRouteTable;
  }

  y = sectionTitle(doc, 'Fleet Status', y);

  const totalVehicles = fleetStatus.reduce((sum, s) => sum + s.value, 0);

  autoTable(doc, {
    startY: y,
    head: [['Status', 'Count', 'Percentage']],
    body: fleetStatus.map((s) => [
      s.name,
      s.value,
      totalVehicles > 0 ? `${((s.value / totalVehicles) * 100).toFixed(1)}%` : '0%',
    ]),
    foot: [['Total', totalVehicles, '100%']],
    headStyles: { fillColor: BRAND, textColor: '#FFFFFF', fontStyle: 'bold', fontSize: 8 },
    bodyStyles: { fontSize: 8 },
    footStyles: { fillColor: '#E2E8F0', fontStyle: 'bold', fontSize: 8 },
    alternateRowStyles: { fillColor: LIGHT },
    margin: { left: 14, right: 14 },
    tableLineColor: '#E2E8F0',
    tableLineWidth: 0.1,
  });

  // ── Footer on every page ─────────────────────────────────────────────────────
  const totalPages = doc.getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    doc.setFontSize(7);
    doc.setTextColor('#94A3B8');
    doc.text(
      `Page ${p} of ${totalPages}  •  Smart Transport Analytics Report`,
      doc.internal.pageSize.getWidth() / 2,
      doc.internal.pageSize.getHeight() - 6,
      { align: 'center' },
    );
  }

  doc.save(`smart-transport-report-${from}-to-${to}.pdf`);
}
