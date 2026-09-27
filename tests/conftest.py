"""Pytest configuration for path setup."""

import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parents[1].resolve()
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


# Make tests reproducible by ignoring machine-specific profile/tool env config.
# Without this, importing config during test collection can pick up a developer's
# local .env and fail before tests run.
os.environ["REACHY_MINI_SKIP_DOTENV"] = "1"
os.environ.pop("REACHY_MINI_CUSTOM_PROFILE", None)
os.environ.pop("REACHY_MINI_EXTERNAL_PROFILES_DIRECTORY", None)
os.environ.pop("REACHY_MINI_EXTERNAL_TOOLS_DIRECTORY", None)


@pytest.fixture(autouse=True)
def reusable_conversation_tests(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    """Exercise inherited generic profile tests in their original unlocked configuration."""
    if request.node.path.name in {"test_intake_flow.py", "test_korean_input.py"}:
        return
    from reachy_korean_intake import config as config_module

    for name, module in list(sys.modules.items()):
        if name.startswith("reachy_korean_intake") and hasattr(module, "LOCKED_PROFILE"):
            monkeypatch.setattr(module, "LOCKED_PROFILE", None)
    monkeypatch.setattr(config_module.Config, "REACHY_MINI_CUSTOM_PROFILE", None)
    monkeypatch.setattr(config_module.config, "REACHY_MINI_CUSTOM_PROFILE", None)
