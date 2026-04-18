import '../../styles/status-footer.css';

export function StatusFooter({ templateName, combinationCount }) {
  return (
    <footer className="status-footer">
      <div className="status-footer__items">
        <div className="status-footer__item">
          <span className="status-footer__dot" />
          <span className="status-footer__text--ok">autosave:on</span>
        </div>
        <span className="status-footer__sep status-footer__sm-only">&middot;</span>
        <span className="status-footer__sm-only">export:ready</span>
        <span className="status-footer__sep status-footer__sm-only">&middot;</span>
        <span className="status-footer__sm-only">solver_idle</span>
        {templateName && (
          <>
            <span className="status-footer__sep status-footer__md-only">&middot;</span>
            <span className="status-footer__md-only status-footer__text--truncate">template:{templateName}</span>
          </>
        )}
        {combinationCount != null && (
          <>
            <span className="status-footer__sep">&middot;</span>
            <span className="status-footer__text--bold">combos:{combinationCount.toLocaleString()}</span>
          </>
        )}
        <span className="status-footer__sep">&middot;</span>
        <span className="status-footer__text--ok">db:ok</span>
      </div>
    </footer>
  );
}
