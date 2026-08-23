import React from 'react';
import { useNavigate } from 'react-router-dom';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '4rem', paddingBottom: '4rem' }}>
      
      {/* Hero Section */}
      <section style={{ textAlign: 'center', maxWidth: '850px', margin: '2rem auto 0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem' }}>
        <div className="badge badge-mint" style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}>
          ✨ AI-POWERED CLINICAL CARE PORTAL
        </div>
        
        <h1 style={{ fontSize: '3.2rem', fontWeight: '800', lineHeight: 1.15, color: '#0f172a' }}>
          Healthcare, Organized in One Place.
        </h1>

        <p style={{ color: '#64748b', fontSize: '1.15rem', lineHeight: 1.6, maxWidth: '720px' }}>
          Book consultations with top specialists like <strong>Dr. Rohit Sharma</strong> and <strong>Dr. Virat Kohli</strong>. Get instant AI pre-visit assessments, 5-minute slot reservation guarantees, and automatic Google Calendar sync.
        </p>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <button onClick={() => navigate('/login')} className="btn-mint" style={{ padding: '0.85rem 1.8rem', fontSize: '1rem' }}>
            Book Appointment Now →
          </button>
          <button onClick={() => navigate('/login')} className="btn-navy" style={{ padding: '0.85rem 1.8rem', fontSize: '1rem' }}>
            Sign In to Portal
          </button>
        </div>
      </section>

      {/* Stats Bar */}
      <section style={{ background: '#ffffff', borderRadius: '20px', border: '1px solid #e2e8f0', padding: '2rem', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '2rem', textAlign: 'center', boxShadow: '0 4px 20px -2px rgba(0,0,0,0.04)' }}>
        <div>
          <div style={{ fontSize: '2.2rem', fontWeight: '800', color: '#10b981' }}>4.9 ★</div>
          <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: '600' }}>Patient Rating</div>
        </div>
        <div>
          <div style={{ fontSize: '2.2rem', fontWeight: '800', color: '#0f172a' }}>10,000+</div>
          <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: '600' }}>Completed Consultations</div>
        </div>
        <div>
          <div style={{ fontSize: '2.2rem', fontWeight: '800', color: '#06b6d4' }}>&lt; 5 Min</div>
          <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: '600' }}>Slot Reservation Hold</div>
        </div>
        <div>
          <div style={{ fontSize: '2.2rem', fontWeight: '800', color: '#10b981' }}>100%</div>
          <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: '600' }}>Calendar Sync Rate</div>
        </div>
      </section>

      {/* Top Doctors Roster Showcase */}
      <section>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: '700', color: '#0f172a' }}>
            Meet Our Top Specialists
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.95rem', marginTop: '0.3rem' }}>
            Renowned clinical practitioners available for online & in-person consultations.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem' }}>
          <div className="glass-card" style={{ padding: '1.75rem', background: '#ffffff', textAlign: 'center' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: '#d1fae5', margin: '0 auto 1rem auto', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem' }}>
              🏏
            </div>
            <h3 style={{ fontSize: '1.15rem', color: '#0f172a', fontWeight: '700' }}>Dr. Rohit Sharma</h3>
            <div style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: '600', marginBottom: '0.4rem' }}>Senior Cardiologist</div>
            <p style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: '1.25rem' }}>Preventive cardiology & vascular health specialist.</p>
            <button onClick={() => navigate('/login')} className="btn-navy" style={{ width: '100%', padding: '0.6rem' }}>Book Dr. Rohit</button>
          </div>

          <div className="glass-card" style={{ padding: '1.75rem', background: '#ffffff', textAlign: 'center' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: '#d1fae5', margin: '0 auto 1rem auto', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem' }}>
              🏏
            </div>
            <h3 style={{ fontSize: '1.15rem', color: '#0f172a', fontWeight: '700' }}>Dr. Virat Kohli</h3>
            <div style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: '600', marginBottom: '0.4rem' }}>Lead Neurologist</div>
            <p style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: '1.25rem' }}>Cognitive performance & neuromuscular medicine.</p>
            <button onClick={() => navigate('/login')} className="btn-navy" style={{ width: '100%', padding: '0.6rem' }}>Book Dr. Virat</button>
          </div>

          <div className="glass-card" style={{ padding: '1.75rem', background: '#ffffff', textAlign: 'center' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: '#e2e8f0', margin: '0 auto 1rem auto', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem' }}>
              👩‍⚕️
            </div>
            <h3 style={{ fontSize: '1.15rem', color: '#0f172a', fontWeight: '700' }}>Dr. Sarah Jenkins</h3>
            <div style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: '600', marginBottom: '0.4rem' }}>General Medicine</div>
            <p style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: '1.25rem' }}>Primary care & diagnostic medicine specialist.</p>
            <button onClick={() => navigate('/login')} className="btn-navy" style={{ width: '100%', padding: '0.6rem' }}>Book Dr. Sarah</button>
          </div>

          <div className="glass-card" style={{ padding: '1.75rem', background: '#ffffff', textAlign: 'center' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: '#e2e8f0', margin: '0 auto 1rem auto', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem' }}>
              👶
            </div>
            <h3 style={{ fontSize: '1.15rem', color: '#0f172a', fontWeight: '700' }}>Dr. Ujjwal</h3>
            <div style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: '600', marginBottom: '0.4rem' }}>Pediatric Specialist</div>
            <p style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: '1.25rem' }}>Child development & adolescent healthcare.</p>
            <button onClick={() => navigate('/login')} className="btn-navy" style={{ width: '100%', padding: '0.6rem' }}>Book Dr. Ujjwal</button>
          </div>
        </div>
      </section>

      {/* Core Features Grid */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1.75rem', background: '#ffffff' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: '#d1fae5', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', marginBottom: '1rem' }}>
            🤖
          </div>
          <h3 style={{ fontSize: '1.2rem', color: '#0f172a', fontWeight: '700', marginBottom: '0.5rem' }}>AI Pre-Visit Assessment</h3>
          <p style={{ color: '#64748b', fontSize: '0.88rem', lineHeight: 1.5 }}>
            Automated LLM triage analyzes patient symptoms before the consultation starts, calculating urgency levels and generating targeted clinical questions.
          </p>
        </div>

        <div className="glass-card" style={{ padding: '1.75rem', background: '#ffffff' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: '#e0f2fe', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', marginBottom: '1rem' }}>
            🗓️
          </div>
          <h3 style={{ fontSize: '1.2rem', color: '#0f172a', fontWeight: '700', marginBottom: '0.5rem' }}>Google Calendar Sync</h3>
          <p style={{ color: '#64748b', fontSize: '0.88rem', lineHeight: 1.5 }}>
            Real-time dual-participant OAuth integration. Automatically syncs confirmed appointments to both patient and doctor Google Calendars independently.
          </p>
        </div>

        <div className="glass-card" style={{ padding: '1.75rem', background: '#ffffff' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: '#fef3c7', color: '#b45309', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', marginBottom: '1rem' }}>
            ⏱️
          </div>
          <h3 style={{ fontSize: '1.2rem', color: '#0f172a', fontWeight: '700', marginBottom: '0.5rem' }}>Slot Reservation Hold</h3>
          <p style={{ color: '#64748b', fontSize: '0.88rem', lineHeight: 1.5 }}>
            Atomic slot reservation guarantees a 5-minute hold while filling out symptoms, preventing double-booking and race conditions.
          </p>
        </div>
      </section>
    </div>
  );
};
