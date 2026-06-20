import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import JobCard from '../components/JobCard.jsx';
import Sidebar from '../components/Sidebar.jsx';
import api, { getApiError } from '../services/api.js';

const sections = [
  { id: 'jobs', label: 'Available Jobs', icon: 'J' },
  { id: 'applications', label: 'My Applications', icon: 'A' },
];

const emptyApplicationDetails = {
  applicant_name: '',
  experience: '',
  skills: '',
  cover_letter: '',
};

export default function JobSeekerDashboard() {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState('jobs');
  const [jobs, setJobs] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [applications, setApplications] = useState([]);
  const [filters, setFilters] = useState({ search: '', company_id: '' });
  const [selectedJob, setSelectedJob] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeUploaded, setResumeUploaded] = useState(null);
  const [applicationDetails, setApplicationDetails] = useState(emptyApplicationDetails);
  const [showResumeStep, setShowResumeStep] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const user = useMemo(() => JSON.parse(localStorage.getItem('goskillUser') || '{}'), []);

  const logout = () => {
    localStorage.clear();
    navigate('/');
  };

  const changeSection = (sectionId) => {
    setActiveSection(sectionId);
    setMessage('');
    setError('');
  };

  const loadJobs = async (params = filters) => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/api/jobs', {
        params: {
          search: params.search || undefined,
          company_id: params.company_id || undefined,
        },
      });
      setJobs(response.data);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const loadCompanies = async () => {
    try {
      const response = await api.get('/api/companies');
      setCompanies(response.data);
    } catch (err) {
      setError(getApiError(err));
    }
  };

  const loadApplications = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/api/applications/me');
      setApplications(response.data);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
    loadCompanies();
  }, []);

  useEffect(() => {
    if (activeSection === 'applications') {
      loadApplications();
    }
  }, [activeSection]);

  const submitFilters = (event) => {
    event.preventDefault();
    loadJobs(filters);
  };

  const viewJob = async (job) => {
    setActionLoading(`view-${job.id}`);
    setSelectedJob(null);
    setError('');
    try {
      const response = await api.get(`/api/jobs/${job.id}`);
      setSelectedJob(response.data);
      setResumeFile(null);
      setResumeUploaded(null);
      setApplicationDetails({
        ...emptyApplicationDetails,
        applicant_name: user.username || '',
      });
      setShowResumeStep(false);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setActionLoading('');
    }
  };

  const applyToSelectedJob = async () => {
    if (!selectedJob) {
      return;
    }

    if (!resumeUploaded) {
      setShowResumeStep(true);
      setMessage('');
      setError('Please upload your resume before applying.');
      return;
    }

    if (!applicationDetails.applicant_name || !applicationDetails.experience || !applicationDetails.skills) {
      setShowResumeStep(true);
      setMessage('');
      setError('Please enter your name, experience, and skills before applying.');
      return;
    }

    setActionLoading(`apply-${selectedJob.id}`);
    setMessage('');
    setError('');
    try {
      const response = await api.post('/api/applications', {
        job_id: selectedJob.id,
        ...applicationDetails,
        resume_url: resumeUploaded.stored_path || resumeUploaded.filename,
      });
      setApplications((current) => {
        const exists = current.some((application) => application.id === response.data.id);
        return exists ? current : [response.data, ...current];
      });
      setMessage(`Application submitted for ${selectedJob.title}.`);
      setShowResumeStep(false);
      setSelectedJob(null);
      setResumeUploaded(null);
      setApplicationDetails(emptyApplicationDetails);
      await loadApplications();
      setActiveSection('applications');
    } catch (err) {
      const apiError = getApiError(err);
      if (apiError.includes('already applied')) {
        setMessage('You have already applied to this job.');
        await loadApplications();
        setActiveSection('applications');
      } else {
        setError(apiError);
      }
    } finally {
      setActionLoading('');
    }
  };

  const uploadResumeForApplication = async (event) => {
    event.preventDefault();
    if (!resumeFile) {
      setError('Please select a PDF, DOC, or DOCX resume file.');
      return;
    }

    setActionLoading('resume');
    setMessage('');
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', resumeFile);
      const response = await api.post('/api/resumes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResumeUploaded(response.data?.resume || { filename: resumeFile.name });
      setMessage('Resume uploaded. Click Apply Now to submit your application.');
      setResumeFile(null);
      event.target.reset();
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setActionLoading('');
    }
  };

  return (
    <div className="dashboard">
      <Sidebar
        title="User"
        sections={sections}
        activeSection={activeSection}
        onSectionChange={changeSection}
        onLogout={logout}
      />
      <main className="dashboard-main">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">Signed in as {user.username || 'User'}</p>
            <h1>{sections.find((section) => section.id === activeSection)?.label}</h1>
          </div>
          <button
            className="button button-outline-blue"
            onClick={() => (activeSection === 'applications' ? loadApplications() : loadJobs())}
          >
            {activeSection === 'applications' ? 'Refresh Applications' : 'Refresh Jobs'}
          </button>
        </div>

        {message && <div className="alert success">{message}</div>}
        {error && <div className="alert error">{error}</div>}

        {activeSection === 'jobs' && (
          <section>
            <form className="content-card filter-bar" onSubmit={submitFilters}>
              <label>
                Search jobs
                <input
                  value={filters.search}
                  onChange={(event) => setFilters({ ...filters, search: event.target.value })}
                  placeholder="Search title or description"
                />
              </label>
              <label>
                Company
                <select
                  value={filters.company_id}
                  onChange={(event) => setFilters({ ...filters, company_id: event.target.value })}
                >
                  <option value="">All companies</option>
                  {companies.map((company) => (
                    <option key={company.id} value={company.id}>
                      {company.name}
                    </option>
                  ))}
                </select>
              </label>
              <button className="button button-primary">Search</button>
              <button
                type="button"
                className="button button-outline-blue"
                onClick={() => {
                  const cleared = { search: '', company_id: '' };
                  setFilters(cleared);
                  loadJobs(cleared);
                }}
              >
                Clear
              </button>
            </form>

            {selectedJob && (
              <section className="content-card detail-card">
                <div className="section-title-row">
                  <h2>{selectedJob.title}</h2>
                  <button className="button button-outline-blue compact-button" onClick={() => setSelectedJob(null)}>
                    Close
                  </button>
                </div>
                <p className="muted">{selectedJob.company?.name || `Company #${selectedJob.company_id}`}</p>
                <div className="job-meta">
                  <span>{selectedJob.location || 'Location not listed'}</span>
                  <span>{selectedJob.salary || 'Salary not listed'}</span>
                  <span>{selectedJob.is_active === false ? 'Closed' : 'Open'}</span>
                </div>
                <p>{selectedJob.description || 'No description provided by the recruiter.'}</p>
                <button
                  className="button button-primary"
                  onClick={applyToSelectedJob}
                  disabled={actionLoading === `apply-${selectedJob.id}` || selectedJob.is_active === false}
                >
                  {actionLoading === `apply-${selectedJob.id}` ? 'Applying...' : resumeUploaded ? 'Apply Now' : 'Upload Resume to Apply'}
                </button>
                {showResumeStep && (
                  <form className="apply-resume-box" onSubmit={uploadResumeForApplication}>
                    <div className="application-fields-grid">
                      <label>
                        Full name
                        <input
                          value={applicationDetails.applicant_name}
                          onChange={(event) =>
                            setApplicationDetails({ ...applicationDetails, applicant_name: event.target.value })
                          }
                          placeholder="Enter your full name"
                          required
                        />
                      </label>
                      <label>
                        Experience
                        <input
                          value={applicationDetails.experience}
                          onChange={(event) =>
                            setApplicationDetails({ ...applicationDetails, experience: event.target.value })
                          }
                          placeholder="Example: 2 years"
                          required
                        />
                      </label>
                      <label className="wide-field">
                        Skills
                        <input
                          value={applicationDetails.skills}
                          onChange={(event) =>
                            setApplicationDetails({ ...applicationDetails, skills: event.target.value })
                          }
                          placeholder="React, Python, SQL"
                          required
                        />
                      </label>
                      <label className="wide-field">
                        Cover letter
                        <textarea
                          value={applicationDetails.cover_letter}
                          onChange={(event) =>
                            setApplicationDetails({ ...applicationDetails, cover_letter: event.target.value })
                          }
                          placeholder="Write a short note for the recruiter"
                          rows="3"
                        />
                      </label>
                    </div>
                    <label>
                      Resume file
                      <input
                        type="file"
                        accept=".pdf,.doc,.docx"
                        onChange={(event) => setResumeFile(event.target.files?.[0] || null)}
                        required
                      />
                    </label>
                    {resumeFile && <div className="file-pill">{resumeFile.name}</div>}
                    {resumeUploaded && <div className="file-pill">Resume uploaded: {resumeUploaded.filename}</div>}
                    <button className="button button-secondary" disabled={actionLoading === 'resume'}>
                      {actionLoading === 'resume' ? 'Uploading...' : 'Upload Resume'}
                    </button>
                  </form>
                )}
              </section>
            )}

            {loading ? (
              <div className="loading-card">Loading available jobs...</div>
            ) : (
              <div className="jobs-grid">
                {jobs.map((job) => (
                  <JobCard
                    key={job.id}
                    job={job}
                    onApply={viewJob}
                    applying={actionLoading === `view-${job.id}`}
                    actionLabel="View Details"
                  />
                ))}
                {!jobs.length && <div className="empty-state">No jobs are available right now.</div>}
              </div>
            )}
          </section>
        )}

        {activeSection === 'applications' && (
          <section className="content-card">
            <h2>My Applications</h2>
            {loading ? (
              <div className="loading-card">Loading applications...</div>
            ) : applications.length ? (
              <div className="applications-list">
                {applications.map((application) => (
                  <article className="application-row" key={application.id}>
                    <div>
                      <h3>{application.job?.title || `Job #${application.job_id}`}</h3>
                      <p>{application.job?.company?.name || `Company #${application.job?.company_id || ''}`}</p>
                    </div>
                    <span className="job-badge">{application.status}</span>
                  </article>
                ))}
              </div>
            ) : (
              <p className="muted">No application history is available right now.</p>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
