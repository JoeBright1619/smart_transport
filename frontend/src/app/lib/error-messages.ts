import i18n from './i18n';
import { ApiError } from './api-client';

// Resolve a user-facing, localised message for an error surfaced to the UI.
//
// Server errors arrive as English strings, but each carries a stable
// `ApiError.code`. We translate by code so messages follow the active language.
// Codes with a single, stable meaning (auth/OTP flow) live in the `errors`
// namespace. Codes reused across many situations (CONFLICT, NOT_FOUND, …) are
// intentionally NOT translated here — for those we fall back to the server's own
// specific message rather than flatten them into one vague string. Fully
// localising those would require message keys on the backend (future work).
export function messageForError(error: unknown): string {
  if (error instanceof ApiError) {
    const key = `errors:${error.code}`;
    if (i18n.exists(key)) {
      return i18n.t(key);
    }
    if (error.message) {
      return error.message;
    }
  }
  return i18n.t('errors:DEFAULT');
}
