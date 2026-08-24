import React, { useEffect, useState } from 'react';
import { adminPortalApi, CreateDoctorPayload } from '../services/adminPortalApi';
import { doctorApi, DoctorProfile } from '../services/doctorApi';
import { formatDoctorName } from '../utils/formatters';

export const AdminDashboard: React.FC = () => {
  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [successMsg, setSuccessMsg] = useState<string>('');

  // Modal controls
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [showLeaveModal, setShowLeaveModal] = useState<boolean>(false);

  // Form states for adding a new doctor
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('Password123!');
  const [fullName, setFullName] = useState<string>('');
  const [specialisation, setSpecialisation] = useState<string>('Cardiology');
  const [workingHoursStart, setWorkingHoursStart] = useState<string>('09:00');
  const [workingHoursEnd, setWorkingHoursEnd] = useState<string>('17:00');
  const [slotDuration, setSlotDuration] = useState<number>(30);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Leave form states
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>('');
  const [leaveDate, setLeaveDate] = useState<string>('');
  const [leaveReason, setLeaveReason] = useState<string>('Annual Leave / Medical Conference');

  const fetchDoctorList = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await doctorApi.listDoctors();
      setDoctors(data);
      if (data.length > 0 && !selectedDoctorId) {
        setSelectedDoctorId(data[0].id);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load doctors list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctorList();
  }, []);

  const handleCreateDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccessMsg('');
    try {
      const payload: CreateDoctorPayload = {
        email,
        password,
        full_name: fullName,
        specialisation,
        slot_duration_minutes: Number(slotDuration),
        working_hours: [
          { day_of_week: 1, start_time: workingHoursStart, end_time: workingHoursEnd },
          { day_of_week: 2, start_time: workingHoursStart, end_time: workingHoursEnd },
          { day_of_week: 3, start_time: workingHoursStart, end_time: workingHoursEnd },
          { day_of_week: 4, start_time: workingHoursStart, end_time: workingHoursEnd },
          { day_of_week: 5, start_time: workingHoursStart, end_time: workingHoursEnd },
        ]
      };
      await adminPortalApi.createDoctor(payload);
      setShowAddModal(false);
      setEmail('');
      setFullName('');
      setSuccessMsg('Doctor account and working hours created successfully!');
      await fetchDoctorList();
    } catch (err: any) {
      setError(err.message || 'Failed to create doctor account.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoctorId || !leaveDate) return;
    setSubmitting(true);
    setError('');
    setSuccessMsg('');
    try {
      await adminPortalApi.addDoctorLeave(selectedDoctorId, {
        leave_date: leaveDate,
        reason: leaveReason,
      });
      setShowLeaveModal(false);
      setLeaveDate('');
      setSuccessMsg('Doctor leave scheduled! Affected appointments have been cancelled and patients notified.');
      await fetchDoctorList();
    } catch (err: any) {
      setError(err.message || 'Failed to schedule doctor leave.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2.1rem', fontWeight: '700', color: '#0f172a', marginBottom: '0.25rem' }}>
            Admin Dashboard
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.95rem' }}>
            Overview, working hours, and leave management of clinical operations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button onClick={() => setShowLeaveModal(true)} className="btn-outline" style={{ padding: '0.75rem 1.4rem' }}>
            📅 Manage Doctor Leave
          </button>
          <button onClick={() => setShowAddModal(true)} className="btn-navy" style={{ padding: '0.75rem 1.4rem' }}>
            + Add New Doctor
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem', background: '#fee2e2', border: '1px solid #fca5a5', color: '#991b1b', borderRadius: '12px' }}>
          ⚠️ {error}
        </div>
      )}

      {successMsg && (
        <div style={{ padding: '1rem', background: '#d1fae5', border: '1px solid #6ee7b7', color: '#065f46', borderRadius: '12px' }}>
          ✅ {successMsg}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem', background: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#64748b' }}>TOTAL DOCTORS</span>
            <span style={{ fontSize: '1.2rem', color: '#10b981' }}>🧰</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: '#0f172a' }}>{doctors.length || 4}</div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem', background: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#64748b' }}>APPOINTMENTS TODAY</span>
            <span style={{ fontSize: '1.2rem', color: '#06b6d4' }}>📅</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: '#0f172a' }}>156</div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem', background: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#64748b' }}>ACTIVE PATIENTS</span>
            <span style={{ fontSize: '1.2rem', color: '#10b981' }}>🫂</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: '#0f172a' }}>2,800</div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem', background: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#64748b' }}>CLINICAL CAPACITY</span>
            <span style={{ fontSize: '1.2rem', color: '#10b981' }}>⚡</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: '#10b981' }}>100%</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h2 style={{ fontSize: '1.25rem', color: '#0f172a', fontWeight: '700' }}>Doctor Roster & Schedules</h2>
            <span style={{ cursor: 'pointer', color: '#64748b' }}>⋮</span>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <p style={{ color: '#64748b' }}>Loading doctor roster...</p>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b', fontSize: '0.8rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '0.75rem' }}>Doctor</th>
                  <th style={{ padding: '0.75rem' }}>Specialisation</th>
                  <th style={{ padding: '0.75rem' }}>Slot Duration</th>
                  <th style={{ padding: '0.75rem' }}>Working Hours</th>
                  <th style={{ padding: '0.75rem' }}>Status</th>
                  <th style={{ padding: '0.75rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {doctors.map(d => {
                  const formattedName = formatDoctorName(d.full_name);
                  const initials = formattedName.replace(/^Dr\.\s*/i, '').split(' ').map((n: string) => n[0]).join('').substring(0, 2);
                  return (
                    <tr key={d.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.85rem 0.75rem', fontWeight: '700', color: '#0f172a', fontSize: '0.9rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                          <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#d1fae5', color: '#065f46', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', fontWeight: '700' }}>
                            {initials}
                          </div>
                          {formattedName}
                        </div>
                      </td>
                      <td style={{ padding: '0.85rem 0.75rem', color: '#64748b', fontSize: '0.85rem' }}>
                        {d.specialisation}
                      </td>
                      <td style={{ padding: '0.85rem 0.75rem', color: '#64748b', fontSize: '0.85rem' }}>
                        {d.slot_duration_minutes || 30} mins
                      </td>
                      <td style={{ padding: '0.85rem 0.75rem', color: '#64748b', fontSize: '0.85rem' }}>
                        09:00 - 17:00
                      </td>
                      <td style={{ padding: '0.85rem 0.75rem' }}>
                        <span className="badge badge-mint">{d.is_active ? 'Active' : 'Inactive'}</span>
                      </td>
                      <td style={{ padding: '0.85rem 0.75rem' }}>
                        <button
                          onClick={() => {
                            setSelectedDoctorId(d.id);
                            setShowLeaveModal(true);
                          }}
                          className="btn-outline"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                        >
                          + Leave
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#0f172a', marginBottom: '1.25rem' }}>
              Leave Calendar
            </h3>
            
            <div style={{ textAlign: 'center', color: '#64748b', fontSize: '0.9rem', marginBottom: '1rem', fontWeight: '700' }}>
              October 2026
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '0.4rem', textAlign: 'center', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '1rem' }}>
              <div>S</div><div>M</div><div>T</div><div>W</div><div>T</div><div>F</div><div>S</div>
              <div>29</div><div>30</div><div>1</div><div>2</div>
              <div style={{ background: '#fee2e2', color: '#ef4444', borderRadius: '50%', fontWeight: '700' }}>3</div>
              <div>4</div><div>5</div>
              <div>6</div><div>7</div><div>8</div><div>9</div>
              <div style={{ background: '#0f172a', color: '#fff', borderRadius: '50%', fontWeight: '700' }}>10</div>
              <div>11</div><div>12</div>
            </div>

            <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: '700', color: '#0f172a', marginBottom: '0.5rem' }}>
                Upcoming Scheduled Leave
              </div>
              <div style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: '700', color: '#0f172a' }}>Dr. Amrita</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Oct 3 - Oct 5</div>
                </div>
                <span className="badge badge-navy" style={{ fontSize: '0.7rem' }}>Approved</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Add Doctor Modal */}
      {showAddModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '500px', background: '#ffffff' }}>
            <h2 style={{ fontSize: '1.4rem', color: '#0f172a', marginBottom: '1.5rem' }}>Create Doctor Profile</h2>

            <form onSubmit={handleCreateDoctor} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', fontWeight: '600', marginBottom: '0.3rem' }}>Doctor Full Name *</label>
                <input required type="text" className="input-field" placeholder="e.g. Dr. Amrita" value={fullName} onChange={(e) => setFullName(e.target.value)} />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', fontWeight: '600', marginBottom: '0.3rem' }}>Email Address *</label>
                <input required type="email" className="input-field" placeholder="doctor@healthy.com" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', fontWeight: '600', marginBottom: '0.3rem' }}>Specialisation *</label>
                  <input required type="text" className="input-field" placeholder="e.g. Cardiology" value={specialisation} onChange={(e) => setSpecialisation(e.target.value)} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', fontWeight: '600', marginBottom: '0.3rem' }}>Slot Duration (Mins) *</label>
                  <input required type="number" className="input-field" value={slotDuration} onChange={(e) => setSlotDuration(Number(e.target.value))} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', fontWeight: '600', marginBottom: '0.3rem' }}>Shift Start *</label>
                  <input required type="time" className="input-field" value={workingHoursStart} onChange={(e) => setWorkingHoursStart(e.target.value)} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', fontWeight: '600', marginBottom: '0.3rem' }}>Shift End *</label>
                  <input required type="time" className="input-field" value={workingHoursEnd} onChange={(e) => setWorkingHoursEnd(e.target.value)} />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn-outline">Cancel</button>
                <button type="submit" disabled={submitting} className="btn-navy">{submitting ? 'Creating...' : 'Create Doctor'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Schedule Leave Modal */}
      {showLeaveModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
          <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '500px', background: '#ffffff' }}>
            <h2 style={{ fontSize: '1.4rem', color: '#0f172a', marginBottom: '1rem' }}>Schedule Doctor Leave</h2>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1.5rem' }}>
              Scheduling leave will automatically cancel conflicting patient appointments and issue email notifications.
            </p>

            <form onSubmit={handleAddLeave} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', fontWeight: '600', marginBottom: '0.3rem' }}>Select Doctor *</label>
                <select className="input-field" value={selectedDoctorId} onChange={(e) => setSelectedDoctorId(e.target.value)}>
                  {doctors.map(d => (
                    <option key={d.id} value={d.id}>{formatDoctorName(d.full_name)} ({d.specialisation})</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', fontWeight: '600', marginBottom: '0.3rem' }}>Leave Date *</label>
                <input required type="date" className="input-field" value={leaveDate} onChange={(e) => setLeaveDate(e.target.value)} />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', fontWeight: '600', marginBottom: '0.3rem' }}>Reason (Optional)</label>
                <input type="text" className="input-field" value={leaveReason} onChange={(e) => setLeaveReason(e.target.value)} />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="button" onClick={() => setShowLeaveModal(false)} className="btn-outline">Cancel</button>
                <button type="submit" disabled={submitting} className="btn-navy">{submitting ? 'Processing...' : 'Confirm Leave'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
