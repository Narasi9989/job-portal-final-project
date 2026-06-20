import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import JobCard from '../components/JobCard.jsx';
import Navbar from '../components/Navbar.jsx';
import api, { getApiError } from '../services/api.js';

const emptyApplicationDetails = {
  applicant_name: '',
  experience: '',
  skills: '',
  cover_letter: '',
};

export default function Landing() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [filters, setFilters] = useState({ search: '', location: '' });
  const [selectedJob, setSelectedJob] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeUploaded, setResumeUploaded] = useState(null);
  const [applicationDetails, setApplicationDetails] = useState(emptyApplicationDetails);
  const [showResumeStep, setShowResumeStep] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadHomeData = async () => {
    setLoading(true);
    setError('');
    try {
      const [jobsResponse, companiesResponse] = await Promise.all([api.get('/api/jobs'), api.get('/api/companies')]);
      setJobs(jobsResponse.data);
      setCompanies(companiesResponse.data);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHomeData();
  }, []);

  const filteredJobs = jobs.filter((job) => {
    const text = `${job.title || ''} ${job.description || ''} ${job.company?.name || ''}`.toLowerCase();
    const location = `${job.location || ''}`.toLowerCase();
    return (
      (!filters.search || text.includes(filters.search.toLowerCase())) &&
      (!filters.location || location.includes(filters.location.toLowerCase()))
    );
  });

  const viewJob = async (job) => {
    setActionLoading(`view-${job.id}`);
    setSelectedJob(null);
    setError('');
    setMessage('');
    try {
      const response = await api.get(`/api/jobs/${job.id}`);
      setSelectedJob(response.data);
      setResumeFile(null);
      setResumeUploaded(null);
      const user = JSON.parse(localStorage.getItem('goskillUser') || '{}');
      setApplicationDetails({
        ...emptyApplicationDetails,
        applicant_name: user.username || '',
      });
      setShowResumeStep(false);
      document.getElementById('job-detail')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setActionLoading('');
    }
  };

  const applyToJob = async () => {
    if (!selectedJob) {
      return;
    }

    const token = localStorage.getItem('goskillToken');
    const savedRole = localStorage.getItem('goskillRole');
    const role = savedRole === 'job-seeker' ? 'user' : savedRole;
    if (!token || role !== 'user') {
      navigate('/user/login', { state: { message: 'Please login as a user to apply for this job.' } });
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
    setError('');
    setMessage('');
    try {
      await api.post('/api/applications', {
        job_id: selectedJob.id,
        ...applicationDetails,
        resume_url: resumeUploaded.stored_path || resumeUploaded.filename,
      });
      setMessage(`Application submitted for ${selectedJob.title}.`);
      setShowResumeStep(false);
      setApplicationDetails(emptyApplicationDetails);
    } catch (err) {
      setError(getApiError(err));
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

    const token = localStorage.getItem('goskillToken');
    const savedRole = localStorage.getItem('goskillRole');
    const role = savedRole === 'job-seeker' ? 'user' : savedRole;
    if (!token || role !== 'user') {
      navigate('/user/login', { state: { message: 'Please login as a user to upload your resume.' } });
      return;
    }

    setActionLoading('resume');
    setError('');
    setMessage('');
    try {
      const formData = new FormData();
      formData.append('file', resumeFile);
      const response = await api.post('/api/resumes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResumeUploaded(response.data?.resume || { filename: resumeFile.name });
      setMessage('Resume uploaded. You can apply now.');
      setResumeFile(null);
      event.target.reset();
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setActionLoading('');
    }
  };

  return (
    <div className="page marketplace-page">
      <Navbar />
      <main>
        <section className="market-hero">
          <div className="market-hero-copy">
            <p className="eyebrow">India's smarter career marketplace</p>
            <h1>Find the role that moves your career forward.</h1>
            <p>
              Search curated jobs, compare companies, save roles, and manage your career from one responsive dashboard.
            </p>
            <form className="home-search" onSubmit={(event) => event.preventDefault()}>
              <input
                value={filters.search}
                onChange={(event) => setFilters({ ...filters, search: event.target.value })}
                placeholder="Job title, skills, or company"
              />
              <input
                value={filters.location}
                onChange={(event) => setFilters({ ...filters, location: event.target.value })}
                placeholder="City or remote"
              />
              <button className="button button-primary">Search Jobs</button>
            </form>
          </div>

          <div className="hero-jobs-panel">
            {loading ? (
              <div className="loading-card">Loading jobs...</div>
            ) : filteredJobs.slice(0, 3).length ? (
              filteredJobs.slice(0, 3).map((job) => (
                <article className="mini-job-card" key={job.id}>
                  <div>
                    <h3>{job.title}</h3>
                    <p>{job.company?.name || `Company #${job.company_id}`}</p>
                    <span>{job.location || 'Location not listed'}</span>
                  </div>
                  <button onClick={() => viewJob(job)}>View details</button>
                </article>
              ))
            ) : (
              <div className="empty-state">No jobs are available right now.</div>
            )}
          </div>
        </section>

        <section className="home-section" id="jobs">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Open Roles</p>
              <h2>Latest jobs</h2>
            </div>
            <Link className="button button-outline-blue small-button" to="/user/register">
              Create user account
            </Link>
          </div>

          {message && <div className="alert success">{message}</div>}
          {error && <div className="alert error">{error}</div>}

          {selectedJob && (
            <section className="content-card detail-card" id="job-detail">
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
                onClick={applyToJob}
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

          <div className="jobs-grid">
            {filteredJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onApply={viewJob}
                applying={actionLoading === `view-${job.id}`}
                actionLabel="View Details"
              />
            ))}
            {!loading && !filteredJobs.length && <div className="empty-state">No jobs match your search.</div>}
          </div>
        </section>

        <section className="home-section" id="companies">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Companies</p>
              <h2>Hiring companies</h2>
            </div>
          </div>
          <div className="company-grid">
            {companies.slice(0, 6).map((company) => (
              <article className="company-card" key={company.id}>
                <h3>{company.name}</h3>
                <p>{company.description || 'Company profile not listed yet.'}</p>
                <span>{company.website || 'Website not listed'}</span>
              </article>
            ))}
            {!companies.length && !loading && <div className="empty-state">No companies are available right now.</div>}
          </div>
        </section>
      </main>
    </div>
  );
}
