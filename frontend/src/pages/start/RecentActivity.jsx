import { Icon } from '../../components/shared/Icon';
import '../../styles/recent-activity.css';

function EmptyState({ icon, title, subtitle }) {
  return (
    <div className="empty-state">
      <Icon name={icon} className="empty-state__icon" />
      <p className="empty-state__title">{title}</p>
      <p className="empty-state__subtitle">{subtitle}</p>
    </div>
  );
}

function RunItem({ run }) {
  const date = new Date(run.created_at);
  const ago = timeAgo(date);
  return (
    <div className="activity-item">
      <div>
        <p className="activity-item__name">
          {run.template_name || 'Custom'}
        </p>
        <p className="activity-item__meta">
          {run.item_count.toLocaleString()} items &middot; {ago}
        </p>
      </div>
      <span className="activity-item__id">{run.id.slice(0, 8)}</span>
    </div>
  );
}

function SolveItem({ solve }) {
  const date = new Date(solve.created_at);
  const ago = timeAgo(date);
  return (
    <div className="activity-item">
      <div>
        <p className="activity-item__name">
          {solve.objective_sense} {solve.objective_param}
        </p>
        <p className="activity-item__meta">
          {solve.selected_count} selected &middot; obj: {solve.objective_value?.toLocaleString() ?? '—'} &middot; {ago}
        </p>
      </div>
      <span className="activity-item__id">{solve.id.slice(0, 8)}</span>
    </div>
  );
}

function timeAgo(date) {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function RecentActivity({ runs, solves }) {
  return (
    <section className="recent-activity">
      <h2 className="recent-activity__title">
        RECENT ACTIVITY
      </h2>
      <div className="recent-activity__grid">
        {/* Generations */}
        <div>
          <div className="recent-activity__col-header">
            <span className="recent-activity__col-label">
              GENERATIONS
            </span>
          </div>
          {runs.length === 0 ? (
            <EmptyState
              icon="history"
              title="No generation runs yet"
              subtitle="Select a template above to begin"
            />
          ) : (
            <div className="recent-activity__list">
              {runs.map(r => <RunItem key={r.id} run={r} />)}
            </div>
          )}
        </div>
        {/* Solves */}
        <div>
          <div className="recent-activity__col-header">
            <span className="recent-activity__col-label">
              SOLVES
            </span>
          </div>
          {solves.length === 0 ? (
            <EmptyState
              icon="target"
              title="No solve runs yet"
              subtitle="Solves will appear here after optimization"
            />
          ) : (
            <div className="recent-activity__list">
              {solves.map(s => <SolveItem key={s.id} solve={s} />)}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
