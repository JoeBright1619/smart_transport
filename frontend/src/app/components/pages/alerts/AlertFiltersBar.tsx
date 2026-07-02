import { useTranslation } from 'react-i18next';
import type { AlertSeverity, AlertType } from '../../../lib/api-types';
import { Card, CardContent } from '../../ui/card';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import {
  alertSeverityOptions,
  alertTypeOptions,
  type AlertFilterValue,
} from './alert-helpers';

type AlertFiltersBarProps = {
  severity: AlertFilterValue<AlertSeverity>;
  type: AlertFilterValue<AlertType>;
  onSeverityChange: (value: AlertFilterValue<AlertSeverity>) => void;
  onTypeChange: (value: AlertFilterValue<AlertType>) => void;
};

export function AlertFiltersBar({
  severity,
  type,
  onSeverityChange,
  onTypeChange,
}: AlertFiltersBarProps) {
  const { t } = useTranslation('alerts');
  return (
    <Card>
      <CardContent className="grid gap-4 pt-6 md:grid-cols-2">
        <div className="space-y-2">
          <Label>{t('severity')}</Label>
          <Select value={severity} onValueChange={onSeverityChange}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {alertSeverityOptions.map((option) => (
                <SelectItem key={option} value={option}>
                  {t(`severity_${option}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>{t('type')}</Label>
          <Select value={type} onValueChange={onTypeChange}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {alertTypeOptions.map((option) => (
                <SelectItem key={option} value={option}>
                  {t(`type_${option}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}
