from __future__ import annotations

import logging
import traceback

from app.domains.skills import storage
from app.domains.skills.schemas import DistillRequest, JobRecord
from app.graphs.skill_distillation import run as run_graph


log = logging.getLogger(__name__)


def start_job(request: DistillRequest) -> JobRecord:
    """Create the job record on disk. Does NOT execute the graph."""
    return storage.create_job(request.name, request)


def execute_job(job_id: str) -> None:
    """Run the LangGraph pipeline for an already-created job.

    Intended to be called from a FastAPI BackgroundTask. Any exception is
    written back into the job record.
    """
    record = storage.load_job(job_id)
    if record is None:
        log.error("execute_job: job not found: %s", job_id)
        return
    try:
        run_graph({"record": record})
    except Exception as exc:  # noqa: BLE001
        log.exception("Skill distillation failed for job %s", job_id)
        latest = storage.load_job(job_id) or record
        latest.error = f"{exc}\n\n{traceback.format_exc()}"
        storage.mark_failed(latest, latest.error)


def get_job(job_id: str) -> JobRecord | None:
    return storage.load_job(job_id)
