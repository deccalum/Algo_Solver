import type {
  TemplateInfo, CountResponse, GenerateRequest, GenerateResponse,
  SolveRequest, SolveResponse, RunSummary, RunDetail, RunItems,
  SolveSummary, SolveDetail, TableInfo, ColumnInfo, TableData,
  SimulateRequest, SimulateResponse, SimStreamMessage,
  SolarPshResponse, SolarSolveRequest, SolarSolveResponse,
} from './types';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`GET ${path}: ${res.status} ${text}`);
  }
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`POST ${path}: ${res.status} ${text}`);
  }
  return res.json();
}

function qs(params: Record<string, any>): string {
  const s = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null) s.set(k, String(v));
  }
  const str = s.toString();
  return str ? `?${str}` : '';
}

// ── Health ──
export const getHealth = () => get<{ status: string }>('/api/health');
export const postRestart = () => post<{ status: string }>('/api/admin/restart', {});

// ── Templates ──
export const getTemplates = () => get<TemplateInfo[]>('/api/templates');
export const getTemplate = (name: string) => get<TemplateInfo>(`/api/templates/${name}`);

// ── Generation ──
export const postCount = (req: GenerateRequest) => post<CountResponse>('/api/count', req);
export const postGenerate = (req: GenerateRequest) => post<GenerateResponse>('/api/generate', req);

// ── Solver ──
export const postSolve = (req: SolveRequest) => post<SolveResponse>('/api/solve', req);

// ── Runs ──
export const getRuns = (limit = 50, offset = 0) =>
  get<RunSummary[]>(`/api/runs${qs({ limit, offset })}`);
export const getRun = (id: string) => get<RunDetail>(`/api/runs/${id}`);
export const getRunItems = (id: string, limit = 100, offset = 0) =>
  get<RunItems>(`/api/runs/${id}/items${qs({ limit, offset })}`);

// ── Solves ──
export const getSolves = (limit = 50, offset = 0) =>
  get<SolveSummary[]>(`/api/solves${qs({ limit, offset })}`);
export const getSolve = (id: string) => get<SolveDetail>(`/api/solves/${id}`);

// ── Solar ──
export const getSolarPsh = (lat: number, tilt?: number, azimuth?: number, date?: string) =>
  get<SolarPshResponse>(`/api/solar/psh${qs({ lat, tilt, azimuth, date })}`);

export const postSolarSolve = (req: SolarSolveRequest) =>
  post<SolarSolveResponse>('/api/solar/solve', req);

// ── Simulation ──
export const postSimulate = (req: SimulateRequest) =>
  post<SimulateResponse>('/api/simulate/run', req);

export async function streamSimulate(
  req: SimulateRequest,
  onMessage: (msg: SimStreamMessage) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch('/api/simulate/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
    signal,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`POST /api/simulate/stream: ${res.status} ${text}`);
  }
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        onMessage(JSON.parse(trimmed) as SimStreamMessage);
      } catch {
        // skip malformed lines
      }
    }
  }
  // flush any remaining buffer
  if (buffer.trim()) {
    try { onMessage(JSON.parse(buffer.trim()) as SimStreamMessage); } catch { /* ignore */ }
  }
}

// ── Database browser ──
export const getTables = () => get<TableInfo[]>('/api/database/tables');
export const getTableSchema = (name: string) =>
  get<ColumnInfo[]>(`/api/database/tables/${encodeURIComponent(name)}/schema`);
export const getTableData = (name: string, limit = 100, offset = 0, filters?: string) =>
  get<TableData>(`/api/database/tables/${encodeURIComponent(name)}/data${qs({ limit, offset, filters })}`);
