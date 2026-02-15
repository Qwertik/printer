import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any, Dict


class JobState(Enum):
    QUEUED = "queued"
    PRINTING = "printing"
    DONE = "done"
    ERROR = "error"


@dataclass
class PrintJob:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    payload: Dict[str, Any] = field(default_factory=dict)
    state: JobState = JobState.QUEUED
    created_at: float = field(default_factory=time.monotonic)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    client_ip: Optional[str] = None
    is_raw: bool = False
