export default function JobCard({ job, onApply, applying, actionLabel = 'Apply' }) {
  const companyName = job.company?.name || `Company #${job.company_id}`;

  return (
    <article className="job-card">
      <div className="job-card-header">
        <div>
          <h3>{job.title}</h3>
          <p>{companyName}</p>
        </div>
        <span className="job-badge">{job.is_active === false ? 'Closed' : 'Open'}</span>
      </div>
      <div className="job-meta">
        <span>{job.location || 'Location not listed'}</span>
        <span>{job.salary || 'Salary not listed'}</span>
      </div>
      <p className="job-description">{job.description || 'No description provided by the recruiter.'}</p>
      {onApply && (
        <button className="button button-primary full-width" onClick={() => onApply(job)} disabled={applying}>
          {applying ? 'Loading...' : actionLabel}
        </button>
      )}
    </article>
  );
}
