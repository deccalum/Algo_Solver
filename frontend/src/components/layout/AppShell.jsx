import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { TopNav } from './TopNav';
import { SessionBar } from './SessionBar';
import { StatusFooter } from './StatusFooter';
import { useHealth } from '../../hooks/useHealth';
import { postRestart } from '../../api/client';
import '../../styles/app-shell.css';

export function AppShell() {
  const { dbConnected } = useHealth();
  const [sessionCtx, setSessionCtx] = useState({
    templateName:  null,
    runIndex:      null,
    combinationCount: null,
    // Persisted simulation state (survives page navigation)
    simLogs:    [],
    simDays:    [],
    simLedger:  [],
    simHorizon: null,
  });

  async function handleRestart() {
    try {
      await postRestart();
    } catch {
      // Expected — the server restarts mid-response, so fetch may throw
    }
  }

  return (
    <div className="app-shell">
      <TopNav />
      <SessionBar
        dbConnected={dbConnected}
        templateName={sessionCtx.templateName}
        runIndex={sessionCtx.runIndex}
        onRestart={handleRestart}
      />
      <main className="app-shell__main">
        <Outlet context={{ sessionCtx, setSessionCtx }} />
      </main>
      <StatusFooter
        templateName={sessionCtx.templateName}
        combinationCount={sessionCtx.combinationCount}
      />
    </div>
  );
}
