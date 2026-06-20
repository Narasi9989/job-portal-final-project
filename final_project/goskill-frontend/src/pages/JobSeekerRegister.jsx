import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar.jsx';
import { getApiError, registerUser } from '../services/api.js';

export default function JobSeekerRegister() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await registerUser(form);
      navigate('/user/login', {
        state: { message: 'Registration successful. Please login as a user.' },
      });
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
          <p className="eyebrow">Create User Account</p>
          <h1>Register first, then login to find jobs.</h1>
          <p>Create your GoSkill account before entering the user dashboard.</p>
        </section>
        <form className="auth-card" onSubmit={submit}>
          <h2>User Register</h2>
          <label>
            Username
            <input
              value={form.username}
              onChange={(event) => setForm({ ...form, username: event.target.value })}
              placeholder="Choose username"
              autoComplete="username"
              required
            />
          </label>
          <label>
            Email
            <input
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              placeholder="Create password"
              autoComplete="new-password"
              required
            />
          </label>
          {error && <div className="alert error">{error}</div>}
          <button className="button button-primary full-width" disabled={loading}>
            {loading ? 'Creating account...' : 'Register'}
          </button>
          <Link className="auth-switch" to="/user/login">
            Already registered? Login
          </Link>
        </form>
      </main>
    </div>
  );
}
