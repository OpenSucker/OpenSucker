from fastapi import APIRouter

from app.graphs.risk_workflow import run_composite_risk_workflow
from app.models.schemas import (
    CompositeRiskRequest,
    MarketSignalRequest,
    NewsRiskRequest,
    RiskAnalysisResponse,
    SampleScenarioResponse,
)
from app.services.risk_engine import analyze_market, analyze_news
from app.services.sample_data import get_high_risk_scenario

router = APIRouter()


@router.post("/analysis/market", response_model=RiskAnalysisResponse, summary="市场风险分析")
def analyze_market_endpoint(request: MarketSignalRequest) -> RiskAnalysisResponse:
    return analyze_market(
        symbol=request.symbol,
        price_series=request.price_series,
        order_book=request.order_book,
    )


@router.post("/analysis/news", response_model=RiskAnalysisResponse, summary="新闻风险分析")
def analyze_news_endpoint(request: NewsRiskRequest) -> RiskAnalysisResponse:
    return analyze_news(request)


@router.post("/analysis/composite", response_model=RiskAnalysisResponse, summary="综合风险分析")
def analyze_composite_endpoint(request: CompositeRiskRequest) -> RiskAnalysisResponse:
    return run_composite_risk_workflow(request)


@router.get("/analysis/scenarios/high-risk", response_model=SampleScenarioResponse, summary="获取高风险样例场景")
def get_high_risk_scenario_endpoint() -> SampleScenarioResponse:
    return get_high_risk_scenario()
