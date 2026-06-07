import { useState } from 'react';
import { FileDown, Loader2 } from 'lucide-react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { UserRead, PassengerUsageReport } from '../../../lib/api-types';
import * as superadminService from '../../../services/superadmin.service';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
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

function defaultDateRange(): { from: string; to: string } {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 30);
  return {
    from: from.toISOString().slice(0, 10),
    to: to.toISOString().slice(0, 10),
  };
}

function generatePdf(report: PassengerUsageReport): void {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  let y = 14;

  // Header
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
    14,
    y,
  );
  y += 10;

  // Summary
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.text('Summary', 14, y);
  y += 6;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text(`Total boardings: ${report.totalBoardings}`, 14, y);
  y += 6;

  if (report.totalBoardings === 0) {
    doc.text(report.message ?? 'No journey data recorded for this period.', 14, y);
    doc.save(`passenger-report-${report.passengerId}-${report.dateFrom}-to-${report.dateTo}.pdf`);
    return;
  }

  // Most-used routes
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

  // Most-used stops
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

  // Timeline
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.text('Trip Timeline', 14, y);
  y += 4;

  autoTable(doc, {
    startY: y,
    head: [['Date', 'Time', 'Route', 'Stop', 'Status']],
    body: report.timeline.map((t) => {
      const dt = new Date(t.boardedAt);
      return [
        dt.toLocaleDateString(),
        dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        t.routeName,
        t.stopName,
        t.tripStatus,
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

  const handleDownload = async () => {
    if (!dateFrom || !dateTo) {
      toast.error('Select a date range first');
      return;
    }
    setLoading(true);
    try {
      const report = await superadminService.getPassengerReport(
        passenger.id,
        dateFrom,
        dateTo,
      );
      generatePdf(report);
      toast.success('PDF downloaded');
    } catch {
      toast.error('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Passenger Report</DialogTitle>
          <DialogDescription>
            {passenger.fullName} — select a date range and download the PDF.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="date-from">From</Label>
              <Input
                id="date-from"
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="date-to">To</Label>
              <Input
                id="date-to"
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
          </div>

          <Button className="w-full" onClick={() => void handleDownload()} disabled={loading}>
            {loading ? (
              <Loader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <FileDown className="mr-2 size-4" />
            )}
            Download PDF
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
