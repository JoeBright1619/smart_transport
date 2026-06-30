import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '../../ui/card';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';

type AnalyticsDateRangeProps = {
  from: string;
  to: string;
  onFromChange: (value: string) => void;
  onToChange: (value: string) => void;
};

export function AnalyticsDateRange({
  from,
  to,
  onFromChange,
  onToChange,
}: AnalyticsDateRangeProps) {
  const { t } = useTranslation('analytics');
  return (
    <Card>
      <CardContent className="grid gap-3 p-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="analyticsFrom">{t('dateRange.from')}</Label>
          <Input
            id="analyticsFrom"
            type="date"
            value={from}
            max={to}
            onChange={(event) => onFromChange(event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="analyticsTo">{t('dateRange.to')}</Label>
          <Input
            id="analyticsTo"
            type="date"
            value={to}
            min={from}
            onChange={(event) => onToChange(event.target.value)}
          />
        </div>
      </CardContent>
    </Card>
  );
}
