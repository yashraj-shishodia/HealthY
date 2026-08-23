import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { doctorApi, DoctorProfile } from '../services/doctorApi';
import { formatDoctorName } from '../utils/formatters';

export const DoctorListPage: React.FC = () => {
  const navigate = useNavigate();
  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [search, setSearch] = useState('');
  const [specialisation, setSpecialisation] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        const data = await doctorApi.listDoctors();
        setDoctors(data);
      } catch (err: any) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDoctors();
  }, []);

  const filteredDoctors = doctors.filter(doc => {
    const docName = doc.full_name || 'Specialist';
    const nameMatch = docName.toLowerCase().includes(search.toLowerCase());
    const specMatch = !specialisation || doc.specialisation === specialisation;
    return nameMatch && specMatch;
  });

  const specialisations = Array.from(new Set(doctors.map(d => d.specialisation)));

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div>
        <h1 style={{ fontSize: '2.1rem', fontWeight: '700', color: '#0f172a', marginBottom: '0.4rem' }}>
          Find the right doctor for you
        </h1>
        <p style={{ color: '#64748b', fontSize: '0.95rem' }}>
          Search through our network of top specialists, view their availability, and book your appointment instantly.
        </p>
      </div>

      {/* Search & Specialisation Filter Card */}
      <div className="glass-card" style={{ padding: '1.25rem 1.5rem', background: '#ffffff' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <span style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}>🔍</span>
            <input
              type="text"
              className="input-field"
              style={{ paddingLeft: '2.5rem' }}
              placeholder="Search by doctor name or keywords..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className="input-field"
            value={specialisation}
            onChange={(e) => setSpecialisation(e.target.value)}
          >
            <option value="">Filter Specialisation (All)</option>
            {specialisations.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Doctor Card Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <p style={{ color: '#64748b' }}>Loading available specialists...</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
          {filteredDoctors.map(doc => (
            <div key={doc.id} className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '1.75rem' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                  <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.8rem', border: '2px solid #ffffff', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
                    👩‍⚕️
                  </div>
                  <span style={{ background: '#fef3c7', color: '#b45309', padding: '0.2rem 0.5rem', borderRadius: '8px', fontSize: '0.8rem', fontWeight: '700', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                    ★ 4.9
                  </span>
                </div>

                <h3 style={{ fontSize: '1.2rem', color: '#0f172a', fontWeight: '700', marginBottom: '0.2rem' }}>
                  {formatDoctorName(doc.full_name)}
                </h3>
                <div style={{ fontSize: '0.88rem', color: '#10b981', fontWeight: '600', marginBottom: '0.3rem' }}>
                  {doc.specialisation}
                </div>
                <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '1.25rem', lineHeight: 1.4 }}>
                  {doc.bio || 'Senior clinical consultant available for consultations.'}
                </p>
              </div>

              <button
                onClick={() => navigate(`/patient/doctors/${doc.id}/book`)}
                className="btn-navy"
                style={{ width: '100%', padding: '0.75rem' }}
              >
                Book Appointment
              </button>
            </div>
          ))}

          {filteredDoctors.length === 0 && (
            <div className="glass-card" style={{ gridColumn: 'span 3', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '3rem', background: '#f8fafc' }}>
              <h4 style={{ fontSize: '1.1rem', color: '#0f172a', fontWeight: '700', marginBottom: '0.4rem' }}>
                No doctors match your criteria
              </h4>
              <p style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
                Try resetting your search term or specialisation filter.
              </p>
              <button
                onClick={() => { setSearch(''); setSpecialisation(''); }}
                className="btn-outline"
                style={{ fontSize: '0.85rem' }}
              >
                Reset Filters
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
