import { useTranslation } from 'react-i18next';
import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function AnalyticsLoadingState() {
  const { t } = useTranslation('analytics');
  return <LoadingSpinner message={t('loading')} />;
}

export function AnalyticsErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
