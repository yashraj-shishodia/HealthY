import { fetchWithAuth } from './apiClient';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'PATIENT' | 'DOCTOR' | 'ADMIN';
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authApi = {
  async register(data: { email: string; password: string; full_name: string; role: string }): Promise<User> {
    return fetchWithAuth<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async login(data: { email: string; password: string }): Promise<AuthResponse> {
    const res = await fetchWithAuth<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (res.access_token) {
      localStorage.setItem('access_token', res.access_token);
      localStorage.setItem('user', JSON.stringify(res.user));
    }
    return res;
  },

  async getMe(): Promise<User> {
    return fetchWithAuth<User>('/auth/me');
  },

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },

  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }
};
