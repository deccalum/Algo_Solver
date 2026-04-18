import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { StartPage } from './pages/start/StartPage';
import { GenerationPage } from './pages/generation/GenerationPage';
import { SolverPage } from './pages/solver/SolverPage';
import { DatabasePage } from './pages/database/DatabasePage';
import { SimulationPage } from './pages/simulation/SimulationPage';
import { SolarPage } from './pages/solar/SolarPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<StartPage />} />
          <Route path="generation" element={<GenerationPage />} />
          <Route path="solver" element={<SolverPage />} />
          <Route path="database" element={<DatabasePage />} />
          <Route path="simulation" element={<SimulationPage />} />
          <Route path="solar" element={<SolarPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
