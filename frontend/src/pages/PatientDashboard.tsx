import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { bookingApi, Appointment } from '../services/bookingApi';
import { authApi } from '../services/authApi';
import { AISummaryCard } from '../components/AISummaryCard';
import { formatDoctorName } from '../utils/formatters';

export const PatientDashboard: React.FC = () => {
  const navigate = useNavigate();
  const user = authApi.getCurrentUser();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMyAppts = async () => {
      try {
        const data = await bookingApi.getMyAppointments();
        setAppointments(data);
      } catch (err: any) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchMyAppts();
  }, []);

  const upcomingAppts = appointments.filter(a => a.status === 'BOOKED' || a.status === 'HELD');
  const pastAppts = appointments.filter(a => a.status === 'COMPLETED' || a.status.includes('CANCELLED'));
  const nextAppt = upcomingAppts[0];

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Top Welcome Greeting */}
      <div>
        <h1 style={{ fontSize: '2.1rem', fontWeight: '700', color: '#0f172a', marginBottom: '0.25rem' }}>
          Good morning, {user?.full_name?.split(' ')[0] || 'Patient'}.
        </h1>
        <p style={{ color: '#64748b', fontSize: '0.95rem' }}>
          Your healthcare, organized in one place.
        </p>
      </div>

      {/* Main 2-Column Dashboard Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        
        {/* Left Column: Spotlight & AI Pre-visit */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          
          {/* Spotlight Hero Card (Next Appointment) */}
          {nextAppt ? (
            <div className="glass-card" style={{ borderLeft: '4px solid #10b981', padding: '1.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span className="badge badge-mint" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} />
                  Next Appointment
                </span>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#0f172a' }}>
                    {nextAppt.appointment_date}, {nextAppt.start_time.substring(0, 5)}
                  </div>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Upcoming visit</span>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.4rem' }}>
                    🩺
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.25rem', color: '#0f172a', fontWeight: '700' }}>
                      {formatDoctorName(nextAppt.doctor_name)}
                    </h3>
                    <p style={{ color: '#64748b', fontSize: '0.88rem' }}>Consultation & Triage</p>
                  </div>
                </div>

                <button
                  onClick={() => navigate(`/patient/appointments/${nextAppt.id}`)}
                  className="btn-navy"
                  style={{ padding: '0.65rem 1.4rem' }}
                >
                  View appointment
                </button>
              </div>
            </div>
          ) : (
            <div className="glass-card" style={{ padding: '2.5rem', textAlign: 'center', background: '#ffffff' }}>
              <p style={{ color: '#64748b', marginBottom: '1rem', fontSize: '1rem' }}>No upcoming appointments scheduled.</p>
              <button onClick={() => navigate('/patient/doctors')} className="btn-mint" style={{ padding: '0.75rem 1.5rem' }}>
                Find & Book Doctor
              </button>
            </div>
          )}

          {/* Quick Action Grid (2 Functional Buttons: Find Doctor & Book Appointment) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.25rem' }}>
            <button
              onClick={() => navigate('/patient/doctors')}
              className="glass-card"
              style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.25rem', border: '1px solid #e2e8f0', cursor: 'pointer', textAlign: 'left', background: '#ffffff' }}
            >
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: '#d1fae5', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.4rem', color: '#10b981' }}>
                🔍
              </div>
              <div>
                <div style={{ fontSize: '1rem', fontWeight: '700', color: '#0f172a' }}>Find a doctor</div>
                <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Browse top specialists</div>
              </div>
            </button>

            <button
              onClick={() => navigate('/patient/doctors')}
              className="glass-card"
              style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.25rem', border: '1px solid #e2e8f0', cursor: 'pointer', textAlign: 'left', background: '#ffffff' }}
            >
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: '#d1fae5', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.4rem', color: '#10b981' }}>
                📅
              </div>
              <div>
                <div style={{ fontSize: '1rem', fontWeight: '700', color: '#0f172a' }}>Book appt</div>
                <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Reserve 30-min slot</div>
              </div>
            </button>
          </div>

          {/* AI Pre-Visit Card */}
          {nextAppt && (
            <div className="glass-card" style={{ padding: '1.75rem' }}>
              <AISummaryCard appointment={nextAppt} type="pre-visit" />
            </div>
          )}

          {/* Visit History List */}
          <div className="glass-card" style={{ padding: '1.75rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '1rem', color: '#0f172a' }}>
              📜 Visit History ({pastAppts.length})
            </h3>
            {pastAppts.length === 0 ? (
              <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>No past visits on file.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {pastAppts.map(a => (
                  <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.85rem 1rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                    <div>
                      <div style={{ fontWeight: '600', color: '#0f172a', fontSize: '0.95rem' }}>
                        {formatDoctorName(a.doctor_name)}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                        {a.appointment_date} at {a.start_time.substring(0, 5)}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span className={`badge badge-${a.status.toLowerCase()}`}>{a.status}</span>
                      <button onClick={() => navigate(`/patient/appointments/${a.id}`)} className="btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
                        Details & Rx
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Upcoming List Widget */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          
          {/* Upcoming Schedule List Widget */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#0f172a', marginBottom: '1.25rem' }}>
              Upcoming Visits
            </h3>

            {upcomingAppts.length === 0 ? (
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>No upcoming visits scheduled.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {upcomingAppts.map(a => (
                  <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                    <div style={{ padding: '0.5rem 0.75rem', background: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', fontWeight: '700', color: '#64748b', textTransform: 'uppercase' }}>{a.appointment_date.split('-')[1]}</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: '800', color: '#0f172a' }}>{a.appointment_date.split('-')[2]}</div>
                    </div>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '0.9rem', color: '#0f172a' }}>
                        {formatDoctorName(a.doctor_name)}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                        {a.start_time.substring(0, 5)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
