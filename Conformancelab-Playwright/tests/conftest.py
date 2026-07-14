import subprocess
import sys
from pathlib import Path
from typing import Generator
import pytest
from filelock import FileLock
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from config.config import CONFIG
from utils.common.logger import (
    set_current_test_id,
    setup_logger,
)

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Set the current test ID and log the start."""
    logger = setup_logger()
    set_current_test_id(item.nodeid)
    logger.info("Start test")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item, nextitem):
    """Reset the test ID and log the end."""
    logger = setup_logger()
    logger.info("End test")
    set_current_test_id(None)

def pytest_ignore_collect(collection_path, config):
    """Prevent -m webapp from triggering bulk setup, and the other way around."""
    markexpr = (getattr(config.option, "markexpr", "") or "").lower()
    path = Path(str(collection_path))
    parts = {part.lower() for part in path.parts}

    if "webapp" in markexpr and "bulk" not in markexpr and "bulk" in parts:
        return True
    if "bulk" in markexpr and "webapp" not in markexpr and "webapp" in parts:
        return True

    return False

@pytest.fixture(scope="session")
def authenticated_storage_state(
    tmp_path_factory: pytest.TempPathFactory,
    worker_id: str,
) -> str:
    """Create one authenticated storage state shared by all xdist workers."""
    if worker_id == "master":
        shared_dir = tmp_path_factory.getbasetemp()
    else:
        shared_dir = tmp_path_factory.getbasetemp().parent

    storage_state_path = shared_dir / "auth-state.json"
    lock_path = shared_dir / "auth-state.lock"

    with FileLock(str(lock_path)):
        if not storage_state_path.exists():
            project_root = Path(__file__).resolve().parents[1]
            login_script = project_root / "utils" / "auth" / "login_once.py"

            try:
                subprocess.run(
                    [
                        sys.executable,
                        str(login_script),
                        "--output",
                        str(storage_state_path),
                    ],
                    check=True,
                    cwd=project_root,
                )
            except subprocess.CalledProcessError as error:
                pytest.fail(f"Login precondition failed: {error}")

    return str(storage_state_path)


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    with sync_playwright() as p:
        browser_type = getattr(p, CONFIG["browser_name"])
        browser = browser_type.launch(headless=CONFIG["headless"])
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def context(
    browser: Browser,
    worker_id: str,
    authenticated_storage_state: str,
) -> Generator[BrowserContext, None, None]:
    trace_path = Path(CONFIG["trace_output_path"])
    trace_path = trace_path.with_name(f"{trace_path.stem}-{worker_id}{trace_path.suffix}")
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    context = browser.new_context(storage_state=authenticated_storage_state)

    if CONFIG["tracing_enabled"]:
        context.tracing.start(screenshots=True, snapshots=True, sources=True,)

    yield context

    if CONFIG["tracing_enabled"]:
        context.tracing.stop(path=str(trace_path))

    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    page = context.new_page()
    yield page
    page.close()
