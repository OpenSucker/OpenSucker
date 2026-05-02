from app.models.schemas import CompositeRiskRequest, MarketSignalRequest, NewsItem, NewsRiskRequest, OrderBookSnapshot, PricePoint, SampleScenarioResponse


def get_high_risk_scenario() -> SampleScenarioResponse:
    market = MarketSignalRequest(
        symbol="SZ300750",
        price_series=[
            PricePoint(timestamp="2026-05-01T09:30:00", price=182.5, volume=210000),
            PricePoint(timestamp="2026-05-01T09:31:00", price=181.9, volume=225000),
            PricePoint(timestamp="2026-05-01T09:32:00", price=180.6, volume=318000),
            PricePoint(timestamp="2026-05-01T09:33:00", price=179.8, volume=452000),
            PricePoint(timestamp="2026-05-01T09:34:00", price=177.2, volume=780000),
        ],
        order_book=[
            OrderBookSnapshot(timestamp="2026-05-01T09:32:00", best_bid=180.5, best_ask=180.8, bid_volume=45000, ask_volume=68000, cancel_ratio=0.43, large_order_ratio=0.31),
            OrderBookSnapshot(timestamp="2026-05-01T09:33:00", best_bid=179.7, best_ask=180.1, bid_volume=38000, ask_volume=92000, cancel_ratio=0.58, large_order_ratio=0.4),
            OrderBookSnapshot(timestamp="2026-05-01T09:34:00", best_bid=177.0, best_ask=177.6, bid_volume=21000, ask_volume=105000, cancel_ratio=0.65, large_order_ratio=0.47),
        ],
    )
    news = NewsRiskRequest(
        symbol="SZ300750",
        news=[
            NewsItem(timestamp="2026-05-01T08:40:00", title="公司收到交易所问询函", source="交易所", summary="涉及业绩异常波动与信息披露风险"),
            NewsItem(timestamp="2026-05-01T08:55:00", title="核心股东计划减持", source="公告", summary="减持规模较大，市场情绪承压"),
            NewsItem(timestamp="2026-05-01T09:10:00", title="市场传出供应链违约风险", source="媒体", summary="相关传闻尚待公司澄清"),
        ],
    )
    return SampleScenarioResponse(name="high_risk", market=market, news=news)


def get_composite_request() -> CompositeRiskRequest:
    scenario = get_high_risk_scenario()
    return CompositeRiskRequest(market=scenario.market, news=scenario.news)
