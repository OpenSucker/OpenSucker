from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, status
from fastapi.responses import PlainTextResponse

from app.domains.skills import service, storage
from app.domains.skills.schemas import DistillRequest


router = APIRouter()


@router.post("/distill", status_code=status.HTTP_202_ACCEPTED)
def distill(request: DistillRequest, background_tasks: BackgroundTasks) -> dict:
    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="name 不能为空")
    record = service.start_job(request)
    background_tasks.add_task(service.execute_job, record.job_id)
    return {
        "job_id": record.job_id,
        "slug": record.slug,
        "status": record.status,
    }


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    record = service.get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    return record.model_dump(mode="json")


@router.get("/jobs/{job_id}/skill", response_class=PlainTextResponse)
def download_skill(job_id: str) -> str:
    record = service.get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    content = storage.read_skill(record.slug)
    if content is None:
        raise HTTPException(status_code=404, detail="skill not ready")
    return content


@router.get("/jobs/{job_id}/research/{dimension}", response_class=PlainTextResponse)
def download_research(job_id: str, dimension: str) -> str:
    record = service.get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    report = storage.load_cached_report(record.slug, dimension)  # type: ignore[arg-type]
    if report is None:
        raise HTTPException(status_code=404, detail="research not available")
    return report.summary_md


@router.post("/uploads/{slug}")
async def upload_materials(slug: str, files: list[UploadFile]) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="至少上传一个文件")
    ids: list[str] = []
    for f in files:
        content = await f.read()
        upload_id = storage.save_upload(slug, f.filename or "upload.txt", content)
        ids.append(upload_id)
    return {"slug": slug, "upload_ids": ids}


@router.get("/cache")
def list_cache() -> list[dict]:
    return [entry.model_dump(mode="json") for entry in storage.list_cache()]
