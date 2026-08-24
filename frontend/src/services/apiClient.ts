const envApiBase = (import.meta as any).env?.VITE_API_BASE_URL;
const API_BASE_URL = envApiBase
  ? `${envApiBase.replace(/\/$/, '')}/api`
  : '/api';

export interface APIErrorResponse {
  error: {
    code: string;
    message: string;
  };
}

export async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('access_token');

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (response.status === 401) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    if (window.location.pathname !== '/login' && window.location.pathname !== '/register' && window.location.pathname !== '/') {
      window.location.href = '/login';
    }
  }

  if (!response.ok) {
    const errorMsg = data?.error?.message || data?.detail?.error?.message || (typeof data?.detail === 'string' ? data.detail : null) || 'Invalid request or credentials.';
    const errorCode = data?.error?.code || data?.detail?.error?.code || 'HTTP_ERROR';
    const err = new Error(errorMsg) as Error & { code?: string; status?: number };
    err.code = errorCode;
    err.status = response.status;
    throw err;
  }

  return data as T;
}
