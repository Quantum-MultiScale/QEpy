"""Tests for KSPP pseudopotential resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from qepy.io import QEInput

KSPPResolver = QEInput.KSPPResolver
apply_kspp = QEInput.apply_kspp

pytestmark = pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1].parent.parent / "KSPP").is_dir(),
    reason="KSPP checkout not available",
)


def test_kspp_resolver_gbrv_offline(kspp_offline_kwargs):
    resolver = KSPPResolver(**kspp_offline_kwargs())
    path = resolver.resolve("Al")
    assert path.name == "al_pbe_v1.uspp.F.UPF"
    assert path.is_file()


def test_qeinput_ksppresolver_init(al_atoms, kspp_offline_kwargs):
    qe_options = {"&system": {}}
    pwin = QEInput(
        qe_options=qe_options,
        atoms=al_atoms,
        ksppresolver=True,
        **kspp_offline_kwargs(),
    )
    assert pwin.kspp_enabled
    assert "atomic_species" in pwin.qe_options
    assert "al_pbe_v1.uspp.F.UPF" in pwin.qe_options["atomic_species"][0]


def test_qeinput_ksppresolver_configure(al_atoms, kspp_root, kspp_cache_dir):
    qe_options = {"&system": {}}
    pwin = QEInput(qe_options=qe_options, atoms=al_atoms, ksppresolver=True)
    pwin.ksppresolver(
        xc="LDA",
        search_paths=[kspp_root],
        offline=True,
        cache_dir=kspp_cache_dir,
        apply=True,
    )
    assert "al_lda_v1.uspp.F.UPF" in pwin.qe_options["atomic_species"][0]


def test_read_upf_cutoffs_nc(kspp_root):
    from qepy.io import _read_upf_cutoffs

    path = kspp_root / "norm-conserving/nc-sr-04/PBE/stringent/upf/Al.upf"
    cutoffs = _read_upf_cutoffs(path)
    assert cutoffs["ecutwfc"] == pytest.approx(37.5)
    assert cutoffs["ecutrho"] == pytest.approx(150.0)


def test_apply_kspp_warns_low_ecut(al_atoms, kspp_root, kspp_cache_dir):
    qe_options = {"&system": {"ecutwfc": 10}}
    with pytest.warns(UserWarning, match="ecutwfc=10"):
        apply_kspp(
            qe_options,
            al_atoms.get_chemical_symbols(),
            table="norm-conserving/nc-sr-04",
            accuracy="stringent",
            search_paths=[kspp_root],
            offline=True,
            cache_dir=kspp_cache_dir,
        )
    assert qe_options["&system"]["ecutwfc"] == 10


def test_apply_kspp_updates_ecuts(al_atoms, kspp_root, kspp_cache_dir):
    qe_options = {"&system": {"ecutwfc": 10}}
    with pytest.warns(UserWarning, match="ecutwfc=10"):
        apply_kspp(
            qe_options,
            al_atoms.get_chemical_symbols(),
            table="norm-conserving/nc-sr-04",
            accuracy="stringent",
            search_paths=[kspp_root],
            offline=True,
            cache_dir=kspp_cache_dir,
            update_ecuts=True,
        )
    assert qe_options["&system"]["ecutwfc"] == pytest.approx(37.5)
    assert qe_options["&system"]["ecutrho"] == pytest.approx(150.0)


def test_qepy_calculator_ksppresolver(al_atoms, kspp_offline_kwargs):
    from qepy.calculator import QEpyCalculator

    qe_options = {"&system": {}}
    calc = QEpyCalculator(
        atoms=al_atoms,
        qe_options=qe_options,
        ksppresolver=True,
        **kspp_offline_kwargs(),
    )
    assert calc.qeinput.kspp_enabled
    assert "atomic_species" in calc.qe_options
    assert "al_pbe_v1.uspp.F.UPF" in calc.qe_options["atomic_species"][0]


def test_qepy_calculator_ksppresolver_configure(al_atoms, kspp_offline_kwargs):
    from qepy.calculator import QEpyCalculator

    qe_options = {"&system": {}}
    calc = QEpyCalculator(
        atoms=al_atoms,
        qe_options=qe_options,
        ksppresolver=True,
        **kspp_offline_kwargs(),
    )
    calc.ksppresolver(xc="LDA", apply=True)
    assert "al_lda_v1.uspp.F.UPF" in calc.qe_options["atomic_species"][0]


def test_qepy_calculator_ksppresolver_update_ecuts_warns(
    al_atoms, kspp_root, kspp_cache_dir
):
    from qepy.calculator import QEpyCalculator

    qe_options = {"&system": {"ecutwfc": 10}}
    calc = QEpyCalculator(
        atoms=al_atoms,
        qe_options=qe_options,
        ksppresolver=True,
        search_paths=[kspp_root],
        offline=True,
        cache_dir=kspp_cache_dir,
    )
    with pytest.warns(UserWarning, match="ecutwfc=10"):
        calc.ksppresolver(
            table="norm-conserving/nc-sr-04",
            accuracy="stringent",
            update_ecuts=True,
            apply=True,
        )
    assert calc.qe_options["&system"]["ecutwfc"] == pytest.approx(37.5)
    assert calc.qe_options["&system"]["ecutrho"] == pytest.approx(150.0)


def test_apply_kspp_fills_qe_options(kspp_offline_kwargs):
    class _Atoms:
        def get_chemical_symbols(self):
            return ["Al", "Al", "Al", "Al"]

    qe_options = {"&system": {}}
    apply_kspp(
        qe_options,
        _Atoms().get_chemical_symbols(),
        **kspp_offline_kwargs(),
    )
    assert "atomic_species" in qe_options
    assert len(qe_options["atomic_species"]) == 1
    assert "al_pbe_v1.uspp.F.UPF" in qe_options["atomic_species"][0]
    assert "pseudo_dir" in qe_options["&control"]


def test_resolve_with_partial_cache(monkeypatch, tmp_path):
    resolver = KSPPResolver(offline=False, cache_dir=tmp_path / "cache")
    resolver.pseudo_dir.mkdir(parents=True, exist_ok=True)
    (resolver.pseudo_dir / "al_pbe_v1.uspp.F.UPF").write_text("dummy")

    monkeypatch.setattr(
        resolver,
        "_list_files",
        lambda: frozenset({"na_pbe_v1.5.uspp.F.UPF"}),
    )

    def _fake_download(filename, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("dummy")

    monkeypatch.setattr(resolver, "_download", _fake_download)
    path = resolver.resolve("Na")
    assert path.name == "na_pbe_v1.5.uspp.F.UPF"
