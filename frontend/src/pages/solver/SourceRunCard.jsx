import { Icon } from '../../components/shared/Icon';
import '../../styles/source-run-card.css';

export function SourceRunCard({ run }) {
  if (!run) return null;

  return (
    <section className="source-run">
      <div className="source-run__heading">
        <h3 className="source-run__title">
          Source Workspace
        </h3>
      </div>
      <div className="source-run__card">
        <div className="source-run__card-body">
          <div className="source-run__icon-wrap">
            <Icon name="database" />
          </div>
          <div>
            <h4 className="source-run__name">
              {run.template_name || 'Custom'}
            </h4>
            <p className="source-run__meta">
              {run.item_count.toLocaleString()} items &middot;
              {run.params.length} axes &middot;
              run #{run.id.slice(0, 8)}
            </p>
          </div>
        </div>
        <div className="source-run__footer">
          {run.params.map((p, i) => (
            <span key={p.name}>
              {i > 0 && <span className="source-run__param-sep">|</span>}
              {p.name}: <span className="source-run__param-value">{p.dist_kwargs?.resolution ?? 10} vals</span>
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
