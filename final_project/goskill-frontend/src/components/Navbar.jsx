import { Link, useNavigate } from 'react-router-dom';

export default function Navbar({ showAuth = true }) {
  const navigate = useNavigate();
  const token = localStorage.getItem('goskillToken');
  const role = localStorage.getItem('goskillRole') === 'job-seeker' ? 'user' : localStorage.getItem('goskillRole');

  const logout = () => {
    localStorage.removeItem('goskillToken');
    localStorage.removeItem('goskillUser');
    localStorage.removeItem('goskillRole');
    navigate('/');
  };

  return (
    <header className="navbar">
      <Link to="/" className="brand">
        <span className="brand-mark">G</span>
        GoSkill
      </Link>
      {showAuth && (
        <nav className="nav-actions">
          {token ? (
            <>
              <Link className="nav-link" to="/">
                Jobs
              </Link>
              <Link className="nav-link" to={role === 'recruiter' ? '/recruiter/dashboard' : '/user/dashboard'}>
                Dashboard
              </Link>
              <button className="button button-ghost" onClick={logout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <a className="nav-link" href="#jobs">
                Jobs
              </a>
              <a className="nav-link" href="#companies">
                Companies
              </a>
              <Link className="nav-link" to="/user/login">
                Login
              </Link>
              <Link className="button button-primary small-button" to="/user/register">
                Register
              </Link>
            </>
          )}
        </nav>
      )}
    </header>
  );
}
