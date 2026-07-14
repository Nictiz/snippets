import pytest
from utils.common.logger import (clear_logs_dir, setup_logger)

@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session: pytest.Session) -> None:
    """Remove logs once, before tests start."""
    config = session.config

    # xdist voert deze hook ook binnen iedere worker uit.
    # Alleen het centrale pytest-proces mag logs verwijderen.
    if hasattr(config, "workerinput"):
        return

    # Een collection-check hoort bestaande testlogs niet te verwijderen.
    if config.option.collectonly:
        return

    clear_logs_dir()


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Initialize the logger for this worker."""
    setup_logger()

def pytest_addoption(parser):
    """Add project CLI options early, so pytest always recognizes them."""
    parser.addoption(
        "--branch",
        action="store",
        default=None,
        help="Override the branch for bulk tests",
    )
    parser.addoption(
        "--bulk-profile",
        action="store",
        default=None,
        help="Bulk profile from config/bulk-testsets.toml or config/bulk.local.toml",
    )
    parser.addoption(
        "--info-standard",
        action="append",
        default=None,
        help="Override the profile with one or more information standards for bulk tests",
    )
    parser.addoption(
        "--input_dir",
        action="store",
        default=None,
        help="Override the input directory for bulk tests",
    )


