import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader } from '../../ui/card';
import { Skeleton } from '../../ui/skeleton';

export function RouteLoadingState() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-56" />
        <Skeleton className="mt-2 h-4 w-64" />
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-28" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-20" />
              <Skeleton className="mt-2 h-3 w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Skeleton className="h-72 w-full" />
    </div>
  );
}

export function RouteErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Route Management</h1>
        <p className="text-slate-600">Manage bus routes and stops</p>
      </div>
      <Card>
        <CardContent className="flex flex-col items-start gap-4 p-6">
          <div>
            <p className="font-medium text-red-700">Unable to load routes</p>
            <p className="mt-1 text-sm text-slate-600">{error}</p>
          </div>
          <Button onClick={onRetry}>Retry</Button>
        </CardContent>
      </Card>
    </div>
  );
}
