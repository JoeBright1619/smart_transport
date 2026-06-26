import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enCommon from '../locales/en/common.json';
import rwCommon from '../locales/rw/common.json';
import enErrors from '../locales/en/errors.json';
import rwErrors from '../locales/rw/errors.json';

// localStorage key the chosen language is persisted under — mirrors the
// `st-access-token` convention in api-client.ts.
export const LANG_KEY = 'st-lang';

export const SUPPORTED_LANGUAGES = ['en', 'rw'] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { common: enCommon, errors: enErrors },
      rw: { common: rwCommon, errors: rwErrors },
    },
    fallbackLng: 'en',
    supportedLngs: SUPPORTED_LANGUAGES,
    defaultNS: 'common',
    ns: ['common', 'errors'],
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: LANG_KEY,
      caches: ['localStorage'],
    },
    interpolation: {
      escapeValue: false, // React already escapes values
    },
  });

export default i18n;
