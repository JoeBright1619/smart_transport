import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { Bus, Lock, Mail } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { useAuth } from '../../lib/auth-context';
import { toast } from 'sonner';
import { validateEmail } from '../../lib/validation';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const { login } = useAuth();
  const navigate = useNavigate();

  const validate = (): boolean => {
    const next: { email?: string; password?: string } = {};
    const emailErr = validateEmail(email);
    if (emailErr) next.email = emailErr;
    if (!password) next.password = 'Password is required';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);

    try {
      const success = await login(email, password);
      if (success) {
        toast.success('Login successful');
        navigate('/');
      } else {
        toast.error('Invalid credentials');
      }
    } catch (error) {
      toast.error('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-emerald-50">
            <Bus className="size-8 text-emerald-700" />
          </div>
          <CardTitle className="text-2xl">Rwanda Transport System</CardTitle>
          <CardDescription>
            Smart Public Transport Tracking & Fleet Management
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                <Input
                  id="email"
                  type="email"
                  placeholder="your.email@transport.rw"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onBlur={() => setErrors((prev) => ({ ...prev, email: validateEmail(email) ?? undefined }))}
                  aria-invalid={!!errors.email}
                  className="pl-10"
                  required
                />
              </div>
              {errors.email && <p className="text-xs text-red-600">{errors.email}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  aria-invalid={!!errors.password}
                  className="pl-10"
                  required
                />
              </div>
              {errors.password && <p className="text-xs text-red-600">{errors.password}</p>}
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-6 space-y-3 text-center text-sm text-slate-600">
            <div className="flex items-center justify-center">
              <span>New here?</span>
              <Link to="/register" className="ml-2 font-medium text-emerald-700 hover:underline">
                Create a passenger account
              </Link>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <div className="flex-1 border-t" />
              <span className="text-xs text-slate-400">or</span>
              <div className="flex-1 border-t" />
            </div>
            <div className="flex items-center justify-center">
              <span>Transport operator?</span>
              <Link to="/register/company" className="ml-2 font-medium text-emerald-700 hover:underline">
                Register your company
              </Link>
            </div>
          </div>

        </CardContent>
      </Card>
    </div>
  );
}
