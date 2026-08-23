import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { bookingApi } from '../services/bookingApi';
import { doctorApi, DoctorProfile, Slot } from '../services/doctorApi';
import { formatDoctorName } from '../utils/formatters';

export const BookAppointmentPage: React.FC = () => {
  const { doctorId } = useParams<{ doctorId: string }>();
  const navigate = useNavigate();

  const [doctor, setDoctor] = useState<DoctorProfile | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [symptoms, setSymptoms] = useState<string>('');
  const [step, setStep] = useState<number>(2);
  const [heldAppointmentId, setHeldAppointmentId] = useState<string | null>(null);
  const [holdExpiresAt, setHoldExpiresAt] = useState<string | null>(null);
  const [countdown, setCountdown] = useState<string>('05:00');
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDocAndSlots = async () => {
      if (!doctorId) return;
      try {
        const docs = await doctorApi.listDoctors();
        const doc = docs.find((d: DoctorProfile) => d.id === doctorId);
        if (doc) setDoctor(doc);

        const avail = await doctorApi.getAvailability(doctorId, selectedDate);
        setSlots(avail.slots || []);
      } catch (err: any) {
        setError(err.message || 'Failed to load doctor slots.');
      } finally {
        setLoading(false);
      }
    };
    fetchDocAndSlots();
  }, [doctorId, selectedDate]);

  useEffect(() => {
    if (!holdExpiresAt) return;
    const interval = setInterval(() => {
      const diff = new Date(holdExpiresAt).getTime() - new Date().getTime();
      if (diff <= 0) {
        setCountdown('EXPIRED');
        clearInterval(interval);
      } else {
        const mins = Math.floor(diff / 60000);
        const secs = Math.floor((diff % 60000) / 1000);
        setCountdown(`${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [holdExpiresAt]);

  const handleHoldSlot = async (slot: Slot) => {
    if (!doctorId) return;
    setError('');
    try {
      const appt = await bookingApi.holdSlot({
        doctor_id: doctorId,
        appointment_date: selectedDate,
        start_time: slot.start_time,
        end_time: slot.end_time,
      });
      setSelectedSlot(slot);
      setHeldAppointmentId(appt.id);
      setHoldExpiresAt(appt.hold_expires_at ?? null);
      setStep(3);
    } catch (err: any) {
      setError(err.message || 'Failed to reserve slot.');
    }
  };

  const handleConfirmBooking = async () => {
    if (!doctorId || !selectedSlot) return;
    setSubmitting(true);
    setError('');
    try {
      const appt = await bookingApi.confirmBooking({
        doctor_id: doctorId,
        appointment_date: selectedDate,
        start_time: selectedSlot.start_time,
        end_time: selectedSlot.end_time,
        symptoms: symptoms.trim() || 'General consultation request',
        appointment_id: heldAppointmentId ?? undefined,
        hold_id: heldAppointmentId ?? undefined,
      });
      navigate(`/patient/appointments/${appt.id}`);
    } catch (err: any) {
      setError(err.message || 'Booking confirmation failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '5rem' }}>
        <p style={{ color: '#64748b' }}>Loading appointment schedule...</p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1.5rem', margin: '1rem 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontWeight: '700', fontSize: '0.85rem' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: '#10b981', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>✓</div>
          01 Doctor
        </div>
        <div style={{ width: '40px', height: '2px', background: step >= 2 ? '#10b981' : '#e2e8f0' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: step >= 2 ? '#10b981' : '#94a3b8', fontWeight: '700', fontSize: '0.85rem' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: step >= 2 ? '#10b981' : '#e2e8f0', color: step >= 2 ? '#fff' : '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>
            {step > 2 ? '✓' : '2'}
          </div>
          02 Time
        </div>
        <div style={{ width: '40px', height: '2px', background: step >= 3 ? '#10b981' : '#e2e8f0' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: step >= 3 ? '#10b981' : '#94a3b8', fontWeight: '700', fontSize: '0.85rem' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: step >= 3 ? '#10b981' : '#e2e8f0', color: step >= 3 ? '#fff' : '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>
            {step > 3 ? '✓' : '3'}
          </div>
          03 Symptoms
        </div>
        <div style={{ width: '40px', height: '2px', background: step >= 4 ? '#10b981' : '#e2e8f0' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: step >= 4 ? '#10b981' : '#94a3b8', fontWeight: '700', fontSize: '0.85rem' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: step >= 4 ? '#10b981' : '#e2e8f0', color: step >= 4 ? '#fff' : '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>
            4
          </div>
          04 Confirm
        </div>
      </div>

      {holdExpiresAt && (
        <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '0.75rem 1.25rem', borderRadius: '9999px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '0.88rem', color: '#065f46', width: 'fit-content', margin: '0 auto' }}>
          <span>⏱️ Your slot is reserved for <strong>{countdown}</strong></span>
        </div>
      )}

      {error && (
        <div style={{ padding: '0.85rem 1.25rem', background: '#fee2e2', border: '1px solid #fca5a5', color: '#991b1b', borderRadius: '12px', fontSize: '0.9rem' }}>
          ⚠️ {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        <div>
          {step === 2 && (
            <div className="glass-card" style={{ padding: '2rem' }}>
              <h2 style={{ fontSize: '1.4rem', color: '#0f172a', marginBottom: '0.4rem' }}>Select Consultation Time</h2>
              <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                Choose an available slot for {formatDoctorName(doctor?.full_name)}.
              </p>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', marginBottom: '0.4rem', fontWeight: '600' }}>Select Date:</label>
                <input
                  type="date"
                  className="input-field"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.85rem' }}>
                {slots.map((s, idx) => {
                  const isAvailable = s.status === 'AVAILABLE';
                  return (
                    <button
                      key={idx}
                      disabled={!isAvailable}
                      onClick={() => handleHoldSlot(s)}
                      className="btn-outline"
                      style={{
                        padding: '0.85rem',
                        textAlign: 'center',
                        borderColor: isAvailable ? '#10b981' : '#e2e8f0',
                        background: isAvailable ? '#ecfdf5' : '#f8fafc',
                        color: isAvailable ? '#065f46' : '#94a3b8',
                        fontWeight: '600',
                        opacity: isAvailable ? 1 : 0.6,
                        cursor: isAvailable ? 'pointer' : 'not-allowed',
                      }}
                    >
                      {s.start_time.substring(0, 5)} - {s.end_time.substring(0, 5)}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="glass-card" style={{ padding: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', color: '#0f172a', marginBottom: '0.4rem' }}>
                Tell your doctor what you're experiencing
              </h2>
              <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                This helps {formatDoctorName(doctor?.full_name)} prepare for your visit.
              </p>

              <div style={{ padding: '1rem 1.25rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', marginBottom: '1.5rem', display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                <span style={{ fontSize: '1.2rem', color: '#10b981' }}>💡</span>
                <div style={{ fontSize: '0.85rem', color: '#475569' }}>
                  <strong>Helpful hint:</strong> Share when your symptoms started, what you are experiencing, and anything that makes them better or worse.
                </div>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <textarea
                  rows={5}
                  className="input-field"
                  placeholder="E.g., I've been having a persistent headache for the past 3 days..."
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  maxLength={500}
                />
                <div style={{ textAlign: 'right', marginTop: '0.4rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                  {symptoms.length} / 500 characters
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2rem' }}>
                <button onClick={() => setStep(2)} className="btn-outline">
                  Back
                </button>
                <button onClick={() => setStep(4)} className="btn-navy">
                  Continue to Confirmation →
                </button>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="glass-card" style={{ padding: '2rem' }}>
              <h2 style={{ fontSize: '1.5rem', color: '#0f172a', marginBottom: '0.4rem' }}>
                Confirm Consultation
              </h2>
              <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                Review your appointment details below before confirming.
              </p>

              <div style={{ padding: '1rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '1.5rem' }}>
                <div style={{ fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase' }}>Reported Symptoms</div>
                <div style={{ marginTop: '0.25rem', color: '#0f172a', fontWeight: '500' }}>{symptoms || 'General consultation request'}</div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button onClick={() => setStep(3)} className="btn-outline">
                  Back
                </button>
                <button onClick={handleConfirmBooking} disabled={submitting} className="btn-mint">
                  {submitting ? 'Confirming...' : 'Confirm Appointment'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="glass-card" style={{ padding: '1.5rem', height: 'fit-content' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#0f172a', marginBottom: '1.25rem' }}>
            Appointment Summary
          </h3>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', paddingBottom: '1.25rem', borderBottom: '1px solid #e2e8f0', marginBottom: '1.25rem' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.3rem' }}>
              👩‍⚕️
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>CONSULTATION WITH</div>
              <div style={{ fontWeight: '700', fontSize: '0.95rem', color: '#0f172a' }}>{formatDoctorName(doctor?.full_name)}</div>
              <div style={{ fontSize: '0.78rem', color: '#10b981' }}>{doctor?.specialisation}</div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.25rem' }}>
            <div>
              <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: '600' }}>📅 Date & Time</div>
              <div style={{ fontSize: '0.88rem', color: '#0f172a', fontWeight: '600', marginTop: '0.2rem' }}>
                {selectedDate} • {selectedSlot ? `${selectedSlot.start_time.substring(0, 5)} - ${selectedSlot.end_time.substring(0, 5)}` : 'Not selected'}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: '600' }}>🎥 Format</div>
              <div style={{ fontSize: '0.88rem', color: '#0f172a', fontWeight: '600', marginTop: '0.2rem' }}>Video Consultation</div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '1rem', borderTop: '1px solid #e2e8f0', marginBottom: '1.25rem' }}>
            <span style={{ fontSize: '0.9rem', color: '#64748b' }}>Consultation Fee</span>
            <span style={{ fontSize: '1.1rem', fontWeight: '800', color: '#0f172a' }}>$120.00</span>
          </div>

          <div style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.75rem', color: '#64748b', textAlign: 'center' }}>
            🔒 Payments are secure and encrypted.
          </div>
        </div>
      </div>
    </div>
  );
};
