# proto/__init__.py
from . import algsolver_pb2 as _pb2

AppConfig = getattr(_pb2, "AppConfig")
Demand = getattr(_pb2, "Demand")
Generation = getattr(_pb2, "Generation")
Guardrails = getattr(_pb2, "Guardrails")
Logistics = getattr(_pb2, "Logistics")
Markup = getattr(_pb2, "Markup")
Stock = getattr(_pb2, "Stock")
TransitMode = getattr(_pb2, "TransitMode")
Transit = getattr(_pb2, "Transit")
TransitResult = getattr(_pb2, "TransitResult")
Zone = getattr(_pb2, "Zone")
ZoneDefaults = getattr(_pb2, "ZoneDefaults")
ZoneSpec = getattr(_pb2, "ZoneSpec")
Product = getattr(_pb2, "Product")
EstimateRequest = getattr(_pb2, "EstimateRequest")
EstimateResponse = getattr(_pb2, "EstimateResponse")
GenerateCatalogRequest = getattr(_pb2, "GenerateCatalogRequest")
GenerateCatalogResponse = getattr(_pb2, "GenerateCatalogResponse")
OptimizeCatalogRequest = getattr(_pb2, "OptimizeCatalogRequest")
OptimizeCatalogResponse = getattr(_pb2, "OptimizeCatalogResponse")
RunPipelineRequest = getattr(_pb2, "RunPipelineRequest")
RunPipelineResponse = getattr(_pb2, "RunPipelineResponse")

__all__ = [
    "AppConfig", "Demand", "Generation", "Guardrails", "Logistics",
    "Markup", "Stock", "TransitMode", "Transit", "TransitResult", "Zone",
    "ZoneDefaults", "ZoneSpec", "Product",
    "EstimateRequest", "EstimateResponse",
    "GenerateCatalogRequest", "GenerateCatalogResponse",
    "OptimizeCatalogRequest", "OptimizeCatalogResponse",
    "RunPipelineRequest", "RunPipelineResponse",
]