import { generateCatalog, estimateProducts, createEstimateRequest } from './protoApi';

// Example of using the protobuf APIs
export async function exampleGenerateCatalog() {
    const response = await generateCatalog({ config: {} });
    return response.generated_count;
}

export async function exampleEstimateProducts() {
    const request = createEstimateRequest(1, 10000, 0.1, 100000);
    const response = await estimateProducts(request);
    return response.estimated_products;
}

// Legacy example (can be removed)
export async function exampleFunction(params: any): Promise<number> {
    const res = await fetch("/api/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
    });
    return res.json();
}