# utils/common/logger.py
import logging
import os
from typing import Optional
import threading
import time
import glob
from pathlib import Path

_log_lock = threading.Lock()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "test-results" / "logs"

def get_worker_id() -> str:
    return os.environ.get("PYTEST_XDIST_WORKER", "master")

def logs_dir() -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    return LOG_DIR

def clear_logs_dir():
    """Remove all *.log files in the logs directory at the start of the test run."""
    d = logs_dir()
    for p in glob.glob(os.path.join(d, "*.log")):
        try:
            os.remove(p)
        except PermissionError:
            # Brief delay, then try once more.
            time.sleep(0.1)
            try:
                os.remove(p)
            except Exception:
                pass

class TestIdFilter(logging.Filter):
    """Add test_id to every log record."""
    def __init__(self):
        super().__init__()
        self._test_id: Optional[str] = None

    def set_test_id(self, test_id: Optional[str]):
        self._test_id = test_id

    def filter(self, record):
        record.test_id = self._test_id or "-"
        return True

_test_id_filter = TestIdFilter()

def setup_logger(name: str = "test-logger", log_file: Optional[str] = None) -> logging.Logger:
    """Create a thread-safe logger with a per-worker file and test_id."""
    worker_id = get_worker_id()
    logger_name = f"{name}-{worker_id}"

    if log_file is None:
        # Each worker gets its own file.
        log_file = os.path.join(logs_dir(), f"test-{worker_id}.log")

    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        fmt_console = logging.Formatter(
            "[%(levelname)s][%(worker)s][%(test_id)s] %(message)s"
        )
        fmt_file = logging.Formatter(
            "%(asctime)s [%(levelname)s][%(worker)s][%(test_id)s] %(message)s"
        )

        console = logging.StreamHandler()
        console.setFormatter(fmt_console)
        logger.addHandler(console)

        # Per-worker file; overwrite on each run.
        fileh = logging.FileHandler(log_file, mode="w", encoding="utf-8", delay=True)
        fileh.setFormatter(fmt_file)

        # Thread-safe emit.
        orig_emit = fileh.emit
        def thread_safe_emit(record):
            with _log_lock:
                orig_emit(record)
        fileh.emit = thread_safe_emit

        # Add filters.
        logger.addFilter(_test_id_filter)

        def add_worker_info(record):
            record.worker = worker_id
            return True
        logger.addFilter(add_worker_info)

        logger.addHandler(fileh)

    return logger

def set_current_test_id(test_id: Optional[str]):
    _test_id_filter.set_test_id(test_id)
