package com.algosolver.dto;

import com.algosolver.model.JobStatus;

import java.time.Instant;

public record JobStatusResponse(
        long jobId,
        long configId,
        int version,
        JobStatus status,
        String output,
        String outputFile,
        String error,
        Instant createdAt,
        Instant startedAt,
        Instant finishedAt) {
}
