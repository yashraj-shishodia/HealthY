import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { fetchWithAuth } from '../services/apiClient';
import { authApi } from '../services/authApi';

export const CalendarCallbackPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [statusMsg, setStatusMsg] = useState('Connecting your Google Calendar...');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (!code || !state) {
      setErrorMsg('Invalid authorization response from Google.');
      return;
    }

    const completeOAuth = async () => {
      try {
        await fetchWithAuth(`/calendar/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`);
        setStatusMsg('✅ Google Calendar connected successfully! Redirecting...');
        setTimeout(() => {
          const user = authApi.getCurrentUser();
          if (user?.role === 'DOCTOR') navigate('/doctor/dashboard');
          else navigate('/patient/dashboard');
        }, 1500);
      } catch (err: any) {
        console.error(err);
        setErrorMsg(err.message || 'Failed to complete Google Calendar connection.');
      }
    };

    completeOAuth();
  }, [searchParams, navigate]);

  return (
    <div style={{ maxWidth: '600px', margin: '4rem auto', padding: '0 1.5rem', textAlign: 'center' }}>
      <div className="glass-card animate-fade-in" style={{ padding: '3rem' }}>
        {errorMsg ? (
          <div>
            <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚠️</div>
            <h2 style={{ color: '#ef4444', marginBottom: '1rem' }}>Calendar Connection Failed</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>{errorMsg}</p>
            <button onClick={() => navigate('/')} className="btn-secondary">
              Back to Dashboard
            </button>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🗓️</div>
            <h2 style={{ color: 'var(--accent-emerald)', marginBottom: '1rem' }}>{statusMsg}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Synchronizing your appointment schedules with Google Calendar...
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
