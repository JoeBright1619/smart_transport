import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { Bus, Lock, Mail, Phone, User } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { useAuth } from '../../lib/auth-context';
import * as authService from '../../services/auth.service';
import { toast } from 'sonner';
import { ApiError } from '../../lib/api-client';

type Step = 1 | 2;

export function RegisterPage() {
  const navigate = useNavigate();
  const { loginFromToken } = useAuth();

  // Step 1 fields
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Step 2 fields
  const [otp, setOtp] = useState('');
  const [countdown, setCountdown] = useState(0);

  const [step, setStep] = useState<Step>(1);
  const [loading, setLoading] = useState(false);

  const passwordsMatch = useMemo(() => {
    if (!password || !confirmPassword) return true;
    return password === confirmPassword;
  }, [password, confirmPassword]);

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (password.length < 8) { toast.error('Password must be at least 8 characters'); return; }
    if (password !== confirmPassword) { toast.error('Passwords do not match'); return; }

    setLoading(true);
    try {
      await authService.registerPassenger({
        fullName,
        email,
        phone: phone.trim() || undefined,
        password,
      });
      setStep(2);
      setCountdown(60);
      toast.success('Check your email for the verification code');
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Registration failed';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await authService.verifyEmail(email, otp);
      loginFromToken(response.accessToken, response.user);
      navigate('/');
    } catch (err) {
      const msg = err instanceof ApiError
        ? (err.data?.error?.message ?? err.message)
        : 'Verification failed';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setLoading(true);
    try {
      await authService.resendOtp(email);
      setCountdown(60);
      toast.success('New verification code sent');
    } catch (err) {
      const msg = err instanceof ApiError
        ? (err.data?.error?.message ?? err.message)
        : 'Could not resend code';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 px-4 py-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-emerald-50">
            <Bus className="size-8 text-emerald-700" />
          </div>
          <CardTitle className="text-2xl">
            {step === 1 ? 'Create your account' : 'Verify your email'}
          </CardTitle>
          <CardDescription>
            {step === 1
              ? 'Sign up as a passenger to track your journeys'
              : `Enter the 6-digit code we sent to ${email}`}
          </CardDescription>
        </CardHeader>

        <CardContent>
          {step === 1 ? (
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="fullName"
                    placeholder="e.g. Alice Mutoni"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="alice@example.rw"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone">Phone (optional)</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="phone"
                    placeholder="+250 7xx xxx xxx"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

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

              <Button type="submit" className="w-full" disabled={loading || !passwordsMatch}>
                {loading ? 'Creating account...' : 'Create Account'}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleVerify} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="otp">Verification Code</Label>
                <Input
                  id="otp"
                  placeholder="000000"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="text-center text-2xl tracking-[0.5em]"
                  maxLength={6}
                  required
                />
                <p className="text-xs text-slate-500">Code expires in 15 minutes</p>
              </div>

              <Button type="submit" className="w-full" disabled={loading || otp.length !== 6}>
                {loading ? 'Verifying...' : 'Verify Email'}
              </Button>

              <div className="text-center text-sm text-slate-600">
                {countdown > 0 ? (
                  <span>Resend code in {countdown}s</span>
                ) : (
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={loading}
                    className="font-medium text-emerald-700 hover:underline disabled:opacity-50"
                  >
                    Resend code
                  </button>
                )}
              </div>

              <div className="text-center text-sm text-slate-600">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="text-slate-500 hover:underline"
                >
                  Use a different email
                </button>
              </div>
            </form>
          )}

          <div className="mt-6 flex items-center justify-center text-sm text-slate-600">
            <span>Already have an account?</span>
            <Link to="/login" className="ml-2 font-medium text-emerald-700 hover:underline">
              Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
