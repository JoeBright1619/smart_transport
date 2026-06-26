import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import type { PassengerNotification } from '../../lib/api-types';
import { getMyNotifications } from '../../services/passenger.service';
import { MapPin, Building2, ChevronLeft, ChevronRight, Bell } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const PAGE_SIZE = 5;

export function PassengerNotificationsPage() {
  const { t } = useTranslation('passenger');
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<PassengerNotification[]>([]);
  const [page, setPage] = useState(1);

  useEffect(() => {
    const fetch = () => getMyNotifications().then(setNotifications).catch(() => {});
    fetch();
    const id = setInterval(fetch, 30_000);
    return () => clearInterval(id);
  }, []);

  const totalPages = Math.max(1, Math.ceil(notifications.length / PAGE_SIZE));
  const paged = notifications.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="rounded-full p-1.5 hover:bg-slate-100 transition-colors"
        >
          <ChevronLeft className="size-5 text-slate-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold">{t('notifications.title')}</h1>
          <p className="text-slate-500 text-sm">{t('notifications.subtitle')}</p>
        </div>
      </div>

      {notifications.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center space-y-2">
            <Bell className="size-10 text-slate-300 mx-auto" />
            <p className="text-slate-600 font-medium">{t('notifications.emptyTitle')}</p>
            <p className="text-slate-400 text-sm">{t('notifications.emptyBody')}</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-4">
            {paged.map((n) => (
              <Card key={n.stopName}>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <MapPin className="size-4 text-slate-400 shrink-0" />
                    {n.stopName}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {n.arrivals.map((a) => (
                      <div key={a.vehicleId} className="rounded-lg border p-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-sm">{a.registrationNumber}</p>
                            <p className="text-xs text-slate-500">{a.routeName}</p>
                            <div className="flex items-center gap-1.5 mt-1.5">
                              <Badge variant="secondary" className="text-xs">{t('tracking.route', { number: a.routeNumber })}</Badge>
                              <span className="flex items-center gap-1 text-xs text-slate-400">
                                <Building2 className="size-3" />{a.tenantName}
                              </span>
                            </div>
                          </div>
                          <div className="text-right">
                            {a.etaMinutes !== null && a.etaMinutes < 2 ? (
                              <span className="text-green-600 font-bold text-sm">{t('tracking.arrivingNow')}</span>
                            ) : a.etaMinutes !== null ? (
                              <span className="font-bold text-sm">{t('tracking.minutes', { count: a.etaMinutes })}</span>
                            ) : (
                              <span className="text-slate-400 text-sm">{t('tracking.stopped')}</span>
                            )}
                            {a.distanceToStopKm != null && (
                              <p className="text-xs text-slate-500 mt-0.5">{t('tracking.kmAway', { km: a.distanceToStopKm.toFixed(1) })}</p>
                            )}
                          </div>
                        </div>
                        {a.seatingCapacity > 0 && (
                          <div className="mt-2 pt-2 border-t">
                            <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                              <span>{t('tracking.seatsTaken', { current: a.currentOccupancy, total: a.seatingCapacity })}</span>
                              {a.remainingSeats === 0 ? (
                                <span className="font-semibold text-red-600">{t('tracking.busFull')}</span>
                              ) : a.remainingSeats < 10 ? (
                                <span className="font-semibold text-amber-600">{t('tracking.nearlyFullShort')}</span>
                              ) : (
                                <span className="font-semibold text-green-700">{t('tracking.seatsFree', { count: a.remainingSeats })}</span>
                              )}
                            </div>
                            <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${
                                  a.remainingSeats === 0 ? 'bg-red-500' : a.remainingSeats < 10 ? 'bg-amber-400' : 'bg-green-500'
                                }`}
                                style={{ width: `${Math.min(100, (a.currentOccupancy / a.seatingCapacity) * 100)}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="size-4" />
              </Button>
              <span className="text-sm text-slate-600">
                {t('notifications.page', { page, total: totalPages })}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                <ChevronRight className="size-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
