import { fetchWithAuth } from './apiClient';

export interface DoctorWorkingHours {
  day_of_week: number;
  start_time: string;
  end_time: string;
}

export interface DoctorProfile {
  id: string;
  user_id: string;
  full_name?: string;
  email?: string;
  specialisation: string;
  bio?: string;
  slot_duration_minutes: number;
  working_hours: DoctorWorkingHours[];
  is_active: boolean;
}

export interface Slot {
  start_time: string;
  end_time: string;
  status: 'AVAILABLE' | 'HELD' | 'BOOKED';
}

export interface AvailabilityResponse {
  doctor_id: string;
  appointment_date: string;
  slot_duration_minutes: number;
  is_on_leave: boolean;
  slots: Slot[];
}

export const doctorApi = {
  async listDoctors(specialisation?: string): Promise<DoctorProfile[]> {
    const query = specialisation ? `?specialisation=${encodeURIComponent(specialisation)}` : '';
    return fetchWithAuth<DoctorProfile[]>(`/doctors${query}`);
  },

  async getDoctor(id: string): Promise<DoctorProfile> {
    return fetchWithAuth<DoctorProfile>(`/doctors/${id}`);
  },

  async getAvailability(doctorId: string, date: string): Promise<AvailabilityResponse> {
    return fetchWithAuth<AvailabilityResponse>(`/doctors/${doctorId}/availability?date=${date}`);
  }
};
