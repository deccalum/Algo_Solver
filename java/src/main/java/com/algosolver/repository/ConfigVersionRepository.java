package com.algosolver.repository;

import com.algosolver.model.ConfigVersionEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface ConfigVersionRepository extends JpaRepository<ConfigVersionEntity, Long> {
    Optional<ConfigVersionEntity> findByConfigDocument_IdAndVersionNum(long configDocumentId, int versionNum);
}
