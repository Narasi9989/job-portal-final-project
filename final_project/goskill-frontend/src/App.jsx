import { Navigate, Route, Routes } from 'react-router-dom';
import Landing from './pages/Landing.jsx';
import JobSeekerLogin from './pages/JobSeekerLogin.jsx';
import JobSeekerRegister from './pages/JobSeekerRegister.jsx';
import RecruiterLogin from './pages/RecruiterLogin.jsx';
import RecruiterRegister from './pages/RecruiterRegister.jsx';
import JobSeekerDashboard from './pages/JobSeekerDashboard.jsx';
import RecruiterDashboard from './pages/RecruiterDashboard.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/user/register" element={<JobSeekerRegister />} />
      <Route path="/user/login" element={<JobSeekerLogin />} />
      <Route path="/recruiter/register" element={<RecruiterRegister />} />
      <Route path="/recruiter/login" element={<RecruiterLogin />} />
      <Route
        path="/user/dashboard"
        element={
          <ProtectedRoute role="user">
            <JobSeekerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recruiter/dashboard"
        element={
          <ProtectedRoute role="recruiter">
            <RecruiterDashboard />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
