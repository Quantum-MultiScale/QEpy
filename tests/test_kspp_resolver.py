"""Tests for KSPP pseudopotential resolution."""

from pathlib import Path

import pytest

from qepy.io import QEInput

KSPPResolver = QEInput.KSPPResolver
apply_kspp = QEInput.apply_kspp

KSPP_ROOT = (Path(__file__).resolve().parents[1].parent.parent / "KSPP").resolve()


@pytest.mark.skipif(not KSPP_ROOT.is_dir(), reason="KSPP checkout not available")
def test_kspp_resolver_gbrv_offline():
    resolver = KSPPResolver(
        search_paths=[KSPP_ROOT],
        cache_dir=Path("/tmp/qepy_kspp_test_cache"),
        offline=True,
    )
    path = resolver.resolve("Al")
    assert path.name == "al_pbe_v1.uspp.F.UPF"
    assert path.is_file()


@pytest.mark.skipif(not KSPP_ROOT.is_dir(), reason="KSPP checkout not available")
def test_qeinput_ksppresolver_init():
    class _Atoms:
        def get_chemical_symbols(self):
            return ["Al"]

    qe_options = {"&system": {}}
    pwin = QEInput(
        qe_options=qe_options,
        atoms=_Atoms(),
        ksppresolver=True,
        search_paths=[KSPP_ROOT],
        offline=True,
    )
    assert pwin.kspp_enabled
    assert "atomic_species" in pwin.qe_options
    assert "al_pbe_v1.uspp.F.UPF" in pwin.qe_options["atomic_species"][0]


@pytest.mark.skipif(not KSPP_ROOT.is_dir(), reason="KSPP checkout not available")
def test_qeinput_ksppresolver_configure():
    class _Atoms:
        def get_chemical_symbols(self):
            return ["Al"]

    qe_options = {"&system": {}}
    pwin = QEInput(qe_options=qe_options, atoms=_Atoms(), ksppresolver=True)
    pwin.ksppresolver(
        xc="LDA",
        search_paths=[KSPP_ROOT],
        offline=True,
        apply=True,
    )
    assert "al_lda_v1.uspp.F.UPF" in pwin.qe_options["atomic_species"][0]


@pytest.mark.skipif(not KSPP_ROOT.is_dir(), reason="KSPP checkout not available")
def test_read_upf_cutoffs_nc():
    from qepy.io import _read_upf_cutoffs

    path = KSPP_ROOT / "norm-conserving/nc-sr-04/PBE/stringent/upf/Al.upf"
    cutoffs = _read_upf_cutoffs(path)
    assert cutoffs["ecutwfc"] == pytest.approx(37.5)
    assert cutoffs["ecutrho"] == pytest.approx(150.0)


@pytest.mark.skipif(not KSPP_ROOT.is_dir(), reason="KSPP checkout not available")
def test_apply_kspp_warns_low_ecut():
    class _Atoms:
        def get_chemical_symbols(self):
            return ["Al"]

    qe_options = {"&system": {"ecutwfc": 10}}
    with pytest.warns(UserWarning, match="ecutwfc=10"):
        apply_kspp(
            qe_options,
            _Atoms().get_chemical_symbols(),
            table="norm-conserving/nc-sr-04",
            accuracy="stringent",
            search_paths=[KSPP_ROOT],
            offline=True,
        )
    assert qe_options["&system"]["ecutwfc"] == 10


@pytest.mark.skipif(not KSPP_ROOT.is_dir(), reason="KSPP checkout not available")
def test_apply_kspp_updates_ecuts():
    class _Atoms:
        def get_chemical_symbols(self):
            return ["Al"]

    qe_options = {"&system": {"ecutwfc": 10}}
    apply_kspp(
        qe_options,
        _Atoms().get_chemical_symbols(),
        table="norm-conserving/nc-sr-04",
        accuracy="stringent",
        search_paths=[KSPP_ROOT],
        offline=True,
        update_ecuts=True,
    )
    assert qe_options["&system"]["ecutwfc"] == pytest.approx(37.5)
    assert qe_options["&system"]["ecutrho"] == pytest.approx(150.0)


@pytest.mark.skipif(not KSPP_ROOT.is_dir(), reason="KSPP checkout not available")
def test_apply_kspp_fills_qe_options():
    class _Atoms:
        def get_chemical_symbols(self):
            return ["Al", "Al", "Al", "Al"]

    qe_options = {"&system": {}}
    apply_kspp(
        qe_options,
        _Atoms().get_chemical_symbols(),
        search_paths=[KSPP_ROOT],
        offline=True,
    )
    assert "atomic_species" in qe_options
    assert len(qe_options["atomic_species"]) == 1
    assert "al_pbe_v1.uspp.F.UPF" in qe_options["atomic_species"][0]
    assert "pseudo_dir" in qe_options["&control"]
