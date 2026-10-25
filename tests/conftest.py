"""Make the two research scripts importable during tests."""

from __future__ import annotations

import sys
from pathlib import Path

CODE_DIRECTORY = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIRECTORY))
