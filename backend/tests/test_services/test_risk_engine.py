from app.models.schemas import MarketSignalRequest, NewsItem, NewsRiskRequest, OrderBookSnapshot, PricePoint
from app.services.risk_engine import analyze_market, analyze_news


def test_analyze_market():
    request = MarketSignalRequest(
        symbol="SZ300750",
        price_series=[
            PricePoint(timestamp="2026-05-01T09:30:00", price=100.0, volume=1000),
            PricePoint(timestamp="2026-05-01T09:31:00", price=101.0, volume=1200),
            PricePoint(timestamp="2026-05-01T09:32:00", price=99.0, volume=3000),
            PricePoint(timestamp="2026-05-01T09:33:00", price=98.0, volume=5000),
            PricePoint(timestamp="2026-05-01T09:34:00", price=97.0, volume=8000),
        ],
        order_book=[
            OrderBookSnapshot(timestamp="2026-05-01T09:32:00", best_bid=99.0, best_ask=99.5, bid_volume=500, ask_volume=2000, cancel_ratio=0.3, large_order_ratio=0.2),
            OrderBookSnapshot(timestamp="2026-05-01T09:33:00", best_bid=98.0, best_ask=98.6, bid_volume=400, ask_volume=2500, cancel_ratio=0.5, large_order_ratio=0.3),
            OrderBookSnapshot(timestamp="2026-05-01T09:34:00", best_bid=97.0, best_ask=97.5, bid_volume=300, ask_volume=3000, cancel_ratio=0.6, large_order_ratio=0.4),
        ],
    )
    result = analyze_market(request.symbol, request.price_series, request.order_book)
    assert 0 <= result.risk_score <= 100
    assert result.symbol == "SZ300750"
    assert len(result.factors) > 0


def test_analyze_news():
    request = NewsRiskRequest(
        symbol="SZ300750",
        news=[
            NewsItem(timestamp="2026-05-01T08:00:00", title="问询函", source="交易所", summary="公司收到问询"),
        ],
    )
    result = analyze_news(request)
    assert 0 <= result.risk_score <= 100
    assert result.symbol == "SZ300750"
