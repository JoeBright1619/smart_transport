import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { Download, Upload, Wand2 } from 'lucide-react';
import type { RouteRead } from '../../../lib/api-types';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../ui/dialog';

function RouteTemplatesDialog({ routes }: { routes: RouteRead[] }) {
  const { t } = useTranslation('routes');
  const templates = useMemo(() => routes.slice(0, 8), [routes]);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">{t('routeTemplates')}</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>{t('routeLibraryTemplates')}</DialogTitle>
          <DialogDescription>
            {t('templatesDesc')}
          </DialogDescription>
        </DialogHeader>
        {templates.length === 0 ? (
          <p className="text-sm text-slate-500">{t('noTemplates')}</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {templates.map((route) => (
              <div key={route.id} className="rounded-lg border p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge style={{ backgroundColor: route.color }} className="text-white">
                        {route.number}
                      </Badge>
                      <p className="font-medium">{route.name}</p>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {t('templateMeta', { stops: route.stops.length, distance: route.distance, duration: route.duration })}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toast.message(t('templateNotWired'))}
                  >
                    {t('use')}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
        <DialogFooter>
          <Button variant="outline">{t('manageTemplates')}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function RouteImportExportDialog() {
  const { t } = useTranslation('routes');
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">{t('importExport')}</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t('importExportTitle')}</DialogTitle>
          <DialogDescription>
            {t('importExportDesc')}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border p-4">
            <p className="flex items-center gap-2 font-medium">
              <Upload className="size-4" />
              {t('importLabel')}
            </p>
            <p className="mt-1 text-sm text-slate-600">{t('uploadHint')}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => toast.message(t('uploadNotWired'))}>
                {t('uploadFile')}
              </Button>
              <Button variant="ghost" onClick={() => toast.message(t('pasteNotWired'))}>
                {t('pasteData')}
              </Button>
            </div>
          </div>
          <div className="rounded-lg border p-4">
            <p className="flex items-center gap-2 font-medium">
              <Download className="size-4" />
              {t('exportLabel')}
            </p>
            <p className="mt-1 text-sm text-slate-600">{t('exportHint')}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => toast.success(t('exportedGeoJson'))}>
                {t('exportGeoJson')}
              </Button>
              <Button variant="outline" onClick={() => toast.success(t('exportedCsv'))}>
                {t('exportCsv')}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function RouteManagementTools({ routes }: { routes: RouteRead[] }) {
  const { t } = useTranslation('routes');
  const suggestions = [
    {
      title: t('suggestHeadwaysTitle'),
      detail: t('suggestHeadwaysDetail'),
    },
    {
      title: t('suggestRecoveryTitle'),
      detail: t('suggestRecoveryDetail'),
    },
    {
      title: t('suggestClusteringTitle'),
      detail: t('suggestClusteringDetail'),
    },
  ];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>{t('routeTools')}</CardTitle>
          <p className="text-sm text-slate-600">{t('routeToolsDesc')}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <RouteTemplatesDialog routes={routes} />
          <RouteImportExportDialog />
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-600">{t('routePerformance')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm text-slate-600">
            <p>- {t('perfDelayHotspots')}</p>
            <p>- {t('perfDwellTime')}</p>
            <p>- {t('perfDemandOverlays')}</p>
            <p>- {t('perfIncidentCorrelation')}</p>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm text-slate-600">
              <Wand2 className="size-4" />
              {t('optimizationSuggestions')}
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            {suggestions.map((suggestion) => (
              <div key={suggestion.title} className="rounded-lg border p-3">
                <p className="text-sm font-medium">{suggestion.title}</p>
                <p className="mt-1 text-xs text-slate-600">{suggestion.detail}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
}
