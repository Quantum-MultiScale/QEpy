import qepy
import qepy_pw
try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    comm = comm.py2f()
except Exception:
    comm = None

oldxml = False # oldxml version QE

inputobj = qepy_pw.qepy_common.input_base()
#-----------------------------------------------------------------------
inputobj.prefix = 'tmp'
# inputobj.tmp_dir = './tmp.wfx/'
#-----------------------------------------------------------------------
if comm : inputobj.my_world_comm = comm
qepy_pw.qepy_initial(inputobj)

if oldxml :
    qepy_pw.oldxml_read_file()
else :
    qepy_pw.read_file()

embed = qepy_pw.qepy_common.embed_base()
energy = qepy_pw.qepy_calc_energies()
qepy_pw.qepy_stop_run(0, what = 'no')
# Newer version QE (>6.3) (XML file name is 'data-file-schema.xml')
# Olderversion QE (XML file name is 'data-file.xml')
