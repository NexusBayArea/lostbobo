from fastapi import APIRouter

from backend.runtime.discovery.graph import DiscoveryGraph
from backend.runtime.discovery.models import DiscoveryLink, DiscoveryNode

router = APIRouter(prefix="/api/v1/discoveries", tags=["discovery-graph"])

graph = DiscoveryGraph()


@router.post("/register")
async def register_discovery(node: DiscoveryNode):
    discovery_id = await graph.create_discovery(node)
    return {"discoveryId": discovery_id, "status": "registered"}


@router.post("/link")
async def link_discoveries(link: DiscoveryLink):
    await graph.link_discoveries(link)
    return {"status": "linked"}


@router.get("/search")
async def search_discoveries(query: dict):
    results = await graph.search(query)
    return {"discoveries": results}


@router.get("/leaderboard")
async def global_leaderboard(limit: int = 50):
    return await graph.search({"score_gt": 0.8, "limit": limit})
