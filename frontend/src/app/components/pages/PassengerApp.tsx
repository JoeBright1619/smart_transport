import { useState } from 'react';
import { BarChart2, Bus, Clock, History, Phone, User } from 'lucide-react';
import { Link } from 'react-router';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../lib/auth-context';
import { PassengerTracking } from './passenger-app/PassengerTracking';
import { PassengerProfileSection } from './passenger-app/PassengerProfileSection';
import { PassengerStats } from './passenger-app/PassengerStats';
import { PassengerTrips } from './passenger-app/PassengerTrips';

type Tab = 'tracking' | 'trips' | 'stats' | 'profile';

export function PassengerApp() {
  const { t } = useTranslation('passenger');
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>('tracking');

  const isPassenger = user?.role === 'passenger';
  const tenantName = user?.tenantName ?? t('app.defaultTenant');
  const tenantContact = user?.tenantPhone ?? user?.tenantEmail;

  return (
    <div className="max-w-5xl mx-auto pb-20 px-4 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold">{tenantName}</h1>
            <p className="text-sm text-blue-100">{t('app.subtitle')}</p>
          </div>

          {/* Service info — top right */}
          <div className="text-right text-xs text-blue-100 space-y-1.5">
            <div className="flex items-center gap-1.5 justify-end">
              <Clock className="size-3.5 flex-shrink-0" />
              <span>{t('app.serviceHours')}</span>
            </div>
            <div className="flex items-center gap-1.5 justify-end">
              {tenantContact ? (
                <>
                  <Phone className="size-3.5 flex-shrink-0" />
                  <span>{tenantContact}</span>
                </>
              ) : (
                <>
                  <Bus className="size-3.5 flex-shrink-0" />
                  <Link
                    to="/operators"
                    className="underline underline-offset-2 hover:text-white transition-colors"
                  >
                    {t('app.viewOperators')}
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Tabs — passenger-only tabs for trips and profile */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setTab('tracking')}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              tab === 'tracking' ? 'bg-white text-blue-700' : 'bg-white/15 text-white hover:bg-white/25'
            }`}
          >
            {t('app.liveTracking')}
          </button>
          {isPassenger && (
            <button
              onClick={() => setTab('trips')}
              className={`flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                tab === 'trips' ? 'bg-white text-blue-700' : 'bg-white/15 text-white hover:bg-white/25'
              }`}
            >
              <History className="size-3.5" />
              {t('app.myTrips')}
            </button>
          )}
          {isPassenger && (
            <button
              onClick={() => setTab('stats')}
              className={`flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                tab === 'stats' ? 'bg-white text-blue-700' : 'bg-white/15 text-white hover:bg-white/25'
              }`}
            >
              <BarChart2 className="size-3.5" />
              {t('app.myStats')}
            </button>
          )}
          {isPassenger && (
            <button
              onClick={() => setTab('profile')}
              className={`flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                tab === 'profile' ? 'bg-white text-blue-700' : 'bg-white/15 text-white hover:bg-white/25'
              }`}
            >
              <User className="size-3.5" />
              {t('app.myProfile')}
            </button>
          )}
        </div>
      </div>

      {/* Tab content */}
      {tab === 'tracking' && <PassengerTracking />}
      {tab === 'trips' && <PassengerTrips />}
      {tab === 'stats' && <PassengerStats />}
      {tab === 'profile' && <PassengerProfileSection />}
    </div>
  );
}
