export const APP_DEFAULTS = {
    solver: {
        budget: 10000,
        space: 1000,
    },
    generation: {
        priceRange: [1, 1000],
        sizeRange: [1, 100],
        priceZones: [
            {
                span_share: 0.5,
                mode: "exact",
                step: 10,
                resolution: 256,
                bias: 1,
            },
            {
                span_share: 0.5,
                mode: "geometric",
                step: 1,
                resolution: 256,
                bias: 1,
            },
        ],
        sizeZones: [
            {
                span_share: 0.3,
                mode: "u_shape",
                step: 1,
                resolution: 352,
                bias: 1,
            },
            {
                span_share: 0.7,
                mode: "geometric",
                step: 1,
                resolution: 256,
                bias: 1,
            },
        ],
        zoneDefaults: {
            span_share: 0.1,
            mode: "exact",
            step: 1,
            resolution: 256,
            bias: 1,
        },
        guardrails: {
            min_span: 0.001,
            min_step: 0.001,
            min_resolution: 2,
            min_bias: 0.001,
        },
    },
};
