"""Versioned API router."""

from fastapi import APIRouter

from piecewise_linear.api.health import router as health_router
from piecewise_linear.api.points import router as points_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(points_router)
api_router.include_router(health_router)
