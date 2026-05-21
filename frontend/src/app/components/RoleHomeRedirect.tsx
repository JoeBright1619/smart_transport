import { Navigate } from 'react-router';
import { useAuth } from '../lib/auth-context';
import { Dashboard } from './pages/Dashboard';

export function RoleHomeRedirect() {
  const { user } = useAuth();

  if (user?.role === 'superadmin') {
    return <Navigate to="/superadmin" replace />;
  }

  return <Dashboard />;
}
