import i18n from './i18n';

// Maps the active i18n language to a BCP-47 locale tag for Intl formatting.
// en → 'en-GB', rw → 'rw-RW'. Runtimes lacking 'rw-RW' data fall back to their
// default locale silently (no throw), so no explicit guard is needed here.
export function localeTag(): string {
  const base = (i18n.language || 'en').split('-')[0];
  return base === 'rw' ? 'rw-RW' : 'en-GB';
}

type DateInput = string | number | Date;

function toDate(value: DateInput): Date {
  return value instanceof Date ? value : new Date(value);
}

export function formatDate(
  value: DateInput,
  options: Intl.DateTimeFormatOptions = { day: '2-digit', month: 'short', year: 'numeric' },
): string {
  try {
    return toDate(value).toLocaleDateString(localeTag(), options);
  } catch {
    return toDate(value).toLocaleDateString('en-GB', options);
  }
}

export function formatTime(
  value: DateInput,
  options: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit' },
): string {
  try {
    return toDate(value).toLocaleTimeString(localeTag(), options);
  } catch {
    return toDate(value).toLocaleTimeString('en-GB', options);
  }
}

export function formatDateTime(
  value: DateInput,
  options: Intl.DateTimeFormatOptions = { dateStyle: 'short', timeStyle: 'short' },
): string {
  try {
    return toDate(value).toLocaleString(localeTag(), options);
  } catch {
    return toDate(value).toLocaleString('en-GB', options);
  }
}

export function formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
  try {
    return value.toLocaleString(localeTag(), options);
  } catch {
    return value.toLocaleString('en-GB', options);
  }
}
