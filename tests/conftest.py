"""Shared fixtures. Puts scripts/ on the import path so the tools can be tested."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def raw_curriculum(root: Path) -> dict:
    """The real curriculum.json, loaded once. Do not mutate; use `doc` instead."""
    return json.loads((root / "roadmap" / "curriculum.json").read_text(encoding="utf-8"))


@pytest.fixture
def doc(raw_curriculum: dict) -> dict:
    """A deep copy of the curriculum, safe to mutate in a test."""
    return copy.deepcopy(raw_curriculum)
