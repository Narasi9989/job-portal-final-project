import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar.jsx';
import api, { getApiError } from '../services/api.js';

const sections = [
  { id: 'post', label: 'Post Job', icon: 'P' },
  { id: 'manage', label: 'Manage Jobs', icon: 'J' },
  { id: 'applications', label: 'View Applications', icon: 'A' },
];

const initialJob = {
  title: '',
  description: '',
  location: '',
  salary: '',
  is_active: true,
};

export default function RecruiterDashboard() {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState('post');
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [jobForm, setJobForm] = useState(initialJob);
  const [editingJobId, setEditingJobId] = useState(null);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const user = useMemo(() => JSON.parse(localStorage.getItem('goskillUser') || '{}'), []);

  const logout = () => {
    localStorage.clear();
    navigate('/');
  };

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [jobsResponse, applicationsResponse] = await Promise.all([
        api.get('/api/recruiter/jobs'),
        api.get('/api/recruiter/applications'),
      ]);
      setJobs(jobsResponse.data);
      setApplications(applicationsResponse.data);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const resetJobForm = () => {
    setJobForm(initialJob);
    setEditingJobId(null);
  };

  const saveJob = async (event) => {
    event.preventDefault();
    setActionLoading('job');
    setMessage('');
    setError('');

    const payload = {
      ...jobForm,
      is_active: Boolean(jobForm.is_active),
    };

    try {
      if (editingJobId) {
        await api.put(`/api/jobs/${editingJobId}`, payload);
        setMessage('Job updated successfully.');
      } else {
        await api.post('/api/jobs', payload);
        setMessage('Job posted successfully.');
      }
      resetJobForm();
      await loadData();
      setActiveSection('manage');
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setActionLoading('');
    }
  };

  const editJob = (job) => {
    setEditingJobId(job.id);
    setJobForm({
      title: job.title || '',
      description: job.description || '',
      location: job.location || '',
      salary: job.salary || '',
      is_active: job.is_active !== false,
    });
    setActiveSection('post');
  };

  const deleteJob = async (jobId) => {
    setActionLoading(`delete-job-${jobId}`);
    setMessage('');
    setError('');
    try {
      await api.delete(`/api/jobs/${jobId}`);
      setMessage('Job deleted successfully.');
      await loadData();
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setActionLoading('');
    }
  };

  const viewDetail = async (type, id) => {
    setActionLoading(`detail-${type}-${id}`);
    setSelectedDetail(null);
    setError('');
    try {
      const response = await api.get(`/api/${type}/${id}`);
      setSelectedDetail({ type, data: response.data });
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setActionLoading('');
    }
  };

  return (
    <div className="dashboard">
      <Sidebar
        title="Recruiter"
        sections={sections}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
        onLogout={logout}
      />
      <main className="dashboard-main">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">Signed in as {user.username || 'Recruiter'}</p>
            <h1>{sections.find((section) => section.id === activeSection)?.label}</h1>
          </div>
          <button className="button button-outline-blue" onClick={loadData}>
            Refresh Data
          </button>
        </div>

        {message && <div className="alert success">{message}</div>}
        {error && <div className="alert error">{error}</div>}
        {selectedDetail && (
          <section className="content-card detail-card">
            <div className="section-title-row">
              <h2>Job Detail</h2>
              <button className="button button-outline-blue compact-button" onClick={() => setSelectedDetail(null)}>
                Close
              </button>
            </div>
            <pre>{JSON.stringify(selectedDetail.data, null, 2)}</pre>
          </section>
        )}

        {activeSection === 'post' && (
          <div className="single-form-layout">
            <form className="content-card form-grid" onSubmit={saveJob}>
              <h2>{editingJobId ? 'Update Job' : 'Create Job'}</h2>
              <label>
                Job title
                <input
                  value={jobForm.title}
                  onChange={(event) => setJobForm({ ...jobForm, title: event.target.value })}
                  placeholder="Senior Python Developer"
                  required
                />
              </label>
              <label>
                Description
                <textarea
                  value={jobForm.description}
                  onChange={(event) => setJobForm({ ...jobForm, description: event.target.value })}
                  placeholder="Role responsibilities and requirements"
                  rows="5"
                />
              </label>
              <label>
                Location
                <input
                  value={jobForm.location}
                  onChange={(event) => setJobForm({ ...jobForm, location: event.target.value })}
                  placeholder="Hyderabad"
                />
              </label>
              <label>
                Salary
                <input
                  value={jobForm.salary}
                  onChange={(event) => setJobForm({ ...jobForm, salary: event.target.value })}
                  placeholder="12 LPA"
                />
              </label>
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={jobForm.is_active}
                  onChange={(event) => setJobForm({ ...jobForm, is_active: event.target.checked })}
                />
                Active job
              </label>
              <div className="form-actions">
                <button className="button button-primary" disabled={actionLoading === 'job'}>
                  {actionLoading === 'job' ? 'Saving...' : editingJobId ? 'Update Job' : 'Post Job'}
                </button>
                {editingJobId && (
                  <button type="button" className="button button-outline-blue" onClick={resetJobForm}>
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </div>
        )}

        {activeSection === 'manage' && (
          <section className="content-card">
            <h2>Posted Jobs</h2>
            {loading ? (
              <div className="loading-card">Loading jobs...</div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Company</th>
                      <th>Location</th>
                      <th>Salary</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job) => (
                      <tr key={job.id}>
                        <td>{job.title}</td>
                        <td>{job.company?.name || 'Recruiter company'}</td>
                        <td>{job.location || 'Not listed'}</td>
                        <td>{job.salary || 'Not listed'}</td>
                        <td>{job.is_active === false ? 'Closed' : 'Open'}</td>
                        <td>
                          <div className="row-actions">
                            <button
                              className="table-button"
                              onClick={() => viewDetail('jobs', job.id)}
                              disabled={actionLoading === `detail-jobs-${job.id}`}
                            >
                              View
                            </button>
                            <button className="table-button" onClick={() => editJob(job)}>
                              Edit
                            </button>
                            <button
                              className="table-button"
                              onClick={() => deleteJob(job.id)}
                              disabled={actionLoading === `delete-job-${job.id}`}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!jobs.length && <div className="empty-state">No jobs are available right now.</div>}
              </div>
            )}
          </section>
        )}

        {activeSection === 'applications' && (
          <section className="content-card">
            <h2>Candidate Applications</h2>
            {loading ? (
              <div className="loading-card">Loading applications...</div>
            ) : applications.length ? (
              <div className="applications-list">
                {applications.map((application) => (
                  <article className="application-row recruiter-application-row" key={application.id}>
                    <div>
                      <h3>{application.job?.title || `Job #${application.job_id}`}</h3>
                      <p>{application.applicant_name || `Candidate #${application.candidate_id}`}</p>
                      <p>{application.experience || 'Experience not listed'}</p>
                      <p>{application.skills || 'Skills not listed'}</p>
                      {application.cover_letter && <p>{application.cover_letter}</p>}
                      {application.resume_url && <p>Resume: {application.resume_url}</p>}
                    </div>
                    <span className="job-badge">{application.status}</span>
                  </article>
                ))}
              </div>
            ) : (
              <p className="muted">No candidate applications are available right now.</p>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
