import { useState } from 'react';
import { ArrowLeft, FileDown, Loader2 } from 'lucide-react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { UserRead, PassengerUsageReport } from '../../../lib/api-types';
import * as superadminService from '../../../services/superadmin.service';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Badge } from '../../ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../../ui/dialog';
import { toast } from 'sonner';

interface Props {
  passenger: UserRead;
  open: boolean;
  onClose: () => void;
}

function defaultDateRange() {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 30);
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

function downloadPdf(report: PassengerUsageReport): void {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  let y = 14;

  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('Smart Transport — Passenger Usage Report', pageWidth / 2, y, { align: 'center' });
  y += 10;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text(`Passenger: ${report.passengerName}  |  Email: ${report.email}`, 14, y);
  y += 6;
  doc.text(
    `Period: ${report.dateFrom} to ${report.dateTo}  |  Generated: ${new Date(report.generatedAt).toLocaleString()}`,
    14, y,
  );
  y += 10;

  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.text('Summary', 14, y);
  y += 6;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text(`Boardings: ${report.totalBoardings}   Alightings: ${report.totalAlightings}`, 14, y);
  y += 6;

  if (report.totalBoardings === 0 && report.totalAlightings === 0) {
    doc.text(report.message ?? 'No journey data recorded for this period.', 14, y);
    doc.save(`passenger-report-${report.passengerId}-${report.dateFrom}-to-${report.dateTo}.pdf`);
    return;
  }

  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.text('Top Routes', 14, y);
  y += 4;
  autoTable(doc, {
    startY: y,
    head: [['Route', 'Boardings']],
    body: report.mostUsedRoutes.slice(0, 3).map((r) => [r.routeName, String(r.count)]),
    theme: 'striped',
    styles: { fontSize: 9 },
    headStyles: { fillColor: [37, 99, 235] },
    margin: { left: 14, right: 14 },
  });
  y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;

  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.text('Top Stops', 14, y);
  y += 4;
  autoTable(doc, {
    startY: y,
    head: [['Stop', 'Boardings']],
    body: report.mostUsedStops.slice(0, 3).map((s) => [s.stopName, String(s.count)]),
    theme: 'striped',
    styles: { fontSize: 9 },
    headStyles: { fillColor: [37, 99, 235] },
    margin: { left: 14, right: 14 },
  });
  y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;

  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.text('Trip Timeline', 14, y);
  y += 4;
  autoTable(doc, {
    startY: y,
    head: [['Date', 'Time', 'Event', 'Route', 'Stop']],
    body: report.timeline.map((t) => {
      const dt = new Date(t.recordedAt);
      return [
        dt.toLocaleDateString(),
        dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        t.eventType === 'boarded' ? 'Boarded' : 'Alighted',
        t.routeName,
        t.stopName,
      ];
    }),
    theme: 'striped',
    styles: { fontSize: 8 },
    headStyles: { fillColor: [37, 99, 235] },
    margin: { left: 14, right: 14 },
  });

  doc.save(`passenger-report-${report.passengerId}-${report.dateFrom}-to-${report.dateTo}.pdf`);
}

export function PassengerReportModal({ passenger, open, onClose }: Props) {
  const defaults = defaultDateRange();
  const [dateFrom, setDateFrom] = useState(defaults.from);
  const [dateTo, setDateTo] = useState(defaults.to);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<PassengerUsageReport | null>(null);

  const handleClose = () => { setReport(null); onClose(); };

  const handlePreview = async () => {
    if (!dateFrom || !dateTo) { toast.error('Select a date range first'); return; }
    if (dateFrom > dateTo) { toast.error('"From" date must be on or before "To" date'); return; }
    setLoading(true);
    try {
      const data = await superadminService.getPassengerReport(passenger.id, dateFrom, dateTo);
      setReport(data);
    } catch {
      toast.error('Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) handleClose(); }}>
      <DialogContent className={report
        ? 'w-[95vw] max-w-5xl max-h-[92vh] overflow-y-auto'
        : 'w-[95vw] max-w-sm'
      }>
        <DialogHeader>
          <DialogTitle>Passenger Report</DialogTitle>
          <DialogDescription>
            {passenger.fullName}
            {report && ` — ${report.dateFrom} to ${report.dateTo}`}
          </DialogDescription>
        </DialogHeader>

        {!report ? (
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label htmlFor="date-from">From</Label>
                <Input
                  id="date-from"
                  type="date"
                  value={dateFrom}
                  max={dateTo}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="date-to">To</Label>
                <Input
                  id="date-to"
                  type="date"
                  value={dateTo}
                  min={dateFrom}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>
            </div>
            <Button className="w-full" onClick={() => void handlePreview()} disabled={loading}>
              {loading ? <Loader2 className="mr-2 size-4 animate-spin" /> : null}
              Preview Report
            </Button>
          </div>
        ) : (
          <div className="space-y-4 py-2">
            {/* Summary */}
            <div className="rounded-lg border bg-slate-50 px-4 py-3 text-sm space-y-1">
              <p className="font-medium text-slate-700">Summary</p>
              <div className="flex flex-wrap gap-4 text-slate-600">
                <span>Boardings: <strong>{report.totalBoardings}</strong></span>
                <span>Alightings: <strong>{report.totalAlightings}</strong></span>
              </div>
              {report.message && <p className="text-slate-500 text-xs">{report.message}</p>}
            </div>

            {/* Top routes + stops side by side */}
            {report.mostUsedRoutes.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase mb-1">Top Routes</p>
                  <table className="w-full text-xs">
                    <thead><tr className="bg-blue-600 text-white"><th className="text-left px-2 py-1">Route</th><th className="px-2 py-1">Boardings</th></tr></thead>
                    <tbody>
                      {report.mostUsedRoutes.slice(0, 3).map((r) => (
                        <tr key={r.routeName} className="even:bg-slate-50">
                          <td className="px-2 py-1">{r.routeName}</td>
                          <td className="px-2 py-1 text-center">{r.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase mb-1">Top Stops</p>
                  <table className="w-full text-xs">
                    <thead><tr className="bg-blue-600 text-white"><th className="text-left px-2 py-1">Stop</th><th className="px-2 py-1">Boardings</th></tr></thead>
                    <tbody>
                      {report.mostUsedStops.slice(0, 3).map((s) => (
                        <tr key={s.stopName} className="even:bg-slate-50">
                          <td className="px-2 py-1">{s.stopName}</td>
                          <td className="px-2 py-1 text-center">{s.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Timeline */}
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase mb-1">Trip Timeline</p>
              <div className="max-h-96 overflow-y-auto overflow-x-auto rounded border text-xs">
                <table className="min-w-full w-full">
                  <thead className="sticky top-0 bg-blue-600 text-white">
                    <tr>
                      <th className="text-left px-2 py-1">Date & Time</th>
                      <th className="px-2 py-1">Event</th>
                      <th className="text-left px-2 py-1">Route</th>
                      <th className="text-left px-2 py-1">Stop</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.timeline.map((t, i) => (
                      <tr key={i} className="even:bg-slate-50">
                        <td className="px-2 py-1 whitespace-nowrap">
                          {new Date(t.recordedAt).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                        </td>
                        <td className="px-2 py-1 text-center">
                          <Badge variant={t.eventType === 'boarded' ? 'default' : 'secondary'} className="text-xs">
                            {t.eventType === 'boarded' ? 'Boarded' : 'Alighted'}
                          </Badge>
                        </td>
                        <td className="px-2 py-1">{t.routeName}</td>
                        <td className="px-2 py-1">{t.stopName}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-1">
              <Button variant="outline" size="sm" onClick={() => setReport(null)}>
                <ArrowLeft className="mr-1 size-3.5" /> Change Dates
              </Button>
              <Button size="sm" className="flex-1" onClick={() => { downloadPdf(report); toast.success('PDF downloaded'); }}>
                <FileDown className="mr-2 size-4" /> Download PDF
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
