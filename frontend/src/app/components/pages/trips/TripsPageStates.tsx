import { useTranslation } from 'react-i18next';
import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function TripsLoadingState() {
  const { t } = useTranslation('trips');
  return <LoadingSpinner message={t('loading')} />;
}

export function TripsErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
