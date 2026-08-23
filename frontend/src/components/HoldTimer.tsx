import React, { useEffect, useState } from 'react';

interface HoldTimerProps {
  expiresAtIso: string;
  onExpire: () => void;
}

export const HoldTimer: React.FC<HoldTimerProps> = ({ expiresAtIso, onExpire }) => {
  const [secondsLeft, setSecondsLeft] = useState<number>(0);

  useEffect(() => {
    const calculateSecondsLeft = () => {
      const expiresAt = new Date(expiresAtIso).getTime();
      const now = new Date().getTime();
      const diff = Math.max(0, Math.floor((expiresAt - now) / 1000));
      return diff;
    };

    setSecondsLeft(calculateSecondsLeft());

    const interval = setInterval(() => {
      const left = calculateSecondsLeft();
      setSecondsLeft(left);
      if (left <= 0) {
        clearInterval(interval);
        onExpire();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [expiresAtIso, onExpire]);

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const isWarning = secondsLeft < 60;

  return (
    <div
      className={`glass-panel ${isWarning ? 'pulse-glow' : ''}`}
      style={{
        padding: '0.75rem 1.25rem',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.75rem',
        borderColor: isWarning ? 'rgba(245, 158, 11, 0.5)' : 'rgba(16, 185, 129, 0.3)',
        background: isWarning ? 'rgba(245, 158, 11, 0.1)' : 'rgba(16, 185, 129, 0.08)',
      }}
    >
      <span style={{ fontSize: '1.2rem' }}>⏳</span>
      <div>
        <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
          Slot Hold Expires In
        </div>
        <div style={{ fontSize: '1.2rem', fontWeight: '700', fontFamily: 'monospace', color: isWarning ? '#f59e0b' : '#10b981' }}>
          {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </div>
      </div>
    </div>
  );
};
