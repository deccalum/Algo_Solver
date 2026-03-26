import {
    GenerateCatalogRequest,
    GenerateCatalogResponse,
    OptimizeCatalogRequest,
    OptimizeCatalogResponse,
    RunPipelineRequest,
    RunPipelineResponse,
    EstimateRequest,
    EstimateResponse
} from '../types/proto';
import {
    parseGenerateCatalogResponse,
    parseOptimizeCatalogResponse,
    parseRunPipelineResponse,
    parseEstimateResponse
} from '../utils/protoMapper';

const API_BASE = '/api';

export async function generateCatalog(request: GenerateCatalogRequest): Promise<GenerateCatalogResponse> {
    const res = await fetch(`${API_BASE}/generate-catalog`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });
    if (!res.ok) {
        throw new Error(`Generate catalog failed: ${res.status}`);
    }
    const data = await res.json();
    return parseGenerateCatalogResponse(data);
}

export async function optimizeCatalog(request: OptimizeCatalogRequest): Promise<OptimizeCatalogResponse> {
    const res = await fetch(`${API_BASE}/optimize-catalog`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });
    if (!res.ok) {
        throw new Error(`Optimize catalog failed: ${res.status}`);
    }
    const data = await res.json();
    return parseOptimizeCatalogResponse(data);
}

export async function runPipeline(request: RunPipelineRequest = {}): Promise<RunPipelineResponse> {
    const res = await fetch(`${API_BASE}/pipeline/run-dev`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });
    if (!res.ok) {
        throw new Error(`Run pipeline failed: ${res.status}`);
    }
    const data = await res.json();
    return parseRunPipelineResponse(data);
}

export async function estimateProducts(request: EstimateRequest): Promise<EstimateResponse> {
    const res = await fetch(`${API_BASE}/estimate-products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });
    if (!res.ok) {
        throw new Error(`Estimate products failed: ${res.status}`);
    }
    const data = await res.json();
    return parseEstimateResponse(data);
}