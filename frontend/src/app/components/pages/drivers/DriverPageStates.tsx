import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function DriverLoadingState() {
  return <LoadingSpinner message="Loading drivers..." />;
}

export function DriverErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
