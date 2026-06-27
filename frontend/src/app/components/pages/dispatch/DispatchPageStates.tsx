import { useTranslation } from 'react-i18next';
import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function DispatchLoadingState() {
  const { t } = useTranslation('dispatch');
  return <LoadingSpinner message={t('loading')} />;
}

export function DispatchErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
