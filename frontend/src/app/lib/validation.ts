// Shared field-level validators for auth/signup forms.
// Each returns a localised error message string, or null when the value is valid.
// Kept in sync with the backend rules in app/schemas/validators.py.
import i18n from './i18n';

const EMAIL_RE = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
const PHONE_RE = /^\+?[0-9][0-9\s().-]{6,19}$/;

const v = (key: string) => i18n.t(`errors:validation.${key}`);

export function validateEmail(value: string): string | null {
  const val = value.trim();
  if (!val) return v('emailRequired');
  if (!EMAIL_RE.test(val)) return v('emailInvalid');
  return null;
}

export function validateName(value: string): string | null {
  const val = value.trim();
  if (!val) return v('nameRequired');
  if (val.length < 2) return v('nameTooShort');
  return null;
}

export function validatePassword(value: string): string | null {
  if (value.length < 8) return v('passwordTooShort');
  if (!/[A-Za-z]/.test(value)) return v('passwordNeedsLetter');
  if (!/[0-9]/.test(value)) return v('passwordNeedsNumber');
  return null;
}

// Phone is optional everywhere it's used — an empty value is valid.
export function validatePhone(value: string): string | null {
  const val = value.trim();
  if (!val) return null;
  if (!PHONE_RE.test(val)) return v('phoneInvalid');
  return null;
}
