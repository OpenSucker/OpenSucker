"""
Document fetcher for skill distillation research.

Two-stage pipeline:
  1. DDGS寻址检索 — callers use DDGS with filetype:pdf operators to find URLs
  2. 下载与解析   — this module downloads the URLs and extracts clean text

Supported formats:
  - PDF  → PyMuPDF (primary) with pdfplumber fallback
  - HTML → httpx + BeautifulSoup, main-content extraction
  - other → best-effort plain text extraction
"""
from __future__ import annotations

import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

_PDF_EXTENSIONS = {".pdf"}
_PDF_URL_PATTERNS = re.compile(
    r"(\.pdf($|\?|#)|/pdf/|filetype=pdf|/download.*pdf|arxiv\.org/pdf/)",
    re.IGNORECASE,
)


def is_pdf_url(url: str) -> bool:
    """Heuristically decide whether a URL points to a PDF."""
    if not url:
        return False
    path = urlparse(url).path.lower()
    if any(path.endswith(ext) for ext in _PDF_EXTENSIONS):
        return True
    return bool(_PDF_URL_PATTERNS.search(url))


# ---------------------------------------------------------------------------
# PDF parsing
# ---------------------------------------------------------------------------

def _parse_pdf_bytes(content: bytes, max_chars: int) -> str:
    """
    Extract text from raw PDF bytes.

    Tries PyMuPDF first (faster, better layout preservation),
    falls back to pdfplumber for scanned/complex PDFs.
    """
    # --- PyMuPDF (fitz) ---
    try:
        import fitz  # type: ignore  # PyMuPDF
        doc = fitz.open(stream=content, filetype="pdf")
        pages: list[str] = []
        for page in doc:
            pages.append(page.get_text("text"))  # type: ignore[arg-type]
        doc.close()
        raw = "\n".join(pages)
        if raw.strip():
            return _clean_text(raw, max_chars)
    except Exception:  # noqa: BLE001
        pass

    # --- pdfplumber fallback ---
    try:
        import pdfplumber  # type: ignore
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        raw = "\n".join(pages)
        if raw.strip():
            return _clean_text(raw, max_chars)
    except Exception:  # noqa: BLE001
        pass

    return "[PDF: 解析失败，可能是扫描件或加密文件]"


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

def _parse_html(html: str, max_chars: int) -> str:
    """Extract main readable text from an HTML string."""
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        # Crude regex fallback when bs4 is absent
        text = re.sub(r"<[^>]+>", " ", html)
        return _clean_text(text, max_chars)

    soup = BeautifulSoup(html, "html.parser")

    # Remove boilerplate tags
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "aside", "form", "noscript", "iframe"]):
        tag.decompose()

    # Prefer semantic content containers
    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find(id=re.compile(r"content|main|article", re.IGNORECASE))
        or soup.find(class_=re.compile(r"content|main|article|post", re.IGNORECASE))
        or soup.find("body")
        or soup
    )
    raw = main.get_text(separator="\n")
    return _clean_text(raw, max_chars)


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def _clean_text(text: str, max_chars: int) -> str:
    """Collapse excessive whitespace, strip junk lines, truncate."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            lines.append(stripped)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    if len(text) <= max_chars:
        return text

    # Truncate at a sentence boundary when possible
    truncated = text[:max_chars]
    last_period = max(
        truncated.rfind("。"),
        truncated.rfind(". "),
        truncated.rfind(".\n"),
    )
    if last_period > max_chars * 0.8:
        truncated = truncated[: last_period + 1]

    return truncated + "\n[…内容已截断]"


# ---------------------------------------------------------------------------
# Network fetch
# ---------------------------------------------------------------------------

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def fetch_document(
    url: str,
    *,
    timeout: int = 25,
    max_chars: int = 8000,
) -> str:
    """
    Fetch a URL and return its text content (Markdown-ish plain text).

    Returns an error string (never raises) so callers can safely ignore failures.
    """
    if not url:
        return ""
    try:
        import httpx
    except ImportError:
        return "[fetch失败: httpx 未安装]"

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers=_HEADERS,
        ) as client:
            resp = client.get(url)

        if resp.status_code == 403:
            return "[fetch失败: 403 Forbidden]"
        if resp.status_code != 200:
            return f"[fetch失败: HTTP {resp.status_code}]"

        content_type = resp.headers.get("content-type", "").lower()

        # --- PDF (by URL or content-type) ---
        if is_pdf_url(url) or "application/pdf" in content_type:
            return _parse_pdf_bytes(resp.content, max_chars)

        # --- HTML ---
        if "text/html" in content_type or "text/plain" in content_type:
            return _parse_html(resp.text, max_chars)

        # --- Unknown: try PDF first, then HTML ---
        if resp.content[:4] == b"%PDF":
            return _parse_pdf_bytes(resp.content, max_chars)
        return _parse_html(resp.text, max_chars)

    except httpx.TimeoutException:
        return f"[fetch失败: 超时 ({timeout}s)]"
    except Exception as exc:  # noqa: BLE001
        return f"[fetch失败: {exc}]"


# ---------------------------------------------------------------------------
# Parallel fetching (for multiple URLs in one research call)
# ---------------------------------------------------------------------------

def fetch_documents_parallel(
    urls: list[str],
    *,
    max_workers: int = 4,
    timeout: int = 25,
    max_chars: int = 6000,
    delay_between: float = 0.3,
) -> dict[str, str]:
    """
    Fetch multiple URLs in parallel.

    Returns a dict mapping url → extracted text.
    Guaranteed to return an entry for every input URL (empty string on error).
    """
    if not urls:
        return {}

    results: dict[str, str] = {u: "" for u in urls}

    def _fetch(url: str) -> tuple[str, str]:
        time.sleep(delay_between)  # be gentle with servers
        return url, fetch_document(url, timeout=timeout, max_chars=max_chars)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_fetch, u): u for u in urls}
        for future in as_completed(futures):
            url, text = future.result()
            results[url] = text

    return results


# ---------------------------------------------------------------------------
# PDF-specific query builder (DDGS filetype:pdf operator)
# ---------------------------------------------------------------------------

# Dimensions where fetching primary-source PDFs adds the most value
PDF_PRIORITY_DIMENSIONS = {"writings", "conversations", "decisions", "external_views"}


def build_pdf_queries(base_queries: list[str], dimension: str) -> list[str]:
    """
    Given the standard DDGS queries for a dimension, append filetype:pdf variants.

    Only the first 2 base queries get a PDF variant to stay within budget.
    Returns just the NEW pdf queries (callers append to their existing list).
    """
    if dimension not in PDF_PRIORITY_DIMENSIONS:
        return []
    return [f"{q} filetype:pdf" for q in base_queries[:2] if q.strip()]
