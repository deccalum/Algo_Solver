package com.algosolver.service;

import com.algosolver.exception.ResourceNotFoundException;
import com.algosolver.model.ConfigVersionEntity;
import com.algosolver.repository.ConfigVersionRepository;
import org.springframework.stereotype.Service;

@Service
public class ConfigStoreService {
    private final ConfigVersionRepository configVersionRepository;

    public ConfigStoreService(ConfigVersionRepository configVersionRepository) {
        this.configVersionRepository = configVersionRepository;
    }

    public ConfigVersionEntity requireConfigVersion(long configId, int version) {
        return configVersionRepository
                .findByConfigDocument_IdAndVersionNum(configId, version)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Config version not found for configId=" + configId + " version=" + version));
    }
}
