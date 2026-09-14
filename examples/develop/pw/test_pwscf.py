import numpy as np
import qepy
import qepy_pw
import qepy_modules

try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    commf = comm.py2f()
except Exception:
    comm = None
    commf = None

fname = 'qe_in.in'

qepy_pw.qepy_pwscf(fname, commf)

embed = qepy_pw.qepy_common.embed_base()

qepy_pw.qepy_electrons_scf(2, 0)

nscf = qepy_modules.control_flags.get_n_scf_steps()
conv_flag = bool(qepy_modules.control_flags.get_conv_elec())
info = 'Converged {} at {} steps'.format(conv_flag, nscf)
qepy_pw.qepy_mod.qepy_write_stdout(info)

# get density
nr = qepy_pw.qepy_mod.qepy_get_grid()
nspin = qepy_pw.lsda_mod.get_nspin()
rho = np.empty((np.prod(nr), nspin), order = 'F')
qepy_pw.qepy_mod.qepy_get_rho(rho)
ncharge = rho.sum()*qepy_modules.cell_base.get_omega()/np.prod(nr)
if comm is None or comm.rank == 0 : print('ncharge', ncharge, flush = True)

# qepy_pw.qepy_calc_energies(embed)
etotal = embed.etotal

qepy_pw.qepy_forces()
forces = qepy_pw.force_mod.get_array_force().T

stress = np.ones((3, 3), order='F')
qepy_pw.qepy_stress(stress)

qepy_pw.punch('all')
qepy_pw.qepy_stop_run(0, what = 'no')
