import { Card, CardHeader, CardContent } from '../../ui/card';
import { Skeleton } from '../../ui/skeleton';
import { ErrorMessage } from '../../ui/error-message';

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
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
