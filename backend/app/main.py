from fastapi import FastAPI

from app.api.v1.router import api_router as v1_router
from app.core.config import settings
from app.core.events import setup_event_handlers

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="面向证券异常波动、盘口异动与新闻风险的分析型后端服务。",
)

setup_event_handlers(app)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


app.include_router(v1_router, prefix=settings.api_prefix)
