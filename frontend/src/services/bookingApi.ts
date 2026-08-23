import { fetchWithAuth } from './apiClient';

export interface Appointment {
  id: string;
  doctor_id: string;
  patient_id: string;
  doctor_name?: string;
  patient_name?: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  status: 'HELD' | 'BOOKED' | 'COMPLETED' | 'CANCELLED_BY_PATIENT' | 'CANCELLED_BY_LEAVE';
  hold_expires_at?: string;
  symptoms?: string;
  pre_visit_summary?: string;
  pre_visit_summary_status: 'PENDING' | 'COMPLETED' | 'FAILED';
  urgency?: 'Low' | 'Medium' | 'High';
  chief_complaint?: string;
  suggested_questions?: string[];
  doctor_notes?: string;
  prescription?: string;
  post_visit_summary?: any;
  post_visit_summary_status: 'PENDING' | 'COMPLETED' | 'FAILED';
  patient_calendar_sync_status: 'NONE' | 'PENDING' | 'SYNCED' | 'FAILED';
  doctor_calendar_sync_status: 'NONE' | 'PENDING' | 'SYNCED' | 'FAILED';
  overall_calendar_sync_status: 'NOT_CONNECTED' | 'PENDING' | 'PARTIAL' | 'SYNCED' | 'FAILED';
}

export const bookingApi = {
  async holdSlot(data: { doctor_id: string; appointment_date: string; start_time: string; end_time: string }): Promise<Appointment> {
    return fetchWithAuth<Appointment>('/appointments/hold', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async confirmBooking(data: { doctor_id: string; appointment_date: string; start_time: string; end_time: string; symptoms: string; hold_id?: string; appointment_id?: string }): Promise<Appointment> {
    return fetchWithAuth<Appointment>('/appointments', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getMyAppointments(): Promise<Appointment[]> {
    return fetchWithAuth<Appointment[]>('/appointments/my');
  },

  async getAppointmentDetail(id: string): Promise<Appointment> {
    return fetchWithAuth<Appointment>(`/appointments/${id}`);
  },

  async cancelAppointment(id: string, reason?: string): Promise<Appointment> {
    return fetchWithAuth<Appointment>(`/appointments/${id}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  async rescheduleAppointment(id: string, data: { new_appointment_date: string; new_start_time: string; new_end_time: string }): Promise<Appointment> {
    return fetchWithAuth<Appointment>(`/appointments/${id}/reschedule`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
};
