import { useConfig } from "../hooks/useConfig";
import Home from "../ui/layout/Home";
import MainPage from "../ui/layout/MainPage";
import { useMemo } from "react";

export default function App() {
  const { data, error, loading } = useConfig();

  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const showMainPage = params.get("main") === "true";

  if (error && !showMainPage) {
    return (
      <main className="container">
        <h1>Algo Solver</h1>
        <p className="error">Could not load config: {error}</p>
        <p className="hint">Make sure backend is running on http://localhost:8080</p>
        <p className="hint">Use: run.bat backend or run.bat dev</p>
      </main>
    );
  }

  if (showMainPage) {
    return <MainPage />;
  }

  return <Home />;
}