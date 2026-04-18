import { Icon } from '../../components/shared/Icon';
import '../../styles/template-card.css';

const TEMPLATE_ICONS = {
  generic_product: { icon: 'apps', color: '#5b35d5', bg: 'rgba(91, 53, 213, 0.1)' },
  production_line: { icon: 'settings_suggest', color: '#d97706', bg: '#fffbeb' },
  solar_panel: { icon: 'wb_sunny', color: '#0ea5c9', bg: '#ecfeff' },
};

export function TemplateCard({ template, onSelect }) {
  const visual = TEMPLATE_ICONS[template.name] || TEMPLATE_ICONS.generic_product;
  const isDefault = template.name === 'generic_product';

  return (
    <div
      className="template-card"
      onClick={() => onSelect(template.name)}
    >
      <div className="template-card__header">
        <div className="template-card__icon-box" style={{ backgroundColor: visual.bg }}>
          <Icon name={visual.icon} style={{ color: visual.color }} />
        </div>
        {isDefault && (
          <span className="template-card__badge">
            DEFAULT
          </span>
        )}
      </div>

      <h3 className="template-card__title">
        {template.name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
      </h3>

      <button
        className={`template-card__button ${isDefault ? 'template-card__button--default' : 'template-card__button--alt'}`}
        style={isDefault ? {} : { borderColor: visual.color, color: visual.color }}
        onClick={(e) => { e.stopPropagation(); onSelect(template.name); }}
      >
        Select Template
      </button>
    </div>
  );
}
