import React, { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { Bus, Building2, Lock, Mail, Phone, User } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { useAuth } from '../../lib/auth-context';
import { toast } from 'sonner';

export function RegisterPage() {
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

  const passwordsMatch = useMemo(() => {
    if (!password || !confirmPassword) return true;
    return password === confirmPassword;
  }, [password, confirmPassword]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
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
          toast.error('An account with this email already exists');
          return;
        }
        toast.error('Unable to create account');
        return;
      }

      toast.success('Company registered - please sign in');
      navigate('/login');
    } catch {
      toast.error('An error occurred');
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
          <CardTitle className="text-2xl">Create your account</CardTitle>
          <CardDescription>
            Register your company and first administrator
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-3">
              <h2 className="text-sm font-medium text-slate-700">Company</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="companyName">Company Name</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="companyName"
                      placeholder="e.g. Kigali Express Ltd"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="contactEmail">Company Contact Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="contactEmail"
                      type="email"
                      placeholder="admin@company.rw"
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h2 className="text-sm font-medium text-slate-700">Administrator</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="adminFullName">Admin Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="adminFullName"
                      placeholder="e.g. Jean Claude Mugabo"
                      value={adminFullName}
                      onChange={(e) => setAdminFullName(e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="adminEmail">Admin Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="adminEmail"
                      type="email"
                      placeholder="jean@company.rw"
                      value={adminEmail}
                      onChange={(e) => setAdminEmail(e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="adminPhone">Admin Phone (optional)</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      id="adminPhone"
                      placeholder="+250 7xx xxx xxx"
                      value={adminPhone}
                      onChange={(e) => setAdminPhone(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="Create a password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
                <p className="text-xs text-slate-500">Minimum 8 characters</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Re-enter your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
                {passwordsMatch ? null : (
                  <p className="text-xs text-red-600">Passwords do not match</p>
                )}
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={loading || !passwordsMatch}>
              {loading ? 'Creating account...' : 'Create Account'}
            </Button>
          </form>

          <div className="mt-6 flex items-center justify-center text-sm text-slate-600">
            <span>Already have an account?</span>
            <Link to="/login" className="ml-2 font-medium text-emerald-700 hover:underline">
              Back to login
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
