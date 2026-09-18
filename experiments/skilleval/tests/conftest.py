import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def _no_real_codex_sessions(monkeypatch, tmp_path):
    monkeypatch.setenv("SKILLEVAL_CODEX_SESSIONS", str(tmp_path / "codex-sessions"))
