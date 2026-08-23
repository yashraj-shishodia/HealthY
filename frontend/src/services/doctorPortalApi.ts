import { fetchWithAuth } from './apiClient';
import { Appointment } from './bookingApi';

export interface CompleteVisitPayload {
  doctor_notes: string;
  prescription?: string;
  medication_instructions?: Array<{
    medication_name: string;
    dosage: string;
    frequency: string;
    duration_days: number;
  }>;
}

export const doctorPortalApi = {
  async getSchedule(date?: string, status?: string): Promise<Appointment[]> {
    const params = new URLSearchParams();
    if (date) params.append('date', date);
    if (status) params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    return fetchWithAuth<Appointment[]>(`/doctor/appointments${query}`);
  },

  async getAppointmentDetail(id: string): Promise<Appointment> {
    return fetchWithAuth<Appointment>(`/doctor/appointments/${id}`);
  },

  async completeVisit(id: string, payload: CompleteVisitPayload): Promise<Appointment> {
    return fetchWithAuth<Appointment>(`/doctor/appointments/${id}/complete`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
};
