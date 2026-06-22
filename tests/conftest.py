import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def _geen_demo_auth(monkeypatch):
    """Tests draaien zonder HTTP Basic Auth tenzij expliciet gezet in de test."""
    monkeypatch.delenv("DEMO_WACHTWOORD", raising=False)
