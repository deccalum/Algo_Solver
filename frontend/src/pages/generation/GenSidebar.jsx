import { Icon } from '../../components/shared/Icon';
import '../../styles/gen-sidebar.css';

const SECTIONS = [
  { id: 'parameters',  icon: 'tune',       label: 'Parameters' },
  { id: 'filter',      icon: 'filter_alt', label: 'Filter' },
  { id: 'influences',  icon: 'insights',   label: 'Influences' },
  { id: 'constraints', icon: 'rule',       label: 'Constraints' },
];

const TEMPLATE_LABELS = {
  generic_product: 'Generic Product',
  solar_panel:     'Solar Panel',
  production_line: 'Production Line',
};

export function GenSidebar({
  activeSection,
  templateName,
  templates,
  paramCount,
  influenceCount,
  onSectionClick,
  onTemplateChange,
}) {
  return (
    <aside className="gen-sidebar">
      <nav className="gen-sidebar__nav">
        {SECTIONS.map(s => (
          <button
            key={s.id}
            className={`gen-sidebar__nav-btn ${
              activeSection === s.id
                ? 'gen-sidebar__nav-btn--active'
                : 'gen-sidebar__nav-btn--inactive'
            }`}
            onClick={() => onSectionClick(s.id)}
          >
            <Icon name={s.icon} className="gen-sidebar__nav-icon" />
            {s.label}
          </button>
        ))}
      </nav>

      {/* Template selector */}
      {templates?.length > 0 && (
        <div className="gen-sidebar__template">
          <span className="gen-sidebar__template-label">TEMPLATE</span>
          {templates.length === 1 ? (
            <span className="gen-sidebar__template-name">
              {TEMPLATE_LABELS[templateName] || templateName}
            </span>
          ) : (
            <select
              className="gen-sidebar__template-select"
              value={templateName || ''}
              onChange={e => onTemplateChange(e.target.value)}
            >
              {templates.map(t => (
                <option key={t.name} value={t.name}>
                  {TEMPLATE_LABELS[t.name] || t.name.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          )}
          <p className="gen-sidebar__template-meta">
            {paramCount} axes &middot; {influenceCount} influence{influenceCount !== 1 ? 's' : ''}
          </p>
        </div>
      )}
    </aside>
  );
}
