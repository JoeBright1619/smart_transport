import { Navigate } from 'react-router';
import { useAuth } from '../lib/auth-context';

export function SuperadminRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  if (user?.role !== 'superadmin') {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
