import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { bookingApi, Appointment } from '../services/bookingApi';
import { AISummaryCard } from '../components/AISummaryCard';
import { formatDoctorName } from '../utils/formatters';

export const AppointmentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [appt, setAppt] = useState<Appointment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDetail = async () => {
      if (!id) return;
      try {
        const data = await bookingApi.getAppointmentDetail(id);
        setAppt(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load visit summary.');
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '5rem' }}>
        <p style={{ color: '#64748b' }}>Loading visit summary...</p>
      </div>
    );
  }

  if (error || !appt) {
    return (
      <div className="glass-card" style={{ maxWidth: '600px', margin: '3rem auto', textAlign: 'center', padding: '2rem' }}>
        <h3 style={{ color: '#ef4444', marginBottom: '1rem' }}>Visit Summary Error</h3>
        <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>{error || 'Appointment not found.'}</p>
        <button onClick={() => navigate('/patient/dashboard')} className="btn-outline">
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Back Header & Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <button onClick={() => navigate(-1)} className="btn-outline" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', marginBottom: '0.75rem' }}>
            ← Back
          </button>
          <h1 style={{ fontSize: '2.1rem', fontWeight: '700', color: '#0f172a' }}>
            Your visit summary
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            📅 {appt.appointment_date} at {appt.start_time.substring(0, 5)}
          </p>
        </div>

        {/* Attending Physician Card */}
        <div style={{ padding: '0.85rem 1.25rem', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '16px', display: 'flex', alignItems: 'center', gap: '0.85rem', boxShadow: '0 4px 12px rgba(0,0,0,0.04)' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '50%', background: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.3rem' }}>
            👩‍⚕️
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: '600' }}>Attending Physician</div>
            <div style={{ fontWeight: '700', fontSize: '0.95rem', color: '#0f172a' }}>{formatDoctorName(appt.doctor_name)}</div>
            <div style={{ fontSize: '0.75rem', color: '#10b981' }}>● Primary Care</div>
          </div>
        </div>
      </div>

      {/* 2-Column Visit Summary Workspace */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        
        {/* Left Column: AI Post-Visit Summary & Action Plan */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          
          {/* Visit Overview Card (Mint Green Left Accent Bar) */}
          <div className="glass-card" style={{ borderLeft: '4px solid #10b981', padding: '1.75rem' }}>
            <h3 style={{ fontSize: '1.15rem', color: '#0f172a', fontWeight: '700', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              📄 Visit Overview
            </h3>
            <AISummaryCard appointment={appt} type="post-visit" />
          </div>

          {/* Action Plan & Follow-ups Card */}
          <div className="glass-card" style={{ padding: '1.75rem' }}>
            <h3 style={{ fontSize: '1.15rem', color: '#0f172a', fontWeight: '700', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              🎯 Action Plan & Follow-ups
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#e0f2fe', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', color: '#0284c7' }}>
                    🧪
                  </div>
                  <div>
                    <div style={{ fontWeight: '700', fontSize: '0.9rem', color: '#0f172a' }}>Blood test in 2 weeks</div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Comprehensive metabolic panel to check kidney function.</div>
                  </div>
                </div>
                <button className="btn-mint" style={{ padding: '0.4rem 0.9rem', fontSize: '0.8rem' }}>Book Lab</button>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#e0f2fe', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', color: '#0284c7' }}>
                    📅
                  </div>
                  <div>
                    <div style={{ fontWeight: '700', fontSize: '0.9rem', color: '#0f172a' }}>Schedule follow-up for Sep 10</div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>In-person or telehealth visit to review lab results.</div>
                  </div>
                </div>
                <button className="btn-mint" style={{ padding: '0.4rem 0.9rem', fontSize: '0.8rem' }}>Schedule</button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Prescribed Medications Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#0f172a' }}>🔗 Medications</h3>
              <span className="badge badge-mint">Active</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginBottom: '1.5rem' }}>
              <div style={{ padding: '1rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontWeight: '700', fontSize: '0.95rem', color: '#0f172a' }}>
                  {appt.prescription || 'Paracetamol 500mg'}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.2rem' }}>500mg • Tablet</div>
                <div style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: '600', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  ⏰ Twice daily
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>Take with food for mild pain relief.</div>
              </div>
            </div>

            <button onClick={() => window.print()} className="btn-outline" style={{ width: '100%', padding: '0.65rem', fontSize: '0.85rem' }}>
              🖨 Print Med List
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
