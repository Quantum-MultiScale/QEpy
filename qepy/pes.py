"""
XC-mixing helpers for PES scans.

Provides ``eval_xc_mix``, ``scf_xc_mix``, and ``make_label`` for mixed
functionals via DFTpy.  The 1-D scan is :meth:`qepy.driver.Driver.compute_pes`,
which takes ``update_geometry``, ``qe_options``, and ``xc_list``.

Usage
-----
    from qepy.driver import Driver

    def update_geometry(qe_options, d):
        opts = dict(qe_options)
        # ... set geometry for scan coordinate d ...
        return opts

    grid, energies = Driver.compute_pes(
        d_grid,
        update_geometry,
        qe_options,
        xc_list,
        scan_label="d (A)",
    )
"""

from dftpy.functional import XC
from .driver import Driver


def make_label(xc_mix):
    """Build a human-readable label from an XC-mix dictionary.

    Examples
    --------
    >>> make_label({"PBE": 1.0})
    'PBE'
    >>> make_label({"PBE": 0.75, "RVV10": 0.25})
    '0.75*PBE + 0.25*RVV10'
    """
    parts = []
    for name, c in xc_mix.items():
        if c == 0.0:
            continue
        parts.append(name if c == 1.0 else f"{c:.2g}*{name}")
    return " + ".join(parts) if parts else "XC"


def eval_xc_mix(driver, xc_mix):
    """Evaluate a mixed XC functional on the current QEpy density.

    Parameters
    ----------
    driver : qepy.driver.Driver
        Active QEpy driver (iterative mode).
    xc_mix : dict
        Mapping of functional name to coefficient,
        e.g. ``{"PBE": 0.75, "RVV10": 0.25}``.

    Returns
    -------
    v_total : ndarray
        Mixed XC potential on the real-space grid (Ry).
    E_total : float
        Mixed XC energy (Ry).
    """
    rho = driver.get_density()
    field = driver.data2field(rho)

    v_total = 0.0
    E_total = 0.0

    for name, coeff in xc_mix.items():
        if coeff == 0.0:
            continue
        xc = XC(name)
        func = xc(field)

        v_total = v_total + coeff * driver.field2data(func.potential) * 2
        E_total = E_total + coeff * func.energy * 2

    return v_total, E_total


def scf_xc_mix(qe_options, xc_mix, maxiter=80, logfile="tmp.out"):
    """Run a single SCF with a mixed XC functional.

    Parameters
    ----------
    qe_options : dict
        Quantum ESPRESSO input options (same format as ``Driver``).
    xc_mix : dict
        XC mix dictionary (see ``eval_xc_mix``).
    maxiter : int
        Maximum SCF iterations.
    logfile : str
        Path for the QE log file.

    Returns
    -------
    energy : float
        Total energy in Ry (QEpy internal units).
    """
    driver = Driver(qe_options=qe_options, iterative=True, logfile=logfile)

    for _ in range(maxiter):
        extpot, ex = eval_xc_mix(driver, xc_mix)
        driver.set_external_potential(potential=extpot, extene=ex, exttype="xc")
        driver.diagonalize()
        driver.mix()
        if driver.check_convergence():
            break

    energy = driver.get_energy()
    driver.stop()
    return energy
