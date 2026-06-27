import React, { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { Bus, Building2, Lock, Mail, Phone, User } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { useAuth } from '../../lib/auth-context';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';
import {
  validateEmail,
  validateName,
  validatePassword,
  validatePhone,
} from '../../lib/validation';

export function TenantRegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { register } = useAuth();

  const [companyName, setCompanyName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [adminFullName, setAdminFullName] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPhone, setAdminPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  type FieldKey =
    | 'companyName'
    | 'contactEmail'
    | 'adminFullName'
    | 'adminEmail'
    | 'adminPhone'
    | 'password'
    | 'confirmPassword';
  const [errors, setErrors] = useState<Partial<Record<FieldKey, string>>>({});

  const passwordsMatch = useMemo(() => {
    if (!password || !confirmPassword) return true;
    return password === confirmPassword;
  }, [password, confirmPassword]);

  const fieldErrorFor = (key: FieldKey): string | undefined => {
    switch (key) {
      case 'companyName':
        return validateName(companyName) ?? undefined;
      case 'contactEmail':
        return validateEmail(contactEmail) ?? undefined;
      case 'adminFullName':
        return validateName(adminFullName) ?? undefined;
      case 'adminEmail':
        return validateEmail(adminEmail) ?? undefined;
      case 'adminPhone':
        return validatePhone(adminPhone) ?? undefined;
      case 'password':
        return validatePassword(password) ?? undefined;
      case 'confirmPassword':
        return password !== confirmPassword ? t('tenantRegister.passwordsDoNotMatch') : undefined;
    }
  };

  const handleBlur = (key: FieldKey) => {
    setErrors((prev) => ({ ...prev, [key]: fieldErrorFor(key) }));
  };

  const validateAll = (): boolean => {
    const keys: FieldKey[] = [
      'companyName',
      'contactEmail',
      'adminFullName',
      'adminEmail',
      'adminPhone',
      'password',
      'confirmPassword',
    ];
    const next: Partial<Record<FieldKey, string>> = {};
    keys.forEach((key) => {
      const err = fieldErrorFor(key);
      if (err) next[key] = err;
    });
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateAll()) {
      toast.error(t('tenantRegister.fixHighlighted'));
      return;
    }

    setLoading(true);
    try {
      const result = await register({
        companyName,
        contactEmail,
        adminFullName,
        adminEmail,
        adminPhone: adminPhone.trim() || undefined,
        password,
      });

      if (!result.ok) {
        if (result.reason === 'email_taken') {
          toast.error(t('tenantRegister.emailTaken'));
          return;
        }
        toast.error(t('tenantRegister.unableToCreate'));
        return;
      }

      toast.success(t('tenantRegister.registered'));
      navigate('/login');
    } catch {
      toast.error(t('tenantRegister.errorOccurred'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 px-4 py-8">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-emerald-50">
            <Bus className="size-8 text-emerald-700" />
          </div>
          <CardTitle className="text-2xl">{t('tenantRegister.title')}</CardTitle>
          <CardDescription>
            {t('tenantRegister.subtitle')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-3">
              <h2 className="text-sm font-medium text-slate-700">{t('tenantRegister.companySection')}</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="companyName">{t('tenantRegister.companyName')}</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="companyName"
                      placeholder={t('tenantRegister.companyNamePlaceholder')}
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      onBlur={() => handleBlur('companyName')}
                      aria-invalid={!!errors.companyName}
                      className="pl-10"
                      required
                    />
                  </div>
                  {errors.companyName && (
                    <p className="text-xs text-red-600">{errors.companyName}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="contactEmail">{t('tenantRegister.contactEmail')}</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="contactEmail"
                      type="email"
                      placeholder={t('tenantRegister.contactEmailPlaceholder')}
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                      onBlur={() => handleBlur('contactEmail')}
                      aria-invalid={!!errors.contactEmail}
                      className="pl-10"
                      required
                    />
                  </div>
                  {errors.contactEmail && (
                    <p className="text-xs text-red-600">{errors.contactEmail}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h2 className="text-sm font-medium text-slate-700">{t('tenantRegister.adminSection')}</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="adminFullName">{t('tenantRegister.adminName')}</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="adminFullName"
                      placeholder={t('tenantRegister.adminNamePlaceholder')}
                      value={adminFullName}
                      onChange={(e) => setAdminFullName(e.target.value)}
                      onBlur={() => handleBlur('adminFullName')}
                      aria-invalid={!!errors.adminFullName}
                      className="pl-10"
                      required
                    />
                  </div>
                  {errors.adminFullName && (
                    <p className="text-xs text-red-600">{errors.adminFullName}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="adminEmail">{t('tenantRegister.adminEmail')}</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="adminEmail"
                      type="email"
                      placeholder={t('tenantRegister.adminEmailPlaceholder')}
                      value={adminEmail}
                      onChange={(e) => setAdminEmail(e.target.value)}
                      onBlur={() => handleBlur('adminEmail')}
                      aria-invalid={!!errors.adminEmail}
                      className="pl-10"
                      required
                    />
                  </div>
                  {errors.adminEmail && (
                    <p className="text-xs text-red-600">{errors.adminEmail}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="adminPhone">{t('tenantRegister.adminPhone')}</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="adminPhone"
                      placeholder={t('tenantRegister.adminPhonePlaceholder')}
                      value={adminPhone}
                      onChange={(e) => setAdminPhone(e.target.value)}
                      onBlur={() => handleBlur('adminPhone')}
                      aria-invalid={!!errors.adminPhone}
                      className="pl-10"
                    />
                  </div>
                  {errors.adminPhone && (
                    <p className="text-xs text-red-600">{errors.adminPhone}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="password">{t('tenantRegister.password')}</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="password"
                    type="password"
                    placeholder={t('tenantRegister.passwordPlaceholder')}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onBlur={() => handleBlur('password')}
                    aria-invalid={!!errors.password}
                    className="pl-10"
                    required
                  />
                </div>
                {errors.password ? (
                  <p className="text-xs text-red-600">{errors.password}</p>
                ) : (
                  <p className="text-xs text-slate-500">
                    {t('tenantRegister.passwordHint')}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">{t('tenantRegister.confirmPassword')}</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder={t('tenantRegister.confirmPasswordPlaceholder')}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    onBlur={() => handleBlur('confirmPassword')}
                    aria-invalid={!passwordsMatch}
                    className="pl-10"
                    required
                  />
                </div>
                {passwordsMatch ? null : (
                  <p className="text-xs text-red-600">{t('tenantRegister.passwordsDoNotMatch')}</p>
                )}
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={loading || !passwordsMatch}>
              {loading ? t('tenantRegister.creatingAccount') : t('tenantRegister.createAccount')}
            </Button>
          </form>

          <div className="mt-6 flex items-center justify-center text-sm text-slate-600">
            <span>{t('tenantRegister.alreadyHaveAccount')}</span>
            <Link to="/login" className="ml-2 font-medium text-emerald-700 hover:underline">
              {t('tenantRegister.backToLogin')}
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
