from __future__ import annotations

import json
import re
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from app.core.config import settings
from app.domains.skills.schemas import (
    DIMENSIONS,
    CacheEntry,
    DimensionName,
    DimensionReport,
    DistillRequest,
    JobProgress,
    JobRecord,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(name: str) -> str:
    """Convert any name to a filesystem-safe ASCII slug.

    Strategy:
    1. NFKD → ASCII (works for Latin / accented names)
    2. pypinyin  (works for CJK characters)
    3. Raw CJK chars with unsafe chars stripped (final fallback)
    """
    # Step 1: ASCII normalization (fast path for Latin names)
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    if slug:
        return slug

    # Step 2: Pinyin for CJK names (e.g. 查理·芒格 → cha-li-mang-ge)
    try:
        from pypinyin import lazy_pinyin  # type: ignore
        pinyin = lazy_pinyin(name)
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", "-".join(pinyin)).strip("-").lower()
        if slug:
            return slug
    except ImportError:
        pass

    # Step 3: Keep CJK chars directly (valid on all modern filesystems)
    safe = re.sub(r'[\s·/\\:*?"<>|]+', "-", name.strip())
    return safe or "unnamed"


def ensure_dirs() -> None:
    for path in (
        settings.data_dir,
        settings.jobs_dir,
        settings.research_cache_dir,
        settings.uploads_dir,
        settings.skills_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _job_path(job_id: str) -> Path:
    return settings.jobs_dir / f"{job_id}.json"


def create_job(name: str, request: DistillRequest) -> JobRecord:
    ensure_dirs()
    job_id = uuid.uuid4().hex[:16]
    slug = slugify(name)
    record = JobRecord(
        job_id=job_id,
        slug=slug,
        name=name,
        status="queued",
        request=request,
        started_at=_now(),
    )
    save_job(record)
    return record


def save_job(record: JobRecord) -> None:
    ensure_dirs()
    path = _job_path(record.job_id)
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")


def load_job(job_id: str) -> JobRecord | None:
    path = _job_path(job_id)
    if not path.exists():
        return None
    return JobRecord.model_validate_json(path.read_text(encoding="utf-8"))


def append_progress(record: JobRecord, stage: str, message: str) -> None:
    record.current_stage = stage
    record.progress.append(JobProgress(timestamp=_now(), stage=stage, message=message))
    save_job(record)


def mark_failed(record: JobRecord, error: str) -> None:
    record.status = "failed"
    record.error = error
    record.finished_at = _now()
    save_job(record)


def mark_done(record: JobRecord, skill_path: Path) -> None:
    record.status = "done"
    record.skill_path = str(skill_path)
    record.finished_at = _now()
    save_job(record)


# ---------- research cache ----------

def cache_dir(slug: str) -> Path:
    path = settings.research_cache_dir / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_path(slug: str, dimension: DimensionName) -> Path:
    return cache_dir(slug) / f"{dimension}.md"


def is_cache_fresh(slug: str, dimension: DimensionName) -> bool:
    path = cache_path(slug, dimension)
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age < timedelta(days=settings.cache_ttl_days)


def load_cached_report(slug: str, dimension: DimensionName) -> DimensionReport | None:
    path = cache_path(slug, dimension)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    return DimensionReport(dimension=dimension, summary_md=text, cached=True)


def write_cached_report(slug: str, report: DimensionReport) -> None:
    path = cache_path(slug, report.dimension)
    path.write_text(report.summary_md, encoding="utf-8")


def list_cache() -> list[CacheEntry]:
    ensure_dirs()
    entries: list[CacheEntry] = []
    for slug_dir in sorted(settings.research_cache_dir.iterdir()) if settings.research_cache_dir.exists() else []:
        if not slug_dir.is_dir():
            continue
        dims = [p.stem for p in slug_dir.glob("*.md") if p.stem in DIMENSIONS]
        if not dims:
            continue
        latest_mtime = max(p.stat().st_mtime for p in slug_dir.glob("*.md"))
        entries.append(
            CacheEntry(
                slug=slug_dir.name,
                dimensions=sorted(dims),
                updated_at=datetime.fromtimestamp(latest_mtime, tz=timezone.utc),
            )
        )
    return entries


# ---------- uploads ----------

def uploads_dir(slug: str) -> Path:
    path = settings.uploads_dir / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(slug: str, filename: str, content: bytes) -> str:
    path = uploads_dir(slug)
    upload_id = uuid.uuid4().hex[:12]
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", filename)
    target = path / f"{upload_id}_{safe_name}"
    target.write_bytes(content)
    return upload_id


def load_uploads(slug: str, upload_ids: Iterable[str] | None = None) -> str:
    path = uploads_dir(slug)
    parts: list[str] = []
    ids = set(upload_ids or [])
    for file in sorted(path.iterdir()):
        if not file.is_file():
            continue
        prefix = file.name.split("_", 1)[0]
        if ids and prefix not in ids:
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        parts.append(f"### {file.name}\n\n{text}")
    return "\n\n".join(parts)


# ---------- final skill ----------

def skill_dir(slug: str) -> Path:
    path = settings.skills_dir / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_skill(slug: str, content: str) -> Path:
    path = skill_dir(slug) / "SKILL.md"
    path.write_text(content, encoding="utf-8")
    return path


def read_skill(slug: str) -> str | None:
    path = skill_dir(slug) / "SKILL.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def write_synthesis(slug: str, payload: dict) -> Path:
    path = skill_dir(slug) / "synthesis.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
