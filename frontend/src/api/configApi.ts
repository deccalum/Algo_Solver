export async function fetchBootstrapConfig() {
    // TODO: Fetch from backend /api/config
    // For now, return default config
    return {
        demand_model: {
            tiers: []
        },
        markup_tiers: []
    };
}

export async function fetchGenerationConfig() {
    // TODO: Fetch generation config from backend
    return {};
}

export async function updateGenerationConfig(config: any) {
    // TODO: Update generation config on backend
    console.log('Updating generation config:', config);
}