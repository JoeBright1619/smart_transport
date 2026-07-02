import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate, useSearchParams } from 'react-router';
import { Bus, CheckCircle, Eye, EyeOff, KeyRound } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { acceptInvite } from '../../services/users.service';
import { toast } from 'sonner';

export function AcceptInvitePage() {
  const { t } = useTranslation('common');
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') ?? '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const mismatch = confirmPassword.length > 0 && newPassword !== confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error(t('acceptInvite.mismatch'));
      return;
    }
    if (!token) {
      toast.error(t('acceptInvite.tokenMissing'));
      return;
    }
    setLoading(true);
    try {
      await acceptInvite({ token, newPassword });
      setDone(true);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : t('acceptInvite.failActivate');
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-xl text-red-600">{t('acceptInvite.invalidTitle')}</CardTitle>
            <CardDescription>
              {t('acceptInvite.invalidDesc')}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Link to="/login">
              <Button variant="outline">{t('acceptInvite.backToLogin')}</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (done) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-emerald-50">
              <CheckCircle className="size-8 text-emerald-600" />
            </div>
            <CardTitle className="text-2xl">{t('acceptInvite.activatedTitle')}</CardTitle>
            <CardDescription>
              {t('acceptInvite.activatedDesc')}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Button onClick={() => navigate('/login')} className="w-full">
              {t('acceptInvite.goToLogin')}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-emerald-50">
            <Bus className="size-8 text-emerald-700" />
          </div>
          <CardTitle className="text-2xl">{t('acceptInvite.title')}</CardTitle>
          <CardDescription>{t('acceptInvite.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="new-password">{t('acceptInvite.newPassword')}</Label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-2.5 size-4 text-slate-400" />
                <Input
                  id="new-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder={t('acceptInvite.atLeast8')}
                  className="pl-9 pr-9"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
                <button
                  type="button"
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                  onClick={() => setShowPassword((p) => !p)}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="confirm-password">{t('acceptInvite.confirmPassword')}</Label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-2.5 size-4 text-slate-400" />
                <Input
                  id="confirm-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder={t('acceptInvite.repeatPassword')}
                  className={`pl-9 ${mismatch ? 'border-red-400 focus-visible:ring-red-400' : ''}`}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
              {mismatch && (
                <p className="text-xs text-red-500">{t('acceptInvite.mismatch')}</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={loading || mismatch}>
              {loading ? t('acceptInvite.activating') : t('acceptInvite.activateAccount')}
            </Button>
          </form>

          <p className="mt-4 text-center text-sm text-slate-500">
            {t('acceptInvite.alreadyHaveAccount')}{' '}
            <Link to="/login" className="font-medium text-slate-700 hover:underline">
              {t('acceptInvite.logIn')}
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
