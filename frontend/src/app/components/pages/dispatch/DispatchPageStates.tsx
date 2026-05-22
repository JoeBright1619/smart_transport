import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function DispatchLoadingState() {
  return <LoadingSpinner message="Loading dispatch..." />;
}

export function DispatchErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
