import { fetchWithAuth } from './apiClient';

export interface CalendarStatusResponse {
  is_connected: boolean;
  provider?: string;
  expires_at?: string;
}

export const calendarApi = {
  async getConnectUrl(): Promise<{ auth_url: string }> {
    return fetchWithAuth<{ auth_url: string }>('/calendar/connect');
  },

  async getStatus(): Promise<CalendarStatusResponse> {
    return fetchWithAuth<CalendarStatusResponse>('/calendar/status');
  },

  async disconnect(): Promise<{ status: string; disconnected: boolean }> {
    return fetchWithAuth<{ status: string; disconnected: boolean }>('/calendar/disconnect', {
      method: 'DELETE',
    });
  }
};
