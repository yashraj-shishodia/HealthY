import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authApi, User } from '../services/authApi';
import { calendarApi, CalendarStatusResponse } from '../services/calendarApi';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState<User | null>(authApi.getCurrentUser());
  const [gcalStatus, setGcalStatus] = useState<CalendarStatusResponse | null>(null);

  useEffect(() => {
    const currentUser = authApi.getCurrentUser();
    setUser(currentUser);
    if (currentUser) {
      calendarApi.getStatus()
        .then(setGcalStatus)
        .catch(() => setGcalStatus({ is_connected: false }));
    }
  }, [location.pathname]);

  const handleLogout = () => {
    authApi.logout();
    setUser(null);
    navigate('/login');
  };

  const handleConnectCalendar = async () => {
    try {
      if (gcalStatus?.is_connected) {
        await calendarApi.disconnect();
        setGcalStatus({ is_connected: false });
      } else {
        const { auth_url } = await calendarApi.getConnectUrl();
        window.location.href = auth_url;
      }
    } catch (err: any) {
      alert(err.message || 'Failed to manage Google Calendar');
    }
  };

  if (!user) {
    return (
      <header className="top-navbar">
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ background: '#10b981', width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: '#fff' }}>+</div>
          <span style={{ fontSize: '1.3rem', fontWeight: '700', color: '#0f172a' }}>HealthY</span>
        </Link>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Link to="/login" className="btn-outline" style={{ textDecoration: 'none' }}>Login</Link>
          <Link to="/register" className="btn-mint" style={{ textDecoration: 'none' }}>Register</Link>
        </div>
      </header>
    );
  }

  return (
    <header className="top-navbar">
      {/* Horizontal Nav Links */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.75rem' }}>
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ background: '#10b981', width: '30px', height: '30px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: '#fff' }}>+</div>
          <span style={{ fontSize: '1.25rem', fontWeight: '700', fontFamily: 'var(--font-display)', color: '#0f172a' }}>
            HealthY
          </span>
        </Link>

        <div style={{ display: 'flex', gap: '1.25rem' }}>
          <Link
            to={user.role === 'DOCTOR' ? '/doctor/dashboard' : user.role === 'ADMIN' ? '/admin/dashboard' : '/patient/dashboard'}
            style={{
              textDecoration: 'none',
              fontSize: '0.85rem',
              fontWeight: '600',
              color: location.pathname.includes('/dashboard') ? '#0f172a' : '#64748b',
              borderBottom: location.pathname.includes('/dashboard') ? '2px solid #0f172a' : 'none',
              paddingBottom: '0.2rem',
            }}
          >
            Dashboard
          </Link>

          {user.role === 'PATIENT' && (
            <Link
              to="/patient/doctors"
              style={{
                textDecoration: 'none',
                fontSize: '0.85rem',
                fontWeight: '600',
                color: location.pathname.includes('/doctors') ? '#0f172a' : '#64748b',
                borderBottom: location.pathname.includes('/doctors') ? '2px solid #0f172a' : 'none',
                paddingBottom: '0.2rem',
              }}
            >
              Doctors
            </Link>
          )}

          {user.role === 'ADMIN' && (
            <Link
              to="/admin/dashboard"
              style={{
                textDecoration: 'none',
                fontSize: '0.85rem',
                fontWeight: '600',
                color: '#0f172a',
                borderBottom: '2px solid #0f172a',
                paddingBottom: '0.2rem',
              }}
            >
              Admin
            </Link>
          )}
        </div>
      </div>

      {/* Right User Bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        {/* Google Calendar Sync Button */}
        <button
          onClick={handleConnectCalendar}
          className="btn-outline"
          style={{
            padding: '0.35rem 0.75rem',
            fontSize: '0.78rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            borderRadius: '9999px',
            borderColor: gcalStatus?.is_connected ? '#a7f3d0' : '#e2e8f0',
            background: gcalStatus?.is_connected ? '#ecfdf5' : '#f8fafc',
          }}
        >
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: gcalStatus?.is_connected ? '#10b981' : '#94a3b8' }} />
          {gcalStatus?.is_connected ? 'Google Calendar Sync On' : 'Connect Google Calendar'}
        </button>

        {/* User Profile Avatar Circle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: 'linear-gradient(135deg, #0f172a 0%, #334155 100%)', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '600', fontSize: '0.82rem' }}>
            {user.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
          </div>
          <button onClick={handleLogout} className="btn-outline" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}>
            Logout
          </button>
        </div>
      </div>
    </header>
  );
};
