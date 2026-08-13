"""Phonon dispersion post-processing helpers for QEpy.

The actual quantities (q-path, dynamical-matrix run, dispersion) come
through :class:`qepy.driver.Driver` -- see `Driver.get_phonon_qpath`,
`Driver.run_q2r`, `Driver.run_matdyn`, `Driver.get_phonon_dispersion`. This
module only holds the plumbing those methods share:

- :func:`_run_subprocess` -- ``q2r.x`` and ``matdyn.x`` are still thin
  f90wrap bindings around QE's original standalone-executable main routines
  (``qepy.qepy_phonon_ph.q2r`` / ``.matdyn``, see ``qepy.qebins.QEBINS``):
  ``matdyn`` ends with a Fortran ``STOP`` and both call ``mp_global_end()``
  (which finalizes MPI) -- either would take down a live Python/Jupyter
  process (unlike ``task='phonon'``, which has been given that treatment).
  Both are therefore run in a short-lived subprocess instead.
- :func:`plot_phonon_dispersion` -- a small plotting convenience for the
  quantities `Driver.get_phonon_dispersion`/`Driver.get_phonon_qpath`
  return; entirely optional, plotting them yourself with matplotlib works
  just as well.
"""
import subprocess
import sys


def _run_subprocess(prog, inputfile, python=None, nproc=1, mpirun='mpirun'):
    """Run a QE program that isn't safe to call in-process as a subprocess."""
    python = python or sys.executable
    code = f"from qepy.cui.qex import run; run({prog!r}, inputfile={inputfile!r})"
    cmd = [python, '-c', code]
    if nproc > 1 :
        cmd = [mpirun, '-np', str(nproc)] + cmd
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 :
        raise RuntimeError(
            f"{prog} failed (exit {result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result.stdout


def plot_phonon_dispersion(x, freq, special_x=None, labels=None, ax=None,
        units='cm-1', color='C0', **kwargs):
    """Plot a phonon dispersion from `qepy.driver.Driver.get_phonon_dispersion`.

    Parameters
    ----------
    x : np.ndarray, shape (npoints,)
        Cumulative path length.
    freq : np.ndarray, shape (npoints, nmodes)
        Phonon frequencies at each point of `x`.
    special_x : np.ndarray, optional
        Path length of each high-symmetry anchor, for vertical guide lines.
    labels : list of str, optional
        Label of each anchor in `special_x`.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on; a new figure/axes is created if not given.
    units : str
        Label for the y-axis; should match the units `freq` is actually in
        (``matdyn.x`` always writes cm-1).
    color : str
        Line color for the bands, forwarded to ``ax.plot``.
    kwargs : dict
        Extra keyword arguments forwarded to ``ax.plot``.

    Returns
    -------
    ax : matplotlib.axes.Axes
    """
    import matplotlib.pyplot as plt
    if ax is None :
        _, ax = plt.subplots()
    for band in freq.T :
        ax.plot(x, band, color=color, **kwargs)
    ax.axhline(0, ls=':', color='gray', lw=1)
    if special_x is not None :
        for xs in special_x :
            ax.axvline(xs, color='gray', lw=0.5)
        if labels is not None :
            ax.set_xticks(special_x)
            ax.set_xticklabels(labels)
    ax.set_xlim(x[0], x[-1])
    ax.set_ylabel(f'Frequency ({units})')
    return ax
