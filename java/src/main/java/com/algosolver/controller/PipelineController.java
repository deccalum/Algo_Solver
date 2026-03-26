package com.algosolver.controller;

import com.algosolver.grpc.ProductEstimatorGrpc;
import com.algosolver.grpc.ProductEstimatorGrpc.ProductEstimatorBlockingStub;
import com.algosolver.grpc.RunPipelineRequest;
import com.algosolver.grpc.RunPipelineResponse;
import io.grpc.StatusRuntimeException;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class PipelineController {

    private final ProductEstimatorBlockingStub stub;

    // Spring injects host + port from application.properties
    public PipelineController(
            @Value("${app.grpc.python.host}") String host,
            @Value("${app.grpc.python.port}") int port) {
        ManagedChannel channel = ManagedChannelBuilder
                .forAddress(host, port)
                .usePlaintext()
                .build();
        this.stub = ProductEstimatorGrpc.newBlockingStub(channel);
    }

    @PostMapping("/api/pipeline/run-dev")
    public ResponseEntity<Map<String, Object>> runDev() {
        try {
            RunPipelineResponse response = stub.runPipeline(
                    RunPipelineRequest.newBuilder().build());
            return ResponseEntity.ok(Map.of(
                    "status", response.getStatus(),
                    "generated_count", response.getGeneratedCount(),
                    "selected_count", response.getSelectedCount(),
                    "objective_value", response.getObjectiveValue()));
        } catch (StatusRuntimeException e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of(
                    "error", "Python gRPC service unavailable on localhost:60051",
                    "grpc_status", String.valueOf(e.getStatus().getCode())));
        }
    }
}