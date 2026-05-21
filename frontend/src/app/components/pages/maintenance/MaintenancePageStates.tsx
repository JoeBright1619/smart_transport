import { AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '../../ui/button';
import { Card, CardContent } from '../../ui/card';

export function MaintenanceLoadingState() {
  return (
    <div className="flex min-h-[360px] items-center justify-center">
      <div className="flex items-center gap-2 text-slate-600">
        <Loader2 className="size-5 animate-spin" />
        <span>Loading maintenance...</span>
      </div>
    </div>
  );
}

export function MaintenanceErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <Card>
      <CardContent className="flex min-h-[280px] flex-col items-center justify-center gap-3 text-center">
        <AlertCircle className="size-8 text-red-500" />
        <div>
          <p className="font-medium">Unable to load maintenance records</p>
          <p className="text-sm text-slate-600">{error}</p>
        </div>
        <Button onClick={onRetry}>Retry</Button>
      </CardContent>
    </Card>
  );
}
