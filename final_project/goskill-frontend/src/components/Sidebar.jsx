export default function Sidebar({ title, sections, activeSection, onSectionChange, onLogout }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-title">{title}</div>
      <div className="sidebar-menu">
        {sections.map((section) => (
          <button
            key={section.id}
            className={`sidebar-item ${activeSection === section.id ? 'active' : ''}`}
            onClick={() => onSectionChange(section.id)}
          >
            <span>{section.icon}</span>
            {section.label}
          </button>
        ))}
      </div>
      <button className="sidebar-logout" onClick={onLogout}>
        Logout
      </button>
    </aside>
  );
}
