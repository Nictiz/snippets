from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONFIG = {
    "base_url": "https://my.interoplab.eu",
    "headless": True,
    "browser_name": "chromium",
    "storage_state_path": str(PROJECT_ROOT / "utils" / "auth" / "state.json"),
    "tracing_enabled": True,
    "trace_output_path": str(PROJECT_ROOT / "test-results" / "trace.zip"),
}