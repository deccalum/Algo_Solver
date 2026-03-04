from concurrent import futures
from dataclasses import dataclass
import os

import grpc

import algsolver_pb2
import algsolver_pb2_grpc
from common import log
from generator import ProductGenerator
from mapper import to_proto
from solver import ProcurementOptimizer, SolverConfig

GenerateCatalogResponseMessage = getattr(algsolver_pb2, "GenerateCatalogResponse")
OptimizeCatalogResponseMessage = getattr(algsolver_pb2, "OptimizeCatalogResponse")
RunPipelineResponseMessage = getattr(algsolver_pb2, "RunPipelineResponse")
EstimateResponseMessage = getattr(algsolver_pb2, "EstimateResponse")


@dataclass
class OptimizeCatalogWire:
    status: str
    objective_value: float
    selected_count: int


@dataclass
class RunPipelineWire:
    status: str
    objective_value: float
    generated_count: int
    selected_count: int


class ProductEstimatorServicer(algsolver_pb2_grpc.ProductEstimatorServicer):
    @staticmethod
    def _use_transit_v2() -> bool:
        value = os.getenv("USE_TRANSIT_V2", "0").strip().lower()
        return value in {"1", "true", "yes", "on"}

    def GenerateCatalog(self, request, context):
        generator = ProductGenerator.from_proto_config(
            request.config, use_transit_v2=self._use_transit_v2()
        )
        products = generator.generate()
        response = GenerateCatalogResponseMessage(generated_count=len(products))
        response.products.extend(products)
        return response

    def OptimizeCatalog(self, request, context):
        products = list(request.products)
        optimizer = ProcurementOptimizer(
            SolverConfig(
                budget_constraint=request.config.generation.budget,
                space_constraint=request.config.generation.space,
            )
        )
        result = optimizer.optimize(products)
        payload = OptimizeCatalogWire(
            status=result.get("status", "UNKNOWN"),
            objective_value=float(result.get("objective_value", 0.0)),
            selected_count=len(result.get("product_totals", {})),
        )
        return to_proto(OptimizeCatalogResponseMessage, payload)

    def RunPipeline(self, request, context):
        generator = ProductGenerator.from_proto_config(
            request.config, use_transit_v2=self._use_transit_v2()
        )
        products = generator.generate()
        optimizer = ProcurementOptimizer(
            SolverConfig(
                budget_constraint=request.config.generation.budget,
                space_constraint=request.config.generation.space,
            )
        )
        result = optimizer.optimize(products)
        payload = RunPipelineWire(
            status=result.get("status", "UNKNOWN"),
            objective_value=float(result.get("objective_value", 0.0)),
            generated_count=len(products),
            selected_count=len(result.get("product_totals", {})),
        )
        return to_proto(RunPipelineResponseMessage, payload)

    def EstimateProducts(self, request, context):
        price_span = max(0.0, request.price_max - request.price_min)
        size_span = max(0.0, request.size_max - request.size_min)

        def zone_points(span: float, zone) -> int:
            if zone.mode.strip().lower() == "exact":
                step = max(1e-9, zone.step)
                return max(1, int(span / step) + 1)
            return max(1, int(zone.resolution))

        price_points = 0
        for zone in request.price_zones:
            price_points += zone_points(price_span * max(0.0, zone.span_share), zone)

        size_points = 0
        for zone in request.size_zones:
            size_points += zone_points(size_span * max(0.0, zone.span_share), zone)

        estimated = max(1, price_points) * max(1, size_points)
        return EstimateResponseMessage(
            estimated_products=estimated,
            strategy="zone_density_quick_estimate",
        )


def serve(host: str = "0.0.0.0", port: int = 50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    algsolver_pb2_grpc.add_ProductEstimatorServicer_to_server(
        ProductEstimatorServicer(), server
    )
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    log("grpc", f"gRPC estimator listening on {host}:{port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
