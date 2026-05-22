import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function MaintenanceLoadingState() {
  return <LoadingSpinner message="Loading maintenance..." />;
}

export function MaintenanceErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
