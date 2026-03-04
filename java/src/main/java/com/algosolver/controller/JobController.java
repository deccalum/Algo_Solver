package com.algosolver.controller;

import com.algosolver.dto.EstimateProductsRequest;
import com.algosolver.dto.EstimateProductsResponse;
import com.algosolver.dto.GenerateJobRequest;
import com.algosolver.dto.JobStatusResponse;
import com.algosolver.service.GrpcEstimatorService;
import com.algosolver.service.JobService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/jobs")
public class JobController {
    private final JobService jobService;
    private final GrpcEstimatorService grpcEstimatorService;

    public JobController(JobService jobService, GrpcEstimatorService grpcEstimatorService) {
        this.jobService = jobService;
        this.grpcEstimatorService = grpcEstimatorService;
    }

    @PostMapping("/generate")
    public JobStatusResponse generate(@Valid @RequestBody GenerateJobRequest request) {
        return jobService.createGenerateJob(request.configId(), request.version());
    }

    @GetMapping("/{jobId}")
    public JobStatusResponse getJob(@PathVariable long jobId) {
        return jobService.getJobStatus(jobId);
    }

    @PostMapping("/estimate")
    public EstimateProductsResponse estimate(@Valid @RequestBody EstimateProductsRequest request) {
        return grpcEstimatorService.estimateProducts(request);
    }
}
