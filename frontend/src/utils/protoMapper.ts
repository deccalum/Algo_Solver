import {
    AppConfig,
    Product,
    GenerateCatalogRequest,
    GenerateCatalogResponse,
    OptimizeCatalogRequest,
    OptimizeCatalogResponse,
    RunPipelineRequest,
    RunPipelineResponse,
    EstimateRequest,
    EstimateResponse
} from '../types/proto';

/**
 * Simple mapper utilities for converting between protobuf dict format and TypeScript types
 * Since the protobuf_to_dict function produces JSON-compatible structures that match our TypeScript interfaces,
 * these are primarily type assertions and validation helpers.
 */

export function parseAppConfig(data: any): AppConfig {
    // Basic validation - in a real app you'd want more thorough validation
    if (!data || typeof data !== 'object') {
        throw new Error('Invalid AppConfig data');
    }
    return data as AppConfig;
}

export function parseProduct(data: any): Product {
    if (!data || typeof data !== 'object' || !data.id) {
        throw new Error('Invalid Product data');
    }
    return data as Product;
}

export function parseProducts(data: any[]): Product[] {
    if (!Array.isArray(data)) {
        throw new Error('Invalid products array');
    }
    return data.map(parseProduct);
}

export function parseGenerateCatalogResponse(data: any): GenerateCatalogResponse {
    if (!data || typeof data !== 'object') {
        throw new Error('Invalid GenerateCatalogResponse data');
    }
    return {
        ...data,
        products: parseProducts(data.products || [])
    };
}

export function parseOptimizeCatalogResponse(data: any): OptimizeCatalogResponse {
    if (!data || typeof data !== 'object') {
        throw new Error('Invalid OptimizeCatalogResponse data');
    }
    return data as OptimizeCatalogResponse;
}

export function parseRunPipelineResponse(data: any): RunPipelineResponse {
    if (!data || typeof data !== 'object') {
        throw new Error('Invalid RunPipelineResponse data');
    }
    return data as RunPipelineResponse;
}

export function parseEstimateResponse(data: any): EstimateResponse {
    if (!data || typeof data !== 'object') {
        throw new Error('Invalid EstimateResponse data');
    }
    return data as EstimateResponse;
}

// Utility to create request objects
export function createGenerateCatalogRequest(config?: AppConfig): GenerateCatalogRequest {
    return {
        config: config || {} as AppConfig
    };
}

export function createOptimizeCatalogRequest(products: Product[], config?: AppConfig): OptimizeCatalogRequest {
    return {
        config: config || {} as AppConfig,
        products
    };
}

export function createRunPipelineRequest(): RunPipelineRequest {
    return {};
}

export function createEstimateRequest(
    priceMin: number,
    priceMax: number,
    sizeMin: number,
    sizeMax: number,
    priceZones: any[] = [],
    sizeZones: any[] = []
): EstimateRequest {
    return {
        price_min: priceMin,
        price_max: priceMax,
        size_min: sizeMin,
        size_max: sizeMax,
        price_zones: priceZones,
        size_zones: sizeZones
    };
}