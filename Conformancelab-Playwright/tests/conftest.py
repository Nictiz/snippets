# tests/conftest.py

import os
import sys
import ast
import pytest
import subprocess
import urllib.parse
from pathlib import Path
from typing import Generator
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from config.config import CONFIG
from utils.common.logger import setup_logger, set_current_test_id, clear_logs_dir
from .helpers import generate_test_urls


# =============================================================================
# INITIALIZATION HOOKS
# =============================================================================

@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args):
    """Verwijder oude logs vóór de test run (alleen controller)."""
    if os.getenv("PYTEST_XDIST_WORKER") is None:
        clear_logs_dir()


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Initialiseer logger voor deze worker."""
    setup_logger()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Stel current test-id in en log start."""
    logger = setup_logger()
    set_current_test_id(item.nodeid)
    logger.info("Start test")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item, nextitem):
    """Reset test-id en log einde."""
    logger = setup_logger()
    logger.info("Einde test")
    set_current_test_id(None)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Draait één keer in de controller – herbouw testsets en login."""
    logger = setup_logger()
    config = session.config

    # Alleen de controller mag dit uitvoeren
    if hasattr(config, "workerinput"):
        return

    project_root = Path(__file__).resolve().parents[2]

    # --- 1. Generate unieke combinaties ---
    extract_script = project_root / "Conformancelab-testen" / "utils" / "common" / "extract_testset.py"
    print(f"Run extract_testset.py: {extract_script}")

    inputdir = config.getoption("--input_dir") or INPUT_DIR_STR
    inputdir = Path(project_root) / inputdir
    info_standards = config.getoption("--info-standard") or INFO_STANDARD
    branch = config.getoption("--branch") or BRANCH

    # Command opbouwen
    cmd = [
        sys.executable,
        str(extract_script),
        "--root", str(inputdir),
        "--branch", str(branch),
        "--folders"
    ] + info_standards

    try:
        subprocess.run(cmd, check=True)
        print("extract_testset.py succesvol uitgevoerd")
    except subprocess.CalledProcessError as e:
        logger.error(f"extract_testset.py faalde: {e}")
        pytest.exit("Extract testsets mislukt; test run afgebroken.", returncode=1)

    # --- 2. Login éénmalig ---
    login_script = project_root / "Conformancelab-testen" / "utils" / "auth" / "login_once.py"
    print(f"Run login_once.py: {login_script}")

    try:
        subprocess.run([sys.executable, str(login_script)], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"login_once.py faalde: {e}")
        pytest.exit("Login preconditie faalde", returncode=1)

    print("login_once.py succesvol uitgevoerd")


# =============================================================================
# DEFAULTS INLEZEN UIT test_regressie.py
# =============================================================================

def _read_test_defaults():
    """Lees BRANCH en INFO_STANDARD uit test_regressie.py."""
    script = Path(__file__).parent / "test_regressie.py"

    try:
        node = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    except Exception as e:
        raise RuntimeError(f"Kan test_regressie.py niet parsen: {e}")

    branch = None
    info_std = None
    input_dir = None

    for n in node.body:
        if not isinstance(n, ast.Assign):
            continue

        for target in n.targets:
            if not isinstance(target, ast.Name):
                continue

            # --- BRANCH ---
            if target.id == "BRANCH":
                if isinstance(n.value, ast.Constant):
                    branch = str(n.value.value)
                else:
                    raise RuntimeError("BRANCH moet een string zijn.")

            # --- INFO_STANDARD ---
            if target.id == "INFO_STANDARD":

                # INFO_STANDARD string
                if isinstance(n.value, ast.Constant):
                    info_std = [str(n.value.value)]

                # INFO_STANDARD list
                elif isinstance(n.value, ast.List):
                    values = []
                    for elt in n.value.elts:
                        if not (isinstance(elt, ast.Constant) and isinstance(elt.value, str)):
                            raise RuntimeError("INFO_STANDARD list mag alleen strings bevatten.")
                        values.append(elt.value)
                    info_std = values

                else:
                    raise RuntimeError("INFO_STANDARD moet een string of lijst van strings zijn.")
                
            # --- INPUT_DIR ---
            if target.id == "INPUT_DIR":
                if isinstance(n.value, ast.Constant):
                    input_dir = str(n.value.value)
                else:
                    raise RuntimeError("INPUT_DIR moet een string zijn.")

    if not branch:
        raise RuntimeError("BRANCH niet gevonden in test_regressie.py")
    if not info_std:
        raise RuntimeError("INFO_STANDARD niet gevonden in test_regressie.py")
    if not input_dir:
        raise RuntimeError("INPUT_DIR niet gevonden in test_regressie.py")

    return branch, info_std, input_dir


BRANCH, INFO_STANDARD, INPUT_DIR_STR = _read_test_defaults()



# =============================================================================
# COMMAND LINE OPTIES
# =============================================================================

def pytest_addoption(parser):
    """Voeg CLI-opties toe voor branch & information standards."""
    parser.addoption("--branch", action="store", default=BRANCH,
                     help="Specificeer de branch naam voor de tests")
    parser.addoption("--info-standard", action="append", default=None,
                     help="Een of meerdere information standards (herhaalbaar)")
    parser.addoption("--input_dir", action="store", default=INPUT_DIR_STR,
                     help="Specificeer de input dir voor de tests")


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def server_config(request):
    """Geeft testconfig door aan testcases."""
    cli_info = request.config.getoption("--info-standard")
    return {
        "branch": request.config.getoption("--branch"),
        "info_standard": cli_info or INFO_STANDARD
    }


# =============================================================================
# PARAMETRISATIE VAN TESTS
# =============================================================================

def _url_id(url: str) -> str:
    """Bouw een nette ID op basis van query parameters."""
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    keys = ["informationStandard", "goal", "category", "subcategory", "role", "variant"]
    parts = [q.get(k, [""])[0] for k in keys]
    return " | ".join(p for p in parts if p) or url


def pytest_generate_tests(metafunc):
    if "test_url" not in metafunc.fixturenames:
        return

    project_root = Path(__file__).resolve().parents[1]
    json_path = project_root / "utils" / "common" / "unieke_combinaties_all.json"

    # branch = metafunc.config.getoption("--branch")
    # info_std = metafunc.config.getoption("--info-standard") or INFO_STANDARD

    urls = generate_test_urls([str(json_path)])
    print(f"Totaal te runnen tests: {len(urls)}")

    metafunc.parametrize("test_url", urls, ids=[_url_id(u) for u in urls])


# =============================================================================
# PLAYWRIGHT FIXTURES
# =============================================================================

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
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    page = context.new_page()
    yield page
    page.close()
