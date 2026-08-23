import React from 'react';
import { Appointment } from '../services/bookingApi';

interface AISummaryCardProps {
  appointment: Appointment;
  type: 'pre-visit' | 'post-visit';
}

export const AISummaryCard: React.FC<AISummaryCardProps> = ({ appointment, type }) => {
  if (type === 'pre-visit') {
    const { pre_visit_summary_status, urgency, chief_complaint, suggested_questions } = appointment;

    if (pre_visit_summary_status === 'FAILED') {
      return (
        <div className="glass-panel" style={{ padding: '1.25rem', borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.08)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f59e0b', fontWeight: '600' }}>
            <span>⚠️</span> AI Pre-Visit Summary Temporarily Unavailable
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
            Our clinical AI service encountered a temporary delay. Your appointment remains fully booked and your symptoms are saved.
          </p>
        </div>
      );
    }

    if (pre_visit_summary_status === 'PENDING') {
      return (
        <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: '18px', height: '18px', border: '2px solid var(--accent-cyan)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Analyzing symptoms and generating AI pre-visit summary...</span>
        </div>
      );
    }

    return (
      <div className="glass-panel" style={{ padding: '1.5rem', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '4px solid var(--accent-cyan)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.2rem' }}>🤖</span>
            <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>AI Pre-Visit Assessment</h3>
          </div>
          {urgency && (
            <span className={`badge badge-urgency-${urgency.toLowerCase()}`}>
              Urgency: {urgency}
            </span>
          )}
        </div>

        {chief_complaint && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '600', marginBottom: '0.2rem' }}>
              Chief Complaint
            </div>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-primary)', lineHeight: '1.4' }}>{chief_complaint}</p>
          </div>
        )}

        {suggested_questions && suggested_questions.length > 0 && (
          <div>
            <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '600', marginBottom: '0.4rem' }}>
              Suggested Clinical Questions (3)
            </div>
            <ul style={{ paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {suggested_questions.map((q, idx) => (
                <li key={idx}>{q}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // Post-Visit Summary
  const { post_visit_summary_status, post_visit_summary } = appointment;

  if (post_visit_summary_status === 'FAILED') {
    return (
      <div className="glass-panel" style={{ padding: '1.25rem', borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.08)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f59e0b', fontWeight: '600' }}>
          <span>⚠️</span> AI Post-Visit Summary Temporarily Unavailable
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
          Your doctor's official clinical notes and prescription are available below.
        </p>
      </div>
    );
  }

  if (post_visit_summary_status === 'PENDING') {
    return (
      <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ width: '18px', height: '18px', border: '2px solid var(--accent-emerald)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Generating patient-friendly summary & medication schedule...</span>
      </div>
    );
  }

  if (!post_visit_summary) return null;

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', background: 'rgba(15, 23, 42, 0.65)', borderLeft: '4px solid var(--accent-emerald)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <span style={{ fontSize: '1.2rem' }}>📋</span>
        <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>Patient Care Summary</h3>
      </div>

      <p style={{ fontSize: '0.95rem', color: 'var(--text-primary)', marginBottom: '1.2rem', lineHeight: '1.5' }}>
        {post_visit_summary.summary}
      </p>

      {post_visit_summary.medication_schedule && post_visit_summary.medication_schedule.length > 0 && (
        <div style={{ marginBottom: '1.2rem' }}>
          <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '600', marginBottom: '0.5rem' }}>
            Prescribed Medication Schedule
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ background: 'rgba(255, 255, 255, 0.05)', textAlign: 'left' }}>
                  <th style={{ padding: '0.5rem 0.75rem', borderBottom: '1px solid var(--glass-border)' }}>Medication</th>
                  <th style={{ padding: '0.5rem 0.75rem', borderBottom: '1px solid var(--glass-border)' }}>Dosage</th>
                  <th style={{ padding: '0.5rem 0.75rem', borderBottom: '1px solid var(--glass-border)' }}>Instructions</th>
                </tr>
              </thead>
              <tbody>
                {post_visit_summary.medication_schedule.map((med: any, idx: number) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '0.5rem 0.75rem', fontWeight: '600', color: 'var(--accent-emerald)' }}>{med.medicine}</td>
                    <td style={{ padding: '0.5rem 0.75rem' }}>{med.dosage}</td>
                    <td style={{ padding: '0.5rem 0.75rem', color: 'var(--text-secondary)' }}>{med.instructions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {post_visit_summary.follow_up_steps && post_visit_summary.follow_up_steps.length > 0 && (
        <div>
          <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '600', marginBottom: '0.4rem' }}>
            Follow-up Steps
          </div>
          <ul style={{ paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            {post_visit_summary.follow_up_steps.map((step: string, idx: number) => (
              <li key={idx}>{step}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
