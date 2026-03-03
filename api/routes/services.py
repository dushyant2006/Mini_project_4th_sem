
from fastapi import APIRouter, HTTPException
import sys, os

ROOT = os.path.dirname(os.path.dirname(
       os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rca.graph.graph_builder import (
    ServiceDependencyGraph,
    SERVICE_DEPENDENCIES,
    SERVICE_METADATA
)

router = APIRouter()

# Create graph once when API starts
graph = ServiceDependencyGraph()


@router.get("/graph", summary="Full service dependency graph")
async def get_service_graph():
    """
    Returns the complete service dependency graph.
    Use this to visualize your microservices architecture.
    """
    nodes = []
    edges = []

    # Build nodes
    for service, meta in SERVICE_METADATA.items():
        nodes.append({
            "id":          service,
            "label":       service,
            "tier":        meta.get("tier"),
            "criticality": meta.get("criticality"),
            "team":        meta.get("team"),
        })

    # Build edges
    for service, deps in SERVICE_DEPENDENCIES.items():
        for dep in deps:
            edges.append({
                "source": service,
                "target": dep,
                "label":  "calls"
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_services": len(nodes),
        "total_dependencies": len(edges),
    }


@router.get("/list", summary="List all services")
async def list_services():
    """Returns all services with their metadata"""
    services = []
    for name, meta in SERVICE_METADATA.items():
        services.append({
            "name":         name,
            "tier":         meta.get("tier"),
            "criticality":  meta.get("criticality"),
            "team":         meta.get("team"),
            "dependencies": SERVICE_DEPENDENCIES.get(name, []),
            "callers":      graph.get_direct_callers(name),
        })
    return {
        "total":    len(services),
        "services": services
    }


@router.get("/{service_name}/blast-radius",
            summary="Blast radius for a service failure")
async def get_blast_radius(service_name: str):
    """
    Shows which services would be affected if this
    service fails.

    Example: /services/payment-service/blast-radius
    """
    if service_name not in SERVICE_METADATA:
        raise HTTPException(
            status_code=404,
            detail=f"Service '{service_name}' not found"
        )

    blast = graph.get_blast_radius(service_name)
    return blast


@router.get("/{service_name}/dependencies",
            summary="Service dependency chain")
async def get_dependencies(service_name: str):
    """Returns full upstream and downstream for a service"""
    if service_name not in SERVICE_METADATA:
        raise HTTPException(
            status_code=404,
            detail=f"Service '{service_name}' not found"
        )

    return {
        "service":    service_name,
        "calls":      SERVICE_DEPENDENCIES.get(service_name, []),
        "called_by":  graph.get_direct_callers(service_name),
        "all_upstream":   graph.get_upstream_services(service_name),
        "all_downstream": graph.get_downstream_services(service_name),
    }