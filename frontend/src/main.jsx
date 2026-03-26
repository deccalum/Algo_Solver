import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ModuleRegistry, AllCommunityModule } from "ag-grid-community";
import "./index.css";
import App from "./app/App.jsx";

ModuleRegistry.registerModules([AllCommunityModule]);
import ErrorBoundary from "./app/ErrorBoundary.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
