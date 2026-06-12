import { useEffect, useState } from 'react';
import { Building2, Mail, MapPin, Phone } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { listOperators } from '../../services/passenger.service';
import type { TenantContactRead } from '../../lib/api-types';

const RTS_CONTACT = {
  name: 'Rwanda Transport System',
  description: 'National public transport coordination authority',
  email: 'info@rts.gov.rw',
  phone: '+250 788 000 000',
  address: 'KG 7 Ave, Kigali, Rwanda',
};

export function OperatorsPage() {
  const [operators, setOperators] = useState<TenantContactRead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listOperators()
      .then(setOperators)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-3xl space-y-8 pb-10">
      <div>
        <h1 className="text-2xl font-bold">Transport Operators</h1>
        <p className="text-slate-500">Contact details for the transport authority and registered operators</p>
      </div>

      {/* Rwanda Transport System */}
      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">
          Transport Authority
        </h2>
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-5">
            <div className="flex items-start gap-4">
              <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white">
                <Building2 className="size-6" />
              </div>
              <div className="flex-1 space-y-2">
                <div>
                  <p className="font-semibold text-blue-900">{RTS_CONTACT.name}</p>
                  <p className="text-sm text-blue-600">{RTS_CONTACT.description}</p>
                </div>
                <div className="grid gap-1.5 text-sm text-slate-700 sm:grid-cols-2">
                  <ContactItem icon={<Phone className="size-3.5" />} value={RTS_CONTACT.phone} href={`tel:${RTS_CONTACT.phone}`} />
                  <ContactItem icon={<Mail className="size-3.5" />} value={RTS_CONTACT.email} href={`mailto:${RTS_CONTACT.email}`} />
                  <ContactItem icon={<MapPin className="size-3.5" />} value={RTS_CONTACT.address} className="sm:col-span-2" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Registered operators */}
      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">
          Registered Bus Operators
        </h2>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100" />
            ))}
          </div>
        ) : operators.length === 0 ? (
          <p className="text-sm text-slate-400 italic">No registered operators found.</p>
        ) : (
          <div className="space-y-3">
            {operators.map((op) => (
              <OperatorCard key={op.id} operator={op} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function OperatorCard({ operator }: { operator: TenantContactRead }) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-start gap-4">
          {operator.logoPath ? (
            <img
              src={operator.logoPath}
              alt=""
              className="size-12 shrink-0 rounded-md object-cover"
            />
          ) : (
            <div className="flex size-12 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-400">
              <Building2 className="size-5" />
            </div>
          )}
          <div className="flex-1 min-w-0 space-y-1.5">
            <p className="font-semibold text-slate-800">{operator.name}</p>
            <div className="grid gap-1 text-sm sm:grid-cols-2">
              <ContactItem icon={<Mail className="size-3.5" />} value={operator.contactEmail} href={`mailto:${operator.contactEmail}`} />
              {operator.phone && (
                <ContactItem icon={<Phone className="size-3.5" />} value={operator.phone} href={`tel:${operator.phone}`} />
              )}
              {operator.address && (
                <ContactItem icon={<MapPin className="size-3.5" />} value={operator.address} className="sm:col-span-2" />
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ContactItem({
  icon,
  value,
  href,
  className = '',
}: {
  icon: React.ReactNode;
  value: string;
  href?: string;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-1.5 text-slate-600 ${className}`}>
      <span className="shrink-0 text-slate-400">{icon}</span>
      {href ? (
        <a href={href} className="truncate hover:underline hover:text-slate-800">
          {value}
        </a>
      ) : (
        <span className="truncate">{value}</span>
      )}
    </div>
  );
}
