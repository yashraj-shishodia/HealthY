import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { authApi } from '../services/authApi';

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const user = authApi.getCurrentUser();

  if (!user) return null;

  const isActive = (path: string) => location.pathname === path;

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ marginBottom: '1.75rem', paddingLeft: '0.5rem' }}>
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', width: '34px', height: '34px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: '#fff', fontSize: '1.1rem' }}>
            +
          </div>
          <div>
            <span style={{ fontSize: '1.35rem', fontWeight: '700', fontFamily: 'var(--font-display)', color: '#0f172a', display: 'block', lineHeight: 1 }}>
              HealthY
            </span>
            <span style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: '500' }}>Clinical Portal</span>
          </div>
        </Link>
      </div>

      {/* Primary Action CTA Button */}
      {user.role === 'PATIENT' && (
        <button
          onClick={() => navigate('/patient/doctors')}
          className="btn-mint"
          style={{ width: '100%', marginBottom: '1.75rem', padding: '0.75rem', fontSize: '0.9rem' }}
        >
          + New Appointment
        </button>
      )}

      {/* Navigation Links */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', flex: 1 }}>
        {user.role === 'PATIENT' && (
          <>
            <Link
              to="/patient/dashboard"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.7rem 0.9rem',
                borderRadius: '12px',
                textDecoration: 'none',
                fontSize: '0.9rem',
                fontWeight: '600',
                color: isActive('/patient/dashboard') ? '#0f172a' : '#64748b',
                background: isActive('/patient/dashboard') ? '#d1fae5' : 'transparent',
                transition: 'all 0.2s ease',
              }}
            >
              <span style={{ fontSize: '1.1rem' }}>📊</span> Dashboard
            </Link>

            <Link
              to="/patient/doctors"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.7rem 0.9rem',
                borderRadius: '12px',
                textDecoration: 'none',
                fontSize: '0.9rem',
                fontWeight: '600',
                color: isActive('/patient/doctors') ? '#0f172a' : '#64748b',
                background: isActive('/patient/doctors') ? '#d1fae5' : 'transparent',
                transition: 'all 0.2s ease',
              }}
            >
              <span style={{ fontSize: '1.1rem' }}>🩺</span> Doctors
            </Link>
          </>
        )}

        {user.role === 'DOCTOR' && (
          <Link
            to="/doctor/dashboard"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.7rem 0.9rem',
              borderRadius: '12px',
              textDecoration: 'none',
              fontSize: '0.9rem',
              fontWeight: '600',
              color: isActive('/doctor/dashboard') ? '#0f172a' : '#64748b',
              background: isActive('/doctor/dashboard') ? '#d1fae5' : 'transparent',
              transition: 'all 0.2s ease',
            }}
          >
            <span style={{ fontSize: '1.1rem' }}>📊</span> Doctor Workstation
          </Link>
        )}

        {user.role === 'ADMIN' && (
          <Link
            to="/admin/dashboard"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.7rem 0.9rem',
              borderRadius: '12px',
              textDecoration: 'none',
              fontSize: '0.9rem',
              fontWeight: '600',
              color: isActive('/admin/dashboard') ? '#0f172a' : '#64748b',
              background: isActive('/admin/dashboard') ? '#d1fae5' : 'transparent',
              transition: 'all 0.2s ease',
            }}
          >
            <span style={{ fontSize: '1.1rem' }}>🔒</span> Admin Portal
          </Link>
        )}
      </nav>
    </aside>
  );
};
