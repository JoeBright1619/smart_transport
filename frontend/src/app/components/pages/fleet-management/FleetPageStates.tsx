import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader } from '../../ui/card';
import { Skeleton } from '../../ui/skeleton';

export function FleetLoadingState() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-56" />
        <Skeleton className="mt-2 h-4 w-80 max-w-full" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-20" />
              <Skeleton className="mt-2 h-3 w-36" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export function FleetErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Fleet Management</h1>
        <p className="text-slate-600">Comprehensive fleet monitoring and control</p>
      </div>
      <Card>
        <CardContent className="flex flex-col items-start gap-4 p-6">
          <div>
            <p className="font-medium text-red-700">Unable to load fleet data</p>
            <p className="mt-1 text-sm text-slate-600">{error}</p>
          </div>
          <Button onClick={onRetry}>Retry</Button>
        </CardContent>
      </Card>
    </div>
  );
}
