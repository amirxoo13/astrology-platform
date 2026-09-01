from fastapi import APIRouter

from app.api.v1.endpoints import planets, houses, chart, eclipses, lunar_phase
from app.api.v1.endpoints import nodes, special_points
from app.api.v1.endpoints import stars, aspects

router = APIRouter(prefix="/api/v1", tags=["v1"])

router.include_router(planets.router)
router.include_router(houses.router)
router.include_router(chart.router)
router.include_router(stars.router)
router.include_router(eclipses.router)
router.include_router(lunar_phase.router)
router.include_router(nodes.router)
router.include_router(special_points.router)
router.include_router(aspects.router)
