package com.algosolver.repository;

import com.algosolver.model.GenerationJobEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface GenerationJobRepository extends JpaRepository<GenerationJobEntity, Long> {
}
