import { useTranslation } from 'react-i18next';
import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function ArrivalLoadingState() {
  const { t } = useTranslation('arrivals');
  return <LoadingSpinner message={t('loading')} />;
}

export function ArrivalErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
