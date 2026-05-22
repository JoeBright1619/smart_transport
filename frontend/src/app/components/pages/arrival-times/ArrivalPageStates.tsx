import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function ArrivalLoadingState() {
  return <LoadingSpinner message="Loading stops..." />;
}

export function ArrivalErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
