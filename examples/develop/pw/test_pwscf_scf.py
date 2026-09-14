import numpy as np
import qepy
import qepy_pw
import qepy_modules

try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    comm = comm.py2f()
except Exception:
    comm = None

fname = 'qe_in.in'

qepy_pw.qepy_pwscf(fname, comm)

embed = qepy_pw.qepy_common.embed_base()
qepy_pw.qepy_common.set_embed(embed)
# embed.ldescf = True # add scf correction energy
embed.extene = 0.0
#
embed.iterative = True

for i in range(60):
    embed.mix_coef = -1.0
    qepy_pw.qepy_electrons_scf(2, 0)
    embed.mix_coef = 0.7
    qepy_pw.qepy_electrons_scf(2, 0)
    if qepy_modules.control_flags.get_conv_elec() : break

# qepy_pw.qepy_calc_energies(embed)
etotal = embed.etotal

#
nat = qepy_modules.ions_base.get_nat()
#
qepy_pw.qepy_forces()
forces = qepy_pw.force_mod.get_array_force().T

#
stress = np.ones((3, 3), order='F')
qepy_pw.qepy_stress(stress)

qepy_pw.punch('all')
qepy_pw.qepy_stop_run(0, what = 'no')
