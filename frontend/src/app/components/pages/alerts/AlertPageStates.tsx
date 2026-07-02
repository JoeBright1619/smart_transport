import { useTranslation } from 'react-i18next';
import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function AlertLoadingState() {
  const { t } = useTranslation('alerts');
  return <LoadingSpinner message={t('loading')} />;
}

export function AlertErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
