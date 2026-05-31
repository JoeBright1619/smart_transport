import type { AlertRead } from '../../../lib/api-types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import type { AlertStats, AlertTab } from './alert-helpers';
import { AlertsList } from './AlertsList';

type AlertsTabsProps = {
  activeTab: AlertTab;
  alerts: AlertRead[];
  stats: AlertStats;
  acknowledgingAlertId: string | null;
  page: number;
  pageSize: number;
  total: number;
  onTabChange: (tab: AlertTab) => void;
  onAcknowledge: (alert: AlertRead) => void;
  onPageChange: (page: number) => void;
};

export function AlertsTabs({
  activeTab,
  alerts,
  stats,
  acknowledgingAlertId,
  page,
  pageSize,
  total,
  onTabChange,
  onAcknowledge,
  onPageChange,
}: AlertsTabsProps) {
  const pagination = { page, pageSize, total, onPageChange };

  return (
    <Tabs value={activeTab} onValueChange={(value) => onTabChange(value as AlertTab)} className="space-y-4">
      <TabsList>
        <TabsTrigger value="unacknowledged">Unread ({stats.unread})</TabsTrigger>
        <TabsTrigger value="acknowledged">Acknowledged ({stats.acknowledged})</TabsTrigger>
        <TabsTrigger value="all">All Alerts ({stats.total})</TabsTrigger>
      </TabsList>

      <TabsContent value="unacknowledged">
        <AlertsList
          title="Unread Alerts"
          alerts={alerts}
          acknowledgingAlertId={acknowledgingAlertId}
          onAcknowledge={onAcknowledge}
          pagination={pagination}
        />
      </TabsContent>
      <TabsContent value="acknowledged">
        <AlertsList
          title="Acknowledged Alerts"
          alerts={alerts}
          acknowledgingAlertId={acknowledgingAlertId}
          onAcknowledge={onAcknowledge}
          pagination={pagination}
        />
      </TabsContent>
      <TabsContent value="all">
        <AlertsList
          title="All Alerts"
          alerts={alerts}
          acknowledgingAlertId={acknowledgingAlertId}
          onAcknowledge={onAcknowledge}
          pagination={pagination}
        />
      </TabsContent>
    </Tabs>
  );
}
