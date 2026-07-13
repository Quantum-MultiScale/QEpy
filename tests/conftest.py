"""Shared pytest fixtures for QEpy tests."""

from __future__ import annotations

from pathlib import Path

import pytest

KSPP_ROOT = (Path(__file__).resolve().parents[1].parent.parent / "KSPP").resolve()


@pytest.fixture(scope="session")
def kspp_root() -> Path:
    if not KSPP_ROOT.is_dir():
        pytest.skip("KSPP checkout not available")
    return KSPP_ROOT


@pytest.fixture
def kspp_cache_dir(tmp_path: Path) -> Path:
    """Worker- and test-unique cache directory for parallel pytest runs."""
    cache = tmp_path / "kspp_cache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


@pytest.fixture
def al_atoms():
    class _Atoms:
        def __init__(self):
            self.calc = None

        def get_chemical_symbols(self):
            return ["Al"]

        def wrap(self):
            pass

    return _Atoms()


@pytest.fixture
def kspp_offline_kwargs(kspp_root: Path, kspp_cache_dir: Path):
    def _make(**overrides):
        kwargs = {
            "search_paths": [kspp_root],
            "offline": True,
            "cache_dir": kspp_cache_dir,
        }
        kwargs.update(overrides)
        return kwargs

    return _make
