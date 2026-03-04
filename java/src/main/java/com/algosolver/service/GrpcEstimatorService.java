package com.algosolver.service;

import com.algosolver.dto.EstimateProductsRequest;
import com.algosolver.dto.EstimateProductsResponse;
import com.algosolver.dto.EstimateZoneRequest;
import com.algosolver.grpc.EstimateRequest;
import com.algosolver.grpc.EstimateResponse;
import com.algosolver.grpc.ProductEstimatorGrpc;
import com.algosolver.grpc.ZoneSpec;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import jakarta.annotation.PreDestroy;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class GrpcEstimatorService {
    private final ManagedChannel channel;
    private final ProductEstimatorGrpc.ProductEstimatorBlockingStub blockingStub;

    public GrpcEstimatorService(
            @Value("${app.grpc.python.host}") String host,
            @Value("${app.grpc.python.port}") int port) {
        this.channel = ManagedChannelBuilder.forAddress(host, port)
                .usePlaintext()
                .build();
        this.blockingStub = ProductEstimatorGrpc.newBlockingStub(channel);
    }

    public EstimateProductsResponse estimateProducts(EstimateProductsRequest request) {
        EstimateRequest.Builder builder = EstimateRequest.newBuilder()
                .setPriceMin(request.priceMin())
                .setPriceMax(request.priceMax())
                .setSizeMin(request.sizeMin())
                .setSizeMax(request.sizeMax());

        for (EstimateZoneRequest zone : request.priceZones()) {
            builder.addPriceZones(toProtoZone(zone));
        }
        for (EstimateZoneRequest zone : request.sizeZones()) {
            builder.addSizeZones(toProtoZone(zone));
        }

        EstimateResponse response = blockingStub.estimateProducts(builder.build());
        return new EstimateProductsResponse(response.getEstimatedProducts(), response.getStrategy());
    }

    private ZoneSpec toProtoZone(EstimateZoneRequest zone) {
        return ZoneSpec.newBuilder()
                .setMode(zone.mode())
                .setSpanShare(zone.spanShare())
                .setResolution(zone.resolution())
                .setStep(zone.step())
                .setBias(zone.bias())
                .build();
    }

    @PreDestroy
    public void shutdown() {
        channel.shutdownNow();
    }
}
