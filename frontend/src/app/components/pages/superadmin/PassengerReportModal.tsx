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
import { useTranslation } from 'react-i18next';
import { pageHeader, sectionTitle, stampFooters, TABLE_STYLES, CONTENT_Y } from '../analytics/analytics-pdf';
import i18n from '../../../lib/i18n';
import { formatDate, formatTime, formatDateTime } from '../../../lib/format';

// PDF content follows the active UI language (Task 5.4 decision).
const rt = (key: string, opts?: Record<string, unknown>): string => i18n.t(`report:${key}`, opts);

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

const RWANDA = { name: 'Rwanda Transport System' };

function downloadPdf(report: PassengerUsageReport): void {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const REPORT_TITLE = rt('passenger.title', { name: report.passengerName });

  pageHeader(doc, REPORT_TITLE, report.dateFrom, report.dateTo, RWANDA);

  let y = CONTENT_Y;
  let sec = 1;

  // ── 1. Passenger Summary ──────────────────────────────────────────────────
  y = sectionTitle(doc, rt('passenger.summary'), y, sec++);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor('#0F172A');
  doc.text(rt('passenger.nameEmail', { name: report.passengerName, email: report.email }), 14, y);
  y += 5.5;
  doc.text(
    rt('passenger.boardingsAlightings', { boardings: report.totalBoardings, alightings: report.totalAlightings }),
    14, y,
  );
  y += 10;

  if (report.totalBoardings === 0 && report.totalAlightings === 0) {
    doc.setFontSize(9);
    doc.setTextColor('#64748B');
    doc.text(report.message ?? rt('passenger.noJourneyData'), 14, y);
    stampFooters(doc, RWANDA, 'Rwanda Transport System');
    doc.save(`passenger-report-${report.passengerId}-${report.dateFrom}-to-${report.dateTo}.pdf`);
    return;
  }

  // ── 2. Top Routes ─────────────────────────────────────────────────────────
  if (report.mostUsedRoutes.length > 0) {
    y = sectionTitle(doc, rt('passenger.topRoutes'), y, sec++);
    autoTable(doc, {
      startY: y,
      head: [[rt('passenger.colNum'), rt('passenger.colRoute'), rt('passenger.colBoardings')]],
      body: report.mostUsedRoutes.slice(0, 3).map((r, i) => [i + 1, r.routeName, r.count]),
      columnStyles: { 0: { cellWidth: 'wrap' } },
      ...TABLE_STYLES,
    });
    y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 10;
  }

  // ── 3. Top Stops ──────────────────────────────────────────────────────────
  if (report.mostUsedStops.length > 0) {
    y = sectionTitle(doc, rt('passenger.topStops'), y, sec++);
    autoTable(doc, {
      startY: y,
      head: [[rt('passenger.colNum'), rt('passenger.colStop'), rt('passenger.colBoardings')]],
      body: report.mostUsedStops.slice(0, 3).map((s, i) => [i + 1, s.stopName, s.count]),
      columnStyles: { 0: { cellWidth: 'wrap' } },
      ...TABLE_STYLES,
    });
    y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 10;
  }

  // ── 4. Trip Timeline ──────────────────────────────────────────────────────
  y = sectionTitle(doc, rt('passenger.tripTimeline'), y, sec++);
  autoTable(doc, {
    startY: y,
    head: [[
      rt('passenger.colNum'), rt('passenger.colDate'), rt('passenger.colTime'),
      rt('passenger.colEvent'), rt('passenger.colRoute'), rt('passenger.colStop'),
    ]],
    body: report.timeline.map((ev, i) => [
      i + 1,
      formatDate(ev.recordedAt),
      formatTime(ev.recordedAt),
      ev.eventType === 'boarded' ? rt('passenger.eventBoarded') : rt('passenger.eventAlighted'),
      ev.routeName,
      ev.stopName,
    ]),
    columnStyles: { 0: { cellWidth: 'wrap' } },
    ...TABLE_STYLES,
  });

  stampFooters(doc, RWANDA, 'Rwanda Transport System');
  doc.save(`passenger-report-${report.passengerId}-${report.dateFrom}-to-${report.dateTo}.pdf`);
}

export function PassengerReportModal({ passenger, open, onClose }: Props) {
  const { t } = useTranslation('admin');
  const defaults = defaultDateRange();
  const [dateFrom, setDateFrom] = useState(defaults.from);
  const [dateTo, setDateTo] = useState(defaults.to);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<PassengerUsageReport | null>(null);

  const handleClose = () => { setReport(null); onClose(); };

  const handlePreview = async () => {
    if (!dateFrom || !dateTo) { toast.error(t('report.selectDateRange')); return; }
    if (dateFrom > dateTo) { toast.error(t('report.fromBeforeTo')); return; }
    setLoading(true);
    try {
      const data = await superadminService.getPassengerReport(passenger.id, dateFrom, dateTo);
      setReport(data);
    } catch {
      toast.error(t('report.failedLoad'));
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
          <DialogTitle>{t('report.title')}</DialogTitle>
          <DialogDescription>
            {passenger.fullName}
            {report && ` — ${report.dateFrom} to ${report.dateTo}`}
          </DialogDescription>
        </DialogHeader>

        {!report ? (
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label htmlFor="date-from">{t('report.from')}</Label>
                <Input
                  id="date-from"
                  type="date"
                  value={dateFrom}
                  max={dateTo}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="date-to">{t('report.to')}</Label>
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
              {t('report.previewReport')}
            </Button>
          </div>
        ) : (
          <div className="space-y-4 py-2">
            {/* Summary */}
            <div className="rounded-lg border bg-slate-50 px-4 py-3 text-sm space-y-1">
              <p className="font-medium text-slate-700">{t('report.summary')}</p>
              <div className="flex flex-wrap gap-4 text-slate-600">
                <span>{t('report.boardings')}: <strong>{report.totalBoardings}</strong></span>
                <span>{t('report.alightings')}: <strong>{report.totalAlightings}</strong></span>
              </div>
              {report.message && <p className="text-slate-500 text-xs">{report.message}</p>}
            </div>

            {/* Top routes + stops side by side */}
            {report.mostUsedRoutes.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase mb-1">{t('report.topRoutes')}</p>
                  <table className="w-full text-xs">
                    <thead><tr className="bg-blue-600 text-white"><th className="text-left px-2 py-1">{t('report.route')}</th><th className="px-2 py-1">{t('report.boardingsCol')}</th></tr></thead>
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
                  <p className="text-xs font-semibold text-slate-500 uppercase mb-1">{t('report.topStops')}</p>
                  <table className="w-full text-xs">
                    <thead><tr className="bg-blue-600 text-white"><th className="text-left px-2 py-1">{t('report.stop')}</th><th className="px-2 py-1">{t('report.boardingsCol')}</th></tr></thead>
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
              <p className="text-xs font-semibold text-slate-500 uppercase mb-1">{t('report.tripTimeline')}</p>
              <div className="max-h-96 overflow-y-auto overflow-x-auto rounded border text-xs">
                <table className="min-w-full w-full">
                  <thead className="sticky top-0 bg-blue-600 text-white">
                    <tr>
                      <th className="text-left px-2 py-1">{t('report.dateTime')}</th>
                      <th className="px-2 py-1">{t('report.event')}</th>
                      <th className="text-left px-2 py-1">{t('report.route')}</th>
                      <th className="text-left px-2 py-1">{t('report.stop')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.timeline.map((ev, i) => (
                      <tr key={i} className="even:bg-slate-50">
                        <td className="px-2 py-1 whitespace-nowrap">
                          {formatDateTime(ev.recordedAt)}
                        </td>
                        <td className="px-2 py-1 text-center">
                          <Badge variant={ev.eventType === 'boarded' ? 'default' : 'secondary'} className="text-xs">
                            {ev.eventType === 'boarded' ? t('report.boarded') : t('report.alighted')}
                          </Badge>
                        </td>
                        <td className="px-2 py-1">{ev.routeName}</td>
                        <td className="px-2 py-1">{ev.stopName}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-1">
              <Button variant="outline" size="sm" onClick={() => setReport(null)}>
                <ArrowLeft className="mr-1 size-3.5" /> {t('report.changeDates')}
              </Button>
              <Button size="sm" className="flex-1" onClick={() => { downloadPdf(report); toast.success(t('report.pdfDownloaded')); }}>
                <FileDown className="mr-2 size-4" /> {t('report.downloadPdf')}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
