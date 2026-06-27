import { useTranslation } from 'react-i18next';
import { LoadingSpinner } from '../../ui/loading-spinner';
import { ErrorMessage } from '../../ui/error-message';

export function MaintenanceLoadingState() {
  const { t } = useTranslation('maintenance');
  return <LoadingSpinner message={t('loading')} />;
}

export function MaintenanceErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return <ErrorMessage error={error} onRetry={onRetry} />;
}
