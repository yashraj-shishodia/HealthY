import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { doctorPortalApi } from '../services/doctorPortalApi';
import { Appointment } from '../services/bookingApi';
import { authApi } from '../services/authApi';
import { AISummaryCard } from '../components/AISummaryCard';

export const DoctorDashboard: React.FC = () => {
  const navigate = useNavigate();
  const user = authApi.getCurrentUser();
  const [schedule, setSchedule] = useState<Appointment[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [selectedAppt, setSelectedAppt] = useState<Appointment | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Clinical consultation form states
  const [notes, setNotes] = useState<string>('');
  const [prescription, setPrescription] = useState<string>('');
  const [meds, setMeds] = useState<Array<{ medication_name: string; dosage: string; frequency: string; duration_days: number }>>([
    { medication_name: '', dosage: '', frequency: 'Twice daily', duration_days: 7 }
  ]);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [dashboardError, setDashboardError] = useState<string>('');
  const [modalError, setModalError] = useState<string>('');

  const fetchSchedule = async () => {
    setLoading(true);
    setDashboardError('');
    try {
      const data = await doctorPortalApi.getSchedule(selectedDate);
      setSchedule(data);
    } catch (err: any) {
      console.error(err);
      if (err?.code === 'DOCTOR_PROFILE_NOT_FOUND' || err?.status === 404) {
        setDashboardError('Doctor profile not configured for this account. Please ask an Admin user to create your Doctor Profile in the Admin Dashboard.');
      } else {
        setDashboardError(err.message || 'Failed to load doctor schedule.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedule();
  }, [selectedDate]);

  const handleOpenVisit = (appt: Appointment) => {
    setSelectedAppt(appt);
    setNotes(appt.doctor_notes || '');
    setPrescription(appt.prescription || '');
    setModalError('');
  };

  const handleAddMed = () => {
    setMeds([...meds, { medication_name: '', dosage: '', frequency: 'Twice daily', duration_days: 7 }]);
  };

  const handleCompleteVisit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppt) return;
    if (!notes.trim()) {
      setModalError('Please enter clinical notes before completing the visit.');
      return;
    }

    setSubmitting(true);
    setModalError('');
    try {
      const validMeds = meds.filter(m => m.medication_name.trim() && m.dosage.trim());
      await doctorPortalApi.completeVisit(selectedAppt.id, {
        doctor_notes: notes.trim(),
        prescription: prescription.trim() || undefined,
        medication_instructions: validMeds,
      });
      setSelectedAppt(null);
      await fetchSchedule();
    } catch (err: any) {
      setModalError(err.message || 'Failed to complete visit.');
    } finally {
      setSubmitting(false);
    }
  };

  const completedCount = schedule.filter(a => a.status === 'COMPLETED').length;
  const waitingCount = schedule.filter(a => a.status === 'BOOKED' || a.status === 'HELD').length;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Greeting Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2.1rem', fontWeight: '700', color: '#0f172a', marginBottom: '0.25rem' }}>
            Good morning, Dr. {user?.full_name?.split(' ')[1] || user?.full_name || 'Clinician'}.
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.95rem' }}>
            Here is your clinical overview for today, {selectedDate}.
          </p>
        </div>

        <div>
          <label style={{ fontSize: '0.8rem', color: '#64748b', display: 'block', marginBottom: '0.3rem', fontWeight: '600' }}>Schedule Date:</label>
          <input
            type="date"
            className="input-field"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
        </div>
      </div>

      {dashboardError && (
        <div style={{ padding: '1rem', background: '#fee2e2', border: '1px solid #fca5a5', color: '#991b1b', borderRadius: '12px' }}>
          ⚠️ {dashboardError}
        </div>
      )}

      {/* 3 Metric Stat Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1.5rem', background: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>TOTAL APPOINTMENTS</span>
            <span style={{ fontSize: '1.3rem' }}>📋</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: '800', color: '#0f172a' }}>{schedule.length}</span>
            <span style={{ fontSize: '0.75rem', color: '#10b981', background: '#d1fae5', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontWeight: '700' }}>↑ 2 from yesterday</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem', background: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>PATIENTS WAITING</span>
            <span style={{ fontSize: '1.3rem' }}>⌛</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: '800', color: '#ef4444' }}>{waitingCount}</span>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Avg wait: 14m</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem', background: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>COMPLETED</span>
            <span style={{ fontSize: '1.3rem' }}>✅</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem' }}>
            <span style={{ fontSize: '2.2rem', fontWeight: '800', color: '#10b981' }}>{completedCount}</span>
          </div>
        </div>
      </div>

      {/* Today's Schedule Timeline List */}
      <div className="glass-card" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', color: '#0f172a', fontWeight: '700' }}>Today's Schedule</h2>
          <span style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: '600', cursor: 'pointer' }}>View Calendar ↗</span>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <p style={{ color: '#64748b' }}>Loading schedule...</p>
          </div>
        ) : schedule.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', background: '#f8fafc', borderRadius: '12px' }}>
            <p style={{ color: '#64748b', marginBottom: '1rem' }}>No appointments scheduled for {selectedDate}.</p>
            <button
              onClick={() => {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                setSelectedDate(tomorrow.toISOString().split('T')[0]);
              }}
              className="btn-outline"
              style={{ fontSize: '0.85rem' }}
            >
              📅 Check Tomorrow's Schedule (2026-08-24)
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {schedule.map((appt) => (
              <div key={appt.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1.25rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                  <div style={{ fontWeight: '700', color: '#0f172a', fontSize: '1rem', width: '85px' }}>
                    {appt.start_time.substring(0, 5)} AM
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ width: '42px', height: '42px', borderRadius: '50%', background: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                      👤
                    </div>
                    <div>
                      <div style={{ fontWeight: '700', fontSize: '1rem', color: '#0f172a' }}>
                        {appt.patient_name || 'Patient'}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                        Symptoms: {appt.symptoms || 'General Consultation'}
                      </div>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span className={`badge badge-${appt.status.toLowerCase()}`}>{appt.status}</span>
                  <button
                    onClick={() => handleOpenVisit(appt)}
                    className="btn-navy"
                    style={{ padding: '0.55rem 1.25rem', fontSize: '0.85rem' }}
                  >
                    {appt.status === 'COMPLETED' ? 'Review Chart' : 'Start Session'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Clinical Consultation Modal (Mockup 6) */}
      {selectedAppt && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '1000px', maxHeight: '92vh', overflowY: 'auto', background: '#ffffff' }}>
            
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', color: '#0f172a' }}>Consultation: {selectedAppt.patient_name || 'Patient'}</h2>
                <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.2rem' }}>
                  Scheduled: {selectedAppt.start_time.substring(0, 5)} - {selectedAppt.end_time.substring(0, 5)} | Status: In Progress
                </div>
              </div>
              <button onClick={() => setSelectedAppt(null)} className="btn-outline" style={{ padding: '0.4rem 0.8rem' }}>
                ✕ End Session
              </button>
            </div>

            {modalError && (
              <div style={{ padding: '0.85rem 1rem', marginBottom: '1rem', background: '#fee2e2', border: '1px solid #fca5a5', color: '#991b1b', borderRadius: '12px', fontSize: '0.88rem' }}>
                ⚠️ {modalError}
              </div>
            )}

            {/* 2-Column Consultation Workspace (Mockup 6) */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              
              {/* Left Column: AI Pre-visit & History Snapshot */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <AISummaryCard appointment={selectedAppt} type="pre-visit" />

                <div style={{ padding: '1.25rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: '#0f172a', marginBottom: '0.75rem' }}>
                    🩺 Medical History Snapshot
                  </h4>
                  <div style={{ fontSize: '0.82rem', color: '#475569', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div><strong>Active Conditions:</strong> Essential Hypertension, Type 2 Diabetes</div>
                    <div><strong>Current Medications:</strong> Amlodipine 5mg (1 tablet daily)</div>
                    <div><strong>Allergies:</strong> Penicillin (Rash)</div>
                  </div>
                </div>
              </div>

              {/* Right Column: Clinical Notes & Prescription Builder */}
              <form onSubmit={handleCompleteVisit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.9rem', color: '#0f172a', fontWeight: '700', marginBottom: '0.4rem' }}>
                    Clinical Notes *
                  </label>
                  <textarea
                    required
                    rows={6}
                    className="input-field"
                    placeholder="Enter objective findings, assessment, and care plan here..."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.9rem', color: '#0f172a', fontWeight: '700', marginBottom: '0.4rem' }}>
                    Prescription (Rx)
                  </label>
                  <input
                    type="text"
                    className="input-field"
                    placeholder="e.g., Lisinopril 10mg"
                    value={prescription}
                    onChange={(e) => setPrescription(e.target.value)}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                  <button type="button" onClick={() => setSelectedAppt(null)} className="btn-outline">
                    Cancel
                  </button>
                  <button type="submit" disabled={submitting} className="btn-mint">
                    {submitting ? 'Saving...' : '➢ Issue Prescription & Complete'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
