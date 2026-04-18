import { useRef, useEffect } from 'react';
import '../../styles/solver-console.css';

export function SolverConsole({ logs }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <aside className="solver-console">
      <div className="solver-console__panel">
        {/* Header */}
        <div className="solver-console__header">
          <div className="solver-console__header-left">
            <div className="solver-console__dots">
              <div className="solver-console__dot solver-console__dot--red" />
              <div className="solver-console__dot solver-console__dot--yellow" />
              <div className="solver-console__dot solver-console__dot--green" />
            </div>
            <span className="solver-console__label">
              Solver Console
            </span>
          </div>
        </div>

        {/* Tab bar */}
        <div className="solver-console__tabs">
          <button className="solver-console__tab">
            LIVE LOG
          </button>
        </div>

        {/* Log content */}
        <div
          ref={scrollRef}
          className="solver-console__log"
        >
          {logs.length === 0 && (
            <div className="solver-console__empty">Waiting for solver run...</div>
          )}
          {logs.map((log, i) => (
            <div key={i} className="solver-console__line">
              <span className="solver-console__time">[{log.time}]</span>
              <span className={`solver-console__level solver-console__level--${log.level}`}>
                {log.level}
              </span>
              <span className="solver-console__msg">{log.message}</span>
            </div>
          ))}
          <div className="solver-console__cursor">_</div>
        </div>

        {/* Input */}
        <div className="solver-console__input-area">
          <div className="solver-console__input-row">
            <span className="solver-console__prompt">&gt;</span>
            <input
              className="solver-console__input"
              placeholder="Type solver command..."
              readOnly
            />
          </div>
        </div>
      </div>
    </aside>
  );
}
