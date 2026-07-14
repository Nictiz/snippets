# tests/bulk/conftest.py

import os
import subprocess
import sys
import tomllib
import urllib.parse
from pathlib import Path
import pytest
from tests.helpers import generate_test_urls
from utils.common.logger import setup_logger
from filelock import FileLock

CONFIG_FILE = "bulk-testsets.toml"
LOCAL_CONFIG_FILE = "bulk.local.toml"
DEFAULT_BRANCH = "main"
DEFAULT_INPUT_DIR = "Nictiz-testscripts/output"
DEFAULT_PROFILE = "ggz"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _config_dir() -> Path:
    return _project_root() / "config"

def _generated_json_path() -> Path:
    return (
        _project_root()
        / "utils"
        / "common"
        / "unique_combinations_all.json"
    )

def _resolve_input_dir(input_dir: str) -> Path:
    path = Path(os.path.expandvars(input_dir)).expanduser()

    if path.is_absolute():
        if path.exists():
            return path.resolve()
        raise pytest.UsageError(
            f"Could not find input_dir '{input_dir}'. Checked:\n- {path}\n\n"
            "Pass --input_dir or configure config/bulk.local.toml."
        )

    project_root = _project_root()
    candidates = [project_root / path]
    candidates.extend(parent / path for parent in project_root.parents)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    checked = "\n".join(f"- {candidate}" for candidate in candidates)
    raise pytest.UsageError(
        f"Could not find input_dir '{input_dir}'. Checked:\n{checked}\n\n"
        "Pass --input_dir or configure config/bulk.local.toml."
    )


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise pytest.UsageError(f"Could not parse bulk config file {path}: {e}") from e


def _merge_profiles(base: dict, local: dict) -> dict:
    defaults = dict(base.get("defaults", {}))
    defaults.update(local.get("defaults", {}))

    profiles = dict(base.get("profiles", {}))
    profiles.update(local.get("profiles", {}))

    return {"defaults": defaults, "profiles": profiles}


def _load_bulk_config() -> dict:
    config_dir = _config_dir()
    return _merge_profiles(
        _load_toml(config_dir / CONFIG_FILE),
        _load_toml(config_dir / LOCAL_CONFIG_FILE),
    )


def _as_string_list(value, name: str) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise pytest.UsageError(f"{name} must be a string or a list of strings.")


def _available_profiles(bulk_config: dict) -> str:
    names = sorted(bulk_config.get("profiles", {}))
    return ", ".join(names) if names else "none"


def _resolve_bulk_options(config) -> dict:
    bulk_config = _load_bulk_config()
    defaults = bulk_config.get("defaults", {})
    profiles = bulk_config.get("profiles", {})

    cli_info_standards = config.getoption("--info-standard")
    profile_name = (
        config.getoption("--bulk-profile")
        or defaults.get("profile")
        or DEFAULT_PROFILE
    )
    profile = profiles.get(profile_name, {})

    if profile_name and profile_name not in profiles and not cli_info_standards:
        raise pytest.UsageError(
            f"Unknown bulk profile '{profile_name}'. Available profiles: {_available_profiles(bulk_config)}."
        )

    branch = (
        config.getoption("--branch")
        or profile.get("branch")
        or defaults.get("branch")
        or DEFAULT_BRANCH
    )
    input_dir = (
        config.getoption("--input_dir")
        or profile.get("input_dir")
        or defaults.get("input_dir")
        or DEFAULT_INPUT_DIR
    )

    if cli_info_standards:
        info_standards = cli_info_standards
    else:
        raw_info_standards = profile.get("info_standards") or defaults.get(
            "info_standards"
        )
        if raw_info_standards is None:
            raise pytest.UsageError(
                f"Bulk profile '{profile_name}' has no info_standards. "
                "Add them to the profile or pass --info-standard."
            )
        info_standards = _as_string_list(
            raw_info_standards,
            f"profiles.{profile_name}.info_standards",
        )

    return {
        "branch": branch,
        "info_standards": info_standards,
        "input_dir": input_dir,
        "profile": profile_name,
    }


def _bulk_options(config) -> dict:
    options = getattr(config, "_bulk_options", None)
    if options is None:
        options = _resolve_bulk_options(config)
        config._bulk_options = options
    return options


_BULK_TESTSETS_EXTRACTED = False


def _extract_bulk_testsets(config):
    """Rebuild the bulk input once per pytest run."""
    global _BULK_TESTSETS_EXTRACTED

    # Voorkomt herhaling binnen dezelfde worker.
    if _BULK_TESTSETS_EXTRACTED:
        return

    logger = setup_logger()
    project_root = _project_root()
    extract_script = (
        project_root
        / "utils"
        / "common"
        / "extract_testset.py"
    )
    json_path = _generated_json_path()

    bulk_options = _bulk_options(config)
    inputdir = _resolve_input_dir(bulk_options["input_dir"])

    cmd = [
        sys.executable,
        str(extract_script),
        "--root",
        str(inputdir),
        "--branch",
        str(bulk_options["branch"]),
        "--folders",
        *bulk_options["info_standards"],
    ]

    coordination_dir = project_root / "test-results"
    coordination_dir.mkdir(parents=True, exist_ok=True)

    lock_path = coordination_dir / "bulk-extraction.lock"
    marker_path = coordination_dir / "bulk-extraction.uid"

    # xdist geeft alle workers binnen één run dezelfde unieke ID.
    run_uid = os.getenv("PYTEST_XDIST_TESTRUNUID")

    with FileLock(str(lock_path)):
        marker_uid = (
            marker_path.read_text(encoding="utf-8")
            if marker_path.exists()
            else None
        )

        already_extracted = (
            run_uid is not None
            and marker_uid == run_uid
            and json_path.exists()
        )

        if not already_extracted:
            print(f"Run extract_testset.py: {extract_script}")
            print(
                f"Bulk profile: {bulk_options['profile']} "
                f"({len(bulk_options['info_standards'])} "
                "information standards)"
            )

            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as error:
                logger.error(
                    f"extract_testset.py failed: {error}"
                )
                pytest.exit(
                    "Test set extraction failed; "
                    "test run aborted.",
                    returncode=1,
                )

            if not json_path.exists():
                pytest.exit(
                    "Test set extraction completed without "
                    f"creating {json_path}.",
                    returncode=1,
                )

            # Alleen schrijven nadat extractie volledig geslaagd is.
            if run_uid is not None:
                marker_path.write_text(
                    run_uid,
                    encoding="utf-8",
                )

            print("extract_testset.py completed successfully")

    _BULK_TESTSETS_EXTRACTED = True


def _url_id(url: str) -> str:
    """Build a readable ID from query parameters."""
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    keys = ["informationStandard", "goal", "category", "subcategory", "role", "variant"]
    parts = [q.get(k, [""])[0] for k in keys]
    return " | ".join(p for p in parts if p) or url


def pytest_generate_tests(metafunc):
    if "test_url" not in metafunc.fixturenames:
        return

    json_path = _generated_json_path()
    _extract_bulk_testsets(metafunc.config)

    urls = generate_test_urls([str(json_path)])
    print(f"Total tests to run: {len(urls)}")

    metafunc.parametrize(
        "test_url", 
        urls, 
        ids=[_url_id(u) for u in urls],
        )
