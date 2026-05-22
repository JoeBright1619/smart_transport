import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function AnalyticsLoadingState() {
  return <LoadingSpinner message="Loading analytics..." />;
}

export function AnalyticsErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
