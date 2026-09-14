#!/usr/bin/env python
# coding: utf-8

import numpy as np
import qepy
import qepy_pw
import qepy_modules
import qepy_xclib

try:
    from mpi4py import MPI
    comm=MPI.COMM_WORLD.py2f()
except Exception :
    comm=None

qepy_pw.qepy_pwscf('vcrelax.in',comm)
embed = qepy_pw.qepy_common.embed_base()

nstep = qepy_modules.control_flags.get_nstep()
#-------------------------------------------------------------------------------
lforce = qepy_modules.control_flags.get_lforce()
tstress = qepy_modules.control_flags.get_tstress()
sigma = qepy_pw.force_mod.get_array_sigma()
lmovecell = qepy_pw.cellmd.get_lmovecell()

fix_volume = qepy_modules.cell_base.get_fix_volume()
fix_area = qepy_modules.cell_base.get_fix_area()
treinit_gvecs = qepy_modules.control_flags.get_treinit_gvecs()

ions_status = np.ones(1, dtype = 'int32')*3
#-------------------------------------------------------------------------------
for idone in range(0, nstep):
    if idone>0 : qepy_modules.control_flags.set_ethr(1E-6)
    qepy_pw.electrons()

    conv_ions = True

    if lforce : qepy_pw.forces()
    if tstress: qepy_pw.stress(sigma)

    lmd = qepy_modules.control_flags.get_lmd()
    lbfgs = qepy_modules.control_flags.get_lbfgs()

    if lmd or lbfgs :
        if fix_volume: qepy_pw.impose_deviatoric_stress(sigma)
        if fix_area: qepy_pw.impose_deviatoric_stress_2d(sigma)

        qepy_pw.extrapolation.update_file()

        qepy_pw.move_ions(idone, ions_status)

        conv_ions = (ions_status == 0) or (ions_status == 1 and treinit_gvecs)

        if idone < nstep and not conv_ions :
            qepy_pw.punch('config-nowf')

        if qepy_xclib.dft_setting_routines.xclib_dft_is('hybrid'):
            qepy_xclib.dft_setting_routines.stop_exx()

    if conv_ions: break

    if lmd or lbfgs :
        if ions_status == 1 :
            qepy_modules.control_flags.set_lbfgs(False)
            qepy_modules.control_flags.set_lmd(False)
            print('Final scf calculation at the relaxed structure', flush=True)
            qepy_pw.reset_gvectors()
        elif ions_status == 2 :
            qepy_pw.reset_magn()
        else :
            if treinit_gvecs :
                if lmovecell : qepy_pw.scale_h()
                qepy_pw.reset_gvectors()
            else :
                qepy_pw.extrapolation.update_pot()
                qepy_pw.hinit1()

qepy_pw.qepy_stop_run(0, what = 'no')
