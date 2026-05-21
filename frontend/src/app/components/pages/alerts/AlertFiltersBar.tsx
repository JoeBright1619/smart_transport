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
  return (
    <Card>
      <CardContent className="grid gap-4 pt-6 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Severity</Label>
          <Select value={severity} onValueChange={onSeverityChange}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {alertSeverityOptions.map((option) => (
                <SelectItem key={option} value={option}>
                  {label(option)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Type</Label>
          <Select value={type} onValueChange={onTypeChange}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {alertTypeOptions.map((option) => (
                <SelectItem key={option} value={option}>
                  {label(option)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}

function label(value: string): string {
  return value
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}
