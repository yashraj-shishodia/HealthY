import { fetchWithAuth } from './apiClient';
import { DoctorProfile } from './doctorApi';

export interface CreateDoctorPayload {
  email: string;
  password: string;
  full_name: string;
  specialisation: string;
  bio?: string;
  slot_duration_minutes: number;
  working_hours: Array<{
    day_of_week: number;
    start_time: string;
    end_time: string;
  }>;
}

export interface AddLeavePayload {
  leave_date: string;
  reason?: string;
}

export const adminPortalApi = {
  async createDoctor(payload: CreateDoctorPayload): Promise<DoctorProfile> {
    return fetchWithAuth<DoctorProfile>('/admin/doctors', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async addDoctorLeave(doctorId: string, payload: AddLeavePayload): Promise<any> {
    return fetchWithAuth<any>(`/admin/doctors/${doctorId}/leave`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async revokeDoctorLeave(doctorId: string, leaveDate: string): Promise<any> {
    return fetchWithAuth<any>(`/admin/doctors/${doctorId}/leave/${leaveDate}`, {
      method: 'DELETE',
    });
  }
};
