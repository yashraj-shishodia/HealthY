import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { PatientDashboard } from './pages/PatientDashboard';
import { DoctorListPage } from './pages/DoctorListPage';
import { BookAppointmentPage } from './pages/BookAppointmentPage';
import { AppointmentDetailPage } from './pages/AppointmentDetailPage';
import { DoctorDashboard } from './pages/DoctorDashboard';
import { AdminDashboard } from './pages/AdminDashboard';
import { CalendarCallbackPage } from './pages/CalendarCallbackPage';
import { authApi } from './services/authApi';

const RootHandler: React.FC = () => {
  const user = authApi.getCurrentUser();
  if (!user) return <LandingPage />;
  if (user.role === 'PATIENT') return <Navigate to="/patient/dashboard" replace />;
  if (user.role === 'DOCTOR') return <Navigate to="/doctor/dashboard" replace />;
  if (user.role === 'ADMIN') return <Navigate to="/admin/dashboard" replace />;
  return <LandingPage />;
};

export const App: React.FC = () => {
  const isAuth = !!authApi.getCurrentUser();

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="app-container">
        {isAuth && <Sidebar />}
        <div className={`main-wrapper ${isAuth ? 'with-sidebar' : ''}`}>
          <Navbar />
          <main className="content-body">
            <Routes>
              <Route path="/" element={<RootHandler />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Patient Portal Routes */}
              <Route path="/patient/dashboard" element={<ProtectedRoute allowedRoles={['PATIENT']}><PatientDashboard /></ProtectedRoute>} />
              <Route path="/patient/doctors" element={<ProtectedRoute allowedRoles={['PATIENT']}><DoctorListPage /></ProtectedRoute>} />
              <Route path="/patient/doctors/:doctorId/book" element={<ProtectedRoute allowedRoles={['PATIENT']}><BookAppointmentPage /></ProtectedRoute>} />
              <Route path="/patient/appointments/:id" element={<ProtectedRoute allowedRoles={['PATIENT', 'DOCTOR', 'ADMIN']}><AppointmentDetailPage /></ProtectedRoute>} />

              {/* Doctor Portal Routes */}
              <Route path="/doctor/dashboard" element={<ProtectedRoute allowedRoles={['DOCTOR']}><DoctorDashboard /></ProtectedRoute>} />

              {/* Admin Portal Routes */}
              <Route path="/admin/dashboard" element={<ProtectedRoute allowedRoles={['ADMIN']}><AdminDashboard /></ProtectedRoute>} />

              {/* Google OAuth Callback Route */}
              <Route path="/calendar/callback" element={<CalendarCallbackPage />} />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
};

export default App;
