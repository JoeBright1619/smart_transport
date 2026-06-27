import { useTranslation } from 'react-i18next';
import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function DriverLoadingState() {
  const { t } = useTranslation('drivers');
  return <LoadingSpinner message={t('loading')} />;
}

export function DriverErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
