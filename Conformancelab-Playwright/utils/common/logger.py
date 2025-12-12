# utils/common/logger.py
import logging
import os
from typing import Optional
import threading
import time
import glob

_log_lock = threading.Lock()
LOG_DIR = "test-results/logs"

def get_worker_id() -> str:
    return os.environ.get("PYTEST_XDIST_WORKER", "master")

def logs_dir() -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    return LOG_DIR

def clear_logs_dir():
    """Verwijder alle *.log in de logs-map aan het begin van de testrun (controller only)."""
    d = logs_dir()
    for p in glob.glob(os.path.join(d, "*.log")):
        try:
            os.remove(p)
        except PermissionError:
            # kleine delay en nog eens proberen
            time.sleep(0.1)
            try:
                os.remove(p)
            except Exception:
                pass

class TestIdFilter(logging.Filter):
    """Voegt test_id toe aan elk logrecord."""
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
    """Maak thread-safe logger met per-worker bestand en test_id."""
    worker_id = get_worker_id()
    logger_name = f"{name}-{worker_id}"

    if log_file is None:
        # elk worker krijgt eigen bestand
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

        # per-worker bestand, en we willen per run overschrijven
        fileh = logging.FileHandler(log_file, mode="w", encoding="utf-8", delay=True)
        fileh.setFormatter(fmt_file)

        # thread-safe emit (meestal niet nodig per worker, maar kan geen kwaad)
        orig_emit = fileh.emit
        def thread_safe_emit(record):
            with _log_lock:
                orig_emit(record)
        fileh.emit = thread_safe_emit

        # filters toevoegen
        logger.addFilter(_test_id_filter)

        def add_worker_info(record):
            record.worker = worker_id
            return True
        logger.addFilter(add_worker_info)

        logger.addHandler(fileh)

    return logger

def set_current_test_id(test_id: Optional[str]):
    _test_id_filter.set_test_id(test_id)
