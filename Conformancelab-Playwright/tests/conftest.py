# tests/conftest.py

import os
import subprocess
import sys
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from config.config import CONFIG
from utils.common.logger import (
    clear_logs_dir,
    set_current_test_id,
    setup_logger,
)


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args):
    """Remove old logs for the test run."""
    if os.getenv("PYTEST_XDIST_WORKER") is None:
        clear_logs_dir()


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Initialize the logger for this worker."""
    setup_logger()


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


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Create login state for tests that require an authenticated browser."""
    logger = setup_logger()
    config = session.config

    if hasattr(config, "workerinput"):
        return
    if getattr(config.option, "collectonly", False):
        return

    project_root = Path(__file__).resolve().parents[1]
    login_script = project_root / "utils" / "auth" / "login_once.py"
    print(f"Run login_once.py: {login_script}")

    try:
        subprocess.run([sys.executable, str(login_script)], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"login_once.py failed: {e}")
        pytest.exit("Login precondition failed", returncode=1)

    print("login_once.py completed successfully")


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
def browser() -> Generator[Browser, None, None]:
    with sync_playwright() as p:
        browser_type = getattr(p, CONFIG["browser_name"])
        browser = browser_type.launch(headless=CONFIG["headless"])
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    context = browser.new_context(storage_state=CONFIG["storage_state_path"])

    if CONFIG["tracing_enabled"]:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield context

    if CONFIG["tracing_enabled"]:
        context.tracing.stop(path=CONFIG["trace_output_path"])

    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    page = context.new_page()
    yield page
    page.close()
