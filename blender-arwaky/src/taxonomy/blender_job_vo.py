from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from .core_types_vo import ErrorMessage, JobId, JobState, Progress, ProviderName, ResultUrl

# ============================================================
# JOB CONSTANTS
# ============================================================

JOB_STATE_PENDING: Final[JobState] = JobState("PENDING")
JOB_STATE_RUNNING: Final[JobState] = JobState("RUNNING")
JOB_STATE_COMPLETED: Final[JobState] = JobState("COMPLETED")
JOB_STATE_FAILED: Final[JobState] = JobState("FAILED")

PROVIDER_HYPER3D_NAME: Final[ProviderName] = ProviderName("tool_generate_hyper3d")
PROVIDER_HUNYUAN_NAME: Final[ProviderName] = ProviderName("hunyuan")


# ============================================================
# JOB ENTITY/VO
# ============================================================


@dataclass
class JobStatus:
    """Mutable tracking of an async background job."""

    job_id: JobId
    status: JobState  # JOB_STATE_PENDING, JOB_STATE_RUNNING, JOB_STATE_COMPLETED, JOB_STATE_FAILED
    progress: Progress = field(default_factory=lambda: Progress(0.0))
    result_url: ResultUrl | None = None
    error: ErrorMessage | None = None

    def mark_running(self) -> None:
        self.status = JOB_STATE_RUNNING
        self.progress = Progress(0.0)

    def mark_completed(self, result_url: ResultUrl | None = None) -> None:
        self.status = JOB_STATE_COMPLETED
        self.progress = Progress(100.0)
        self.result_url = result_url

    def mark_failed(self, error: ErrorMessage) -> None:
        self.status = JOB_STATE_FAILED
        self.error = error


# ============================================================
# JOB FACTORIES
# ============================================================


def create_job_id(raw: str) -> JobId:
    return JobId(raw)


def create_progress(raw: float) -> Progress:
    if raw < 0.0 or raw > 100.0:
        raise ValueError("progress must be between 0.0 and 100.0")
    return Progress(raw)
