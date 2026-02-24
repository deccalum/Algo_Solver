import { useEffect, useState } from "react";
import { fetchBootstrapConfig } from "../api/configApi";

export function useConfig() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadConfig() {
      try {
        const payload = await fetchBootstrapConfig();
        if (isMounted) {
          setData(payload);
          setError("");
        }
      } catch (e) {
        if (isMounted) {
          setError(e instanceof Error ? e.message : "Failed to load config");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadConfig();

    return () => {
      isMounted = false;
    };
  }, []);

  return { data, error, loading };
}
