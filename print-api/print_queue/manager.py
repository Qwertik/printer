import time
import threading
import logging
from queue import Queue, Full, Empty
from typing import Optional, Dict, Callable

from .job import PrintJob, JobState

logger = logging.getLogger(__name__)


class JobQueue:
    def __init__(self, max_depth: int = 20, job_timeout: float = 30.0):
        self._queue: Queue[PrintJob] = Queue(maxsize=max_depth)
        self._jobs: Dict[str, PrintJob] = {}
        self._lock = threading.Lock()
        self._consumer_thread: Optional[threading.Thread] = None
        self._shutdown = threading.Event()
        self._printer_callback: Optional[Callable] = None
        self._job_timeout = job_timeout

    def start(self, printer_callback: Callable[[PrintJob], None]):
        """Start the consumer thread. printer_callback(job) does the actual printing."""
        self._printer_callback = printer_callback
        self._consumer_thread = threading.Thread(
            target=self._consumer_loop,
            name="print-consumer",
            daemon=True,
        )
        self._consumer_thread.start()
        logger.info("Print queue consumer started")

    def stop(self):
        """Signal shutdown and wait for consumer to finish current job."""
        self._shutdown.set()
        if self._consumer_thread and self._consumer_thread.is_alive():
            self._consumer_thread.join(timeout=self._job_timeout + 5)

    def submit(self, job: PrintJob) -> bool:
        """Submit a job. Returns True if accepted, False if queue is full."""
        try:
            self._queue.put_nowait(job)
        except Full:
            return False
        with self._lock:
            self._jobs[job.id] = job
        logger.info("Job %s queued (depth=%d)", job.id, self._queue.qsize())
        return True

    def get_job(self, job_id: str) -> Optional[PrintJob]:
        """Look up a job by ID for status queries."""
        with self._lock:
            return self._jobs.get(job_id)

    @property
    def depth(self) -> int:
        return self._queue.qsize()

    def _consumer_loop(self):
        """Single consumer: pulls jobs one at a time, calls printer_callback."""
        while not self._shutdown.is_set():
            try:
                job = self._queue.get(timeout=1.0)
            except Empty:
                continue

            job.state = JobState.PRINTING
            job.started_at = time.monotonic()
            logger.info("Job %s printing", job.id)

            exc_container: list = [None]

            def _do_print():
                try:
                    self._printer_callback(job)
                except Exception as e:
                    exc_container[0] = e

            worker = threading.Thread(target=_do_print, daemon=True)
            worker.start()
            worker.join(timeout=self._job_timeout)

            if worker.is_alive():
                job.state = JobState.ERROR
                job.error = f"Job timed out after {self._job_timeout}s"
                job.completed_at = time.monotonic()
                logger.error("Job %s timed out", job.id)
            elif exc_container[0]:
                job.state = JobState.ERROR
                job.error = str(exc_container[0])
                job.completed_at = time.monotonic()
                logger.error("Job %s failed: %s", job.id, exc_container[0])
            else:
                job.state = JobState.DONE
                job.completed_at = time.monotonic()
                logger.info("Job %s done", job.id)

            self._queue.task_done()
            self._evict_old_jobs()

    def _evict_old_jobs(self, max_age: float = 300.0):
        """Remove completed jobs older than max_age seconds from the lookup dict."""
        now = time.monotonic()
        with self._lock:
            stale = [
                jid
                for jid, j in self._jobs.items()
                if j.state in (JobState.DONE, JobState.ERROR)
                and j.completed_at
                and (now - j.completed_at) > max_age
            ]
            for jid in stale:
                del self._jobs[jid]
