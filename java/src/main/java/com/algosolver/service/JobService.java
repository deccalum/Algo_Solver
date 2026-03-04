package com.algosolver.service;

import com.algosolver.dto.JobStatusResponse;
import com.algosolver.exception.ResourceNotFoundException;
import com.algosolver.model.ConfigVersionEntity;
import com.algosolver.model.GenerationJobEntity;
import com.algosolver.model.JobStatus;
import com.algosolver.repository.GenerationJobRepository;
import jakarta.annotation.PreDestroy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Service
public class JobService {
    private final GenerationJobRepository generationJobRepository;
    private final ConfigStoreService configStoreService;
    private final PythonRunnerService pythonRunnerService;
    private final ExecutorService jobExecutor;

    public JobService(
            GenerationJobRepository generationJobRepository,
            ConfigStoreService configStoreService,
            PythonRunnerService pythonRunnerService) {
        this.generationJobRepository = generationJobRepository;
        this.configStoreService = configStoreService;
        this.pythonRunnerService = pythonRunnerService;
        this.jobExecutor = Executors.newFixedThreadPool(2);
    }

    @Transactional
    public JobStatusResponse createGenerateJob(long configId, int version) {
        ConfigVersionEntity configVersion = configStoreService.requireConfigVersion(configId, version);

        GenerationJobEntity job = new GenerationJobEntity();
        job.setConfigDocument(configVersion.getConfigDocument());
        job.setConfigVersion(configVersion);
        job.setStatus(JobStatus.QUEUED);
        job.setCreatedAt(Instant.now());

        GenerationJobEntity saved = generationJobRepository.save(job);
        long jobId = saved.getId();
        jobExecutor.submit(() -> runJob(jobId));

        return toResponse(saved);
    }

    @Transactional(readOnly = true)
    public JobStatusResponse getJobStatus(long jobId) {
        GenerationJobEntity job = generationJobRepository.findById(jobId)
                .orElseThrow(() -> new ResourceNotFoundException("Job not found: " + jobId));
        return toResponse(job);
    }

    private void runJob(long jobId) {
        GenerationJobEntity running = generationJobRepository.findById(jobId)
                .orElseThrow(() -> new ResourceNotFoundException("Job not found: " + jobId));

        running.setStatus(JobStatus.RUNNING);
        running.setStartedAt(Instant.now());
        running.setErrorText(null);
        generationJobRepository.save(running);

        try {
            PythonRunnerService.RunResult result = pythonRunnerService.runGenerate();

            GenerationJobEntity finished = generationJobRepository.findById(jobId)
                    .orElseThrow(() -> new ResourceNotFoundException("Job not found: " + jobId));

            finished.setOutputText(result.output());
            finished.setFinishedAt(Instant.now());
            if (result.exitCode() == 0) {
                finished.setStatus(JobStatus.COMPLETED);
                finished.setErrorText(null);
            } else {
                finished.setStatus(JobStatus.FAILED);
                finished.setErrorText("Python exited with code " + result.exitCode());
            }
            generationJobRepository.save(finished);
        } catch (RuntimeException ex) {
            GenerationJobEntity failed = generationJobRepository.findById(jobId)
                    .orElseThrow(() -> new ResourceNotFoundException("Job not found: " + jobId));
            failed.setStatus(JobStatus.FAILED);
            failed.setFinishedAt(Instant.now());
            failed.setErrorText(ex.getMessage());
            generationJobRepository.save(failed);
        }
    }

    private JobStatusResponse toResponse(GenerationJobEntity job) {
        return new JobStatusResponse(
                job.getId(),
                job.getConfigDocument().getId(),
                job.getConfigVersion().getVersionNum(),
                job.getStatus(),
                job.getOutputText(),
                job.getOutputFile(),
                job.getErrorText(),
                job.getCreatedAt(),
                job.getStartedAt(),
                job.getFinishedAt());
    }

    @PreDestroy
    public void shutdownExecutor() {
        jobExecutor.shutdown();
    }
}
