import { useTranslation } from 'react-i18next';
import { AlertCircle } from 'lucide-react';
import { Button } from './button';
import { Card, CardContent } from './card';

interface ErrorMessageProps {
  error: string;
  onRetry: () => void;
}

export function ErrorMessage({ error, onRetry }: ErrorMessageProps) {
  const { t } = useTranslation('common');
  return (
    <Card>
      <CardContent className="flex min-h-[280px] flex-col items-center justify-center gap-3 text-center">
        <AlertCircle className="size-8 text-red-500" />
        <div>
          <p className="font-medium">{t('common.somethingWentWrong')}</p>
          <p className="text-sm text-slate-600">{error}</p>
        </div>
        <Button onClick={onRetry}>{t('common.retry')}</Button>
      </CardContent>
    </Card>
  );
}
