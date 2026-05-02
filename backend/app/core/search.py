from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from app.core.config import SearchProvider, settings


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source_type: Literal["primary", "secondary", "unknown"] = "unknown"


@dataclass
class SearchConfig:
    provider: SearchProvider
    api_key: str = ""
    top_k: int = 8
    snippet_chars: int = 400
    extra: dict[str, Any] = field(default_factory=dict)


class SearchBackend(Protocol):
    def run(self, query: str, *, config: SearchConfig) -> list[SearchResult]: ...


def _truncate(text: str, n: int) -> str:
    text = (text or "").strip()
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


class TavilyBackend:
    def run(self, query: str, *, config: SearchConfig) -> list[SearchResult]:
        if not config.api_key:
            raise RuntimeError("Tavily requires an api key (TAVILY_API_KEY or per-request override)")
        try:
            from tavily import TavilyClient  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "tavily-python is not installed. Install it or pick a different search provider."
            ) from exc
        client = TavilyClient(api_key=config.api_key)
        response = client.search(query=query, max_results=config.top_k)
        results: list[SearchResult] = []
        for item in response.get("results", [])[: config.top_k]:
            results.append(
                SearchResult(
                    title=item.get("title", "") or "",
                    url=item.get("url", "") or "",
                    snippet=_truncate(item.get("content", "") or "", config.snippet_chars),
                )
            )
        return results


class SerperBackend:
    def run(self, query: str, *, config: SearchConfig) -> list[SearchResult]:
        if not config.api_key:
            raise RuntimeError("Serper requires an api key (SERPER_API_KEY or per-request override)")
        import httpx

        payload = {"q": query, "num": config.top_k}
        headers = {"X-API-KEY": config.api_key, "Content-Type": "application/json"}
        with httpx.Client(timeout=30) as client:
            response = client.post("https://google.serper.dev/search", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        results: list[SearchResult] = []
        for item in (data.get("organic") or [])[: config.top_k]:
            results.append(
                SearchResult(
                    title=item.get("title", "") or "",
                    url=item.get("link", "") or "",
                    snippet=_truncate(item.get("snippet", "") or "", config.snippet_chars),
                )
            )
        return results


class DuckDuckGoBackend:
    def run(self, query: str, *, config: SearchConfig) -> list[SearchResult]:
        # Support both the new package name (ddgs) and old (duckduckgo_search)
        try:
            from ddgs import DDGS  # type: ignore
        except ImportError:
            try:
                from duckduckgo_search import DDGS  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "Neither 'ddgs' nor 'duckduckgo-search' is installed. "
                    "Install with: pip install ddgs"
                ) from exc
        results: list[SearchResult] = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=config.top_k):
                results.append(
                    SearchResult(
                        title=item.get("title", "") or "",
                        url=item.get("href", "") or "",
                        snippet=_truncate(item.get("body", "") or "", config.snippet_chars),
                    )
                )
        return results


_BACKENDS: dict[SearchProvider, SearchBackend] = {
    "tavily": TavilyBackend(),
    "serper": SerperBackend(),
    "duckduckgo": DuckDuckGoBackend(),
}


def get_search(
    provider: SearchProvider | None = None,
    api_key: str | None = None,
    *,
    top_k: int | None = None,
    snippet_chars: int | None = None,
) -> tuple[SearchBackend, SearchConfig]:
    provider = provider or settings.search_provider
    if provider not in _BACKENDS:
        raise ValueError(f"Unknown search provider: {provider}")

    if api_key is None:
        if provider == "tavily":
            api_key = settings.tavily_api_key
        elif provider == "serper":
            api_key = settings.serper_api_key
        else:
            api_key = ""

    config = SearchConfig(
        provider=provider,
        api_key=api_key or "",
        top_k=top_k or settings.search_top_k,
        snippet_chars=snippet_chars or settings.search_snippet_chars,
    )
    return _BACKENDS[provider], config


def run_queries(
    queries: list[str],
    *,
    provider: SearchProvider | None = None,
    api_key: str | None = None,
    top_k: int | None = None,
    snippet_chars: int | None = None,
) -> list[SearchResult]:
    backend, config = get_search(provider, api_key, top_k=top_k, snippet_chars=snippet_chars)
    seen: set[str] = set()
    merged: list[SearchResult] = []
    for query in queries:
        try:
            hits = backend.run(query, config=config)
        except Exception as exc:  # noqa: BLE001
            merged.append(
                SearchResult(
                    title=f"[search error] {query}",
                    url="",
                    snippet=str(exc)[: config.snippet_chars],
                )
            )
            continue
        for hit in hits:
            key = hit.url or hit.title
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            merged.append(hit)
    return merged
