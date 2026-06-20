import { Navigate } from 'react-router-dom';

export default function ProtectedRoute({ children, role }) {
  const token = localStorage.getItem('goskillToken');
  const rawRole = localStorage.getItem('goskillRole');
  const storedRole = rawRole === 'job-seeker' ? 'user' : rawRole;

  if (!token) {
    return <Navigate to={role === 'recruiter' ? '/recruiter/login' : '/user/login'} replace />;
  }

  if (role && storedRole && storedRole !== role) {
    return <Navigate to={storedRole === 'recruiter' ? '/recruiter/dashboard' : '/user/dashboard'} replace />;
  }

  return children;
}
