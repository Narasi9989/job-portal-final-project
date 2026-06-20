import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar.jsx';
import { getApiError, loginUser } from '../services/api.js';

export default function JobSeekerLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await loginUser(form.username, form.password);
      localStorage.setItem('goskillToken', data.access_token);
      localStorage.setItem('goskillUser', JSON.stringify(data.user));
      localStorage.setItem('goskillRole', 'user');
      navigate('/user/dashboard');
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      <Navbar showAuth={false} />
      <main className="auth-layout">
        <section className="auth-info">
          <p className="eyebrow">User Access</p>
          <h1>Find the right job faster with GoSkill.</h1>
          <p>Sign in to browse available jobs, upload your resume, and manage your profile.</p>
        </section>
        <form className="auth-card" onSubmit={submit}>
          <h2>User Login</h2>
          {location.state?.message && <div className="alert success">{location.state.message}</div>}
          <label>
            Username or email
            <input
              value={form.username}
              onChange={(event) => setForm({ ...form, username: event.target.value })}
              placeholder="Enter username or email"
              autoComplete="username"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              placeholder="Enter password"
              autoComplete="current-password"
              required
            />
          </label>
          {error && <div className="alert error">{error}</div>}
          <button className="button button-primary full-width" disabled={loading}>
            {loading ? 'Signing in...' : 'Login'}
          </button>
          <Link className="auth-switch" to="/recruiter/login">
            Recruiter login
          </Link>
          <Link className="auth-switch" to="/user/register">
            New user? Register first
          </Link>
        </form>
      </main>
    </div>
  );
}
