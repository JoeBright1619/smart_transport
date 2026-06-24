// Shared field-level validators for auth/signup forms.
// Each returns an error message string, or null when the value is valid.
// Kept in sync with the backend rules in app/schemas/validators.py.

const EMAIL_RE = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
const PHONE_RE = /^\+?[0-9][0-9\s().-]{6,19}$/;

export function validateEmail(value: string): string | null {
  const v = value.trim();
  if (!v) return 'Email is required';
  if (!EMAIL_RE.test(v)) return 'Enter a valid email address (e.g. name@example.com)';
  return null;
}

export function validateName(value: string): string | null {
  const v = value.trim();
  if (!v) return 'Full name is required';
  if (v.length < 2) return 'Name must be at least 2 characters';
  return null;
}

export function validatePassword(value: string): string | null {
  if (value.length < 8) return 'Password must be at least 8 characters';
  if (!/[A-Za-z]/.test(value)) return 'Password must contain at least one letter';
  if (!/[0-9]/.test(value)) return 'Password must contain at least one number';
  return null;
}

// Phone is optional everywhere it's used — an empty value is valid.
export function validatePhone(value: string): string | null {
  const v = value.trim();
  if (!v) return null;
  if (!PHONE_RE.test(v)) return 'Enter a valid phone number';
  return null;
}
