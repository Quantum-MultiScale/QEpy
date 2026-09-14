import qepy
import qepy_pw
try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    comm = comm.py2f()
except Exception:
    comm = None

oldxml = False # oldxml version QE

fname = 'qe_in.in'
qepy_pw.qepy_pwscf(fname, comm)

embed = qepy_pw.qepy_common.embed_base()

qepy_pw.qepy_mod.qepy_restart_from_xml()
if qepy_pw.starting_scf.get_starting_pot().strip() != 'file' :
    qepy_pw.starting_scf.set_starting_pot('file')
    qepy_pw.potinit()
if qepy_pw.starting_scf.get_starting_wfc().strip() != 'file' :
    qepy_pw.starting_scf.set_starting_wfc('file')
    qepy_pw.wfcinit()

energy = qepy_pw.qepy_calc_energies()
qepy_pw.qepy_stop_run(0, what = 'no')
