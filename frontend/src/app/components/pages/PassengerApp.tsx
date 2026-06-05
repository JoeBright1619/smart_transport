import { useState } from 'react';
import { Bus, Clock, Phone, User } from 'lucide-react';
import { useAuth } from '../../lib/auth-context';
import { PassengerTracking } from './passenger-app/PassengerTracking';
import { PassengerProfileSection } from './passenger-app/PassengerProfileSection';

type Tab = 'tracking' | 'profile';

export function PassengerApp() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>('tracking');

  const isPassenger = user?.role === 'passenger';
  const tenantName = user?.tenantName ?? 'Transport System';
  const tenantContact = user?.tenantPhone ?? user?.tenantEmail;

  return (
    <div className="max-w-5xl mx-auto pb-20 px-4 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold">{tenantName}</h1>
            <p className="text-sm text-blue-100">Passenger service updates</p>
          </div>

          {/* Service info — top right */}
          <div className="text-right text-xs text-blue-100 space-y-1.5">
            <div className="flex items-center gap-1.5 justify-end">
              <Clock className="size-3.5 flex-shrink-0" />
              <span>Mon – Sun: 5:00 AM – 11:00 PM</span>
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
                  <span>Contact your transport operator</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Tabs — profile tab only for passengers */}
        <div className="flex gap-2">
          <button
            onClick={() => setTab('tracking')}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              tab === 'tracking' ? 'bg-white text-blue-700' : 'bg-white/15 text-white hover:bg-white/25'
            }`}
          >
            Live Tracking
          </button>
          {isPassenger && (
            <button
              onClick={() => setTab('profile')}
              className={`flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                tab === 'profile' ? 'bg-white text-blue-700' : 'bg-white/15 text-white hover:bg-white/25'
              }`}
            >
              <User className="size-3.5" />
              My Profile
            </button>
          )}
        </div>
      </div>

      {/* Tab content */}
      {tab === 'tracking' ? <PassengerTracking /> : <PassengerProfileSection />}
    </div>
  );
}
