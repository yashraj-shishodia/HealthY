import React from 'react';
import { Slot } from '../services/doctorApi';

interface SlotPickerProps {
  slots: Slot[];
  selectedSlot: Slot | null;
  onSelectSlot: (slot: Slot) => void;
  isOnLeave: boolean;
}

export const SlotPicker: React.FC<SlotPickerProps> = ({ slots, selectedSlot, onSelectSlot, isOnLeave }) => {
  if (isOnLeave) {
    return (
      <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center', borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.08)' }}>
        <span style={{ fontSize: '2rem' }}>🏖️</span>
        <h4 style={{ margin: '0.5rem 0', color: '#ef4444' }}>Doctor is On Leave</h4>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>No appointment slots are available on this date. Please select another date.</p>
      </div>
    );
  }

  if (!slots || slots.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-secondary)' }}>No working hours or available slots found for this date.</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: '0.75rem', marginTop: '1rem' }}>
      {slots.map((slot) => {
        const isSelected = selectedSlot?.start_time === slot.start_time;
        const isAvailable = slot.status === 'AVAILABLE';

        return (
          <button
            key={slot.start_time}
            disabled={!isAvailable}
            onClick={() => onSelectSlot(slot)}
            style={{
              padding: '0.75rem 0.5rem',
              borderRadius: 'var(--radius-md)',
              border: isSelected
                ? '2px solid var(--accent-emerald)'
                : isAvailable
                ? '1px solid var(--glass-border)'
                : '1px dashed rgba(255, 255, 255, 0.08)',
              background: isSelected
                ? 'rgba(16, 185, 129, 0.25)'
                : isAvailable
                ? 'rgba(30, 41, 59, 0.6)'
                : 'rgba(15, 23, 42, 0.4)',
              color: isSelected
                ? '#10b981'
                : isAvailable
                ? 'var(--text-primary)'
                : 'var(--text-muted)',
              cursor: isAvailable ? 'pointer' : 'not-allowed',
              textAlign: 'center',
              transition: 'all 0.15s ease',
              fontWeight: isSelected ? '700' : '500',
              fontSize: '0.9rem',
            }}
          >
            <div>{slot.start_time.substring(0, 5)}</div>
            <div style={{ fontSize: '0.7rem', opacity: 0.7, marginTop: '2px' }}>
              {isAvailable ? (isSelected ? 'Selected' : 'Available') : slot.status}
            </div>
          </button>
        );
      })}
    </div>
  );
};
