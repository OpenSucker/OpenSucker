from fastapi import APIRouter

from app.api.v1.endpoints import (
    analysis,
    anet,
    counters,
    health,
    intelligence,
    monitoring,
    orders,
    personality,
    play,
    quiz,
    skills,
    terminals,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(terminals.router, prefix="/terminals", tags=["terminals"])
api_router.include_router(counters.router, prefix="/counters", tags=["counters"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["intelligence"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(anet.router, prefix="/anet", tags=["agent-network"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
api_router.include_router(personality.router, prefix="/personality", tags=["personality"])
api_router.include_router(play.router, prefix="/play", tags=["play"])
