import { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useAuth } from '../../lib/auth-context';
import { MainLayout } from './MainLayout';

export function ProtectedLayout() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) {
    return null;
  }

  return <MainLayout />;
}
