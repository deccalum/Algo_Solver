import { AppConfig, GenerateCatalogResponse } from '../types/proto';

export async function fetchBootstrapConfig(): Promise<AppConfig> {
    const res = await fetch('/api/config');
    if (!res.ok) {
        throw new Error(`Failed to fetch config: ${res.status}`);
    }
    return res.json();
}

export async function fetchGenerationConfig(): Promise<AppConfig> {
    // Same as bootstrap config for now
    return fetchBootstrapConfig();
}

export async function updateGenerationConfig(config: AppConfig): Promise<void> {
    // TODO: Implement config update endpoint
    console.log('Updating generation config:', config);
}

export async function generateCatalog(count?: number): Promise<GenerateCatalogResponse> {
    const url = count ? `/api/generate-catalog?count=${count}` : '/api/generate-catalog';
    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
    });
    if (!res.ok) {
        throw new Error(`Failed to generate catalog: ${res.status}`);
    }
    return res.json();
}

export async function checkApiStatus(): Promise<{ status: string }> {
    const res = await fetch('/api/db/status');
    if (!res.ok) {
        throw new Error(`API not connected: ${res.status}`);
    }
    return res.json();
}