import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosRequestHeaders,
  type InternalAxiosRequestConfig,
} from 'axios';
import type { ApiResponse, RefreshTokenResponse } from './api-types';

export const ACCESS_TOKEN_KEY = 'st-access-token';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

type ErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
  };
  detail?: {
    error?: {
      code?: string;
      message?: string;
    };
  };
};

export class ApiError extends Error {
  code: string;
  status?: number;

  constructor(message: string, code = 'API_ERROR', status?: number) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }

  static fromAxiosError(error: AxiosError<ErrorEnvelope>): ApiError {
    const status = error.response?.status;
    const envelope = error.response?.data?.error ?? error.response?.data?.detail?.error;

    return new ApiError(
      envelope?.message ?? error.message ?? 'An unexpected API error occurred',
      envelope?.code ?? 'API_ERROR',
      status,
    );
  }
}

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

function redirectToLogin(): void {
  if (window.location.pathname !== '/login') {
    window.location.assign('/login');
  }
}

function setAuthorizationHeader(config: InternalAxiosRequestConfig, token: string): void {
  if (!config.headers) {
    config.headers = new AxiosHeaders() as AxiosRequestHeaders;
  }

  if (config.headers instanceof AxiosHeaders) {
    config.headers.set('Authorization', `Bearer ${token}`);
    return;
  }

  config.headers.Authorization = `Bearer ${token}`;
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

const refreshClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

let refreshPromise: Promise<string> | null = null;

export async function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = refreshClient
      .post<ApiResponse<RefreshTokenResponse>>('/auth/refresh')
      .then((response) => {
        const token = response.data.data.accessToken;
        setStoredToken(token);
        return token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();

  if (token) {
    setAuthorizationHeader(config, token);
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorEnvelope>) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;
    const isUnauthorized = error.response?.status === 401;
    const isRefreshRequest = originalRequest?.url?.includes('/auth/refresh');

    if (isUnauthorized && originalRequest && !originalRequest._retry && !isRefreshRequest) {
      originalRequest._retry = true;

      try {
        const token = await refreshAccessToken();
        setAuthorizationHeader(originalRequest, token);

        return apiClient(originalRequest);
      } catch (refreshError) {
        clearStoredToken();
        redirectToLogin();
        return Promise.reject(
          refreshError instanceof AxiosError
            ? ApiError.fromAxiosError(refreshError as AxiosError<ErrorEnvelope>)
            : refreshError,
        );
      }
    }

    return Promise.reject(ApiError.fromAxiosError(error));
  },
);
