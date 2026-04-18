import { useState } from 'react';
import '../../styles/session-bar.css';

export function SessionBar({ dbConnected = false, templateName = null, runIndex = null, onRestart }) {
  const [state, setState] = useState('idle'); // idle | waiting | ok | err

  async function handleRestart() {
    setState('waiting');
    try {
      await onRestart?.();
      setState('ok');
    } catch {
      setState('err');
    } finally {
      setTimeout(() => setState('idle'), 4000);
    }
  }

  return (
    <div className="session-bar">
      <div className="session-bar__statuses">
        <div className="session-bar__item">
          <span className={`session-bar__dot ${dbConnected ? 'session-bar__dot--ok' : 'session-bar__dot--err'}`} />
          <span className={dbConnected ? 'session-bar__label--ok' : 'session-bar__label--err'}>
            <span className="session-bar__label-prefix">DB: </span>{dbConnected ? 'OK' : 'ERR'}
          </span>
        </div>
        <div className="session-bar__item session-bar__item--engine">
          <span className={`session-bar__dot ${dbConnected ? 'session-bar__dot--ok' : 'session-bar__dot--warn'}`} />
          <span className={dbConnected ? 'session-bar__label--ok' : 'session-bar__label--warn'}>
            Engine: {dbConnected ? 'Active' : 'Idle'}
          </span>
        </div>
        <div className="session-bar__item session-bar__item--template">
          <span className={`session-bar__dot ${templateName ? 'session-bar__dot--accent' : 'session-bar__dot--warn'}`} />
          <span className="session-bar__label--muted">
            <span className="session-bar__label-prefix">Template: </span>{templateName || 'UNSET'}
          </span>
        </div>
      </div>

      <div className="session-bar__actions">
        {runIndex && (
          <div className="session-bar__run">RUN: {runIndex}</div>
        )}
        <button
          className={`session-bar__restart-btn ${state !== 'idle' ? `session-bar__restart-btn--${state}` : ''}`}
          onClick={handleRestart}
          disabled={state === 'waiting'}
          title="Kill and restart the Python backend (use if the solver gets stuck)"
        >
          {state === 'waiting' ? '⟳' : state === 'ok' ? '✓' : state === 'err' ? '✗' : '↺'} RESTART
        </button>
      </div>
    </div>
  );
}
