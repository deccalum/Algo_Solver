import { useState, useEffect, useCallback } from 'react';
import { getHealth } from '../api/client';

export function useHealth(intervalMs = 30000) {
  const [dbConnected, setDbConnected] = useState(false);

  const check = useCallback(async () => {
    try {
      const res = await getHealth();
      setDbConnected(res.status === 'ok');
    } catch {
      setDbConnected(false);
    }
  }, []);

  useEffect(() => {
    check();
    const id = setInterval(check, intervalMs);
    return () => clearInterval(id);
  }, [check, intervalMs]);

  return { dbConnected };
}
