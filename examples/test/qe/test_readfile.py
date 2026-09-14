import numpy as np
import qepy
from qepy.core import qepy_clean_saved
from qepy import qepy_pw
from qepy import qepy_modules
import unittest
import pathlib
import shutil

try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    commf = comm.py2f()
except Exception:
    comm = None
    commf = None

path = pathlib.Path(__file__).resolve().parent / 'DATA'
inputfile = path / 'qe_in.in'


class Test(unittest.TestCase):
    def test_0_scf(self):
        qepy_pw.qepy_pwscf(inputfile, commf)
        qepy_pw.electrons()

        conv_flag = bool(qepy_modules.control_flags.get_conv_elec())
        self.assertTrue(conv_flag)

        etotal = qepy_pw.ener.get_etot()
        self.assertTrue(np.isclose(etotal, -552.93477389, atol = 1E-6))

        qepy_pw.qepy_stop_run(0, what = 'all')
        qepy_clean_saved()

    def test_1_read(self):
        inputobj = qepy_pw.qepy_common.input_base()
        inputobj.prefix = 'tmp'
        if commf : inputobj.my_world_comm = commf

        qepy_pw.qepy_initial(inputobj)

        qepy_pw.read_file()

        embed = qepy_pw.qepy_common.embed_base()
        qepy_pw.qepy_common.set_embed(embed)
        qepy_pw.qepy_calc_energies()
        self.assertTrue(np.isclose(embed.etotal, -552.93477389, atol = 1E-6))
        qepy_pw.qepy_stop_run(0, what = 'no')
        qepy_clean_saved()

    def test_2_read_pw(self):
        qepy_pw.qepy_pwscf(inputfile, commf)
        embed = qepy_pw.qepy_common.embed_base()
        qepy_pw.qepy_common.set_embed(embed)

        qepy_pw.qepy_mod.qepy_restart_from_xml()
        if qepy_pw.starting_scf.get_starting_pot().strip() != 'file' :
            qepy_pw.starting_scf.set_starting_pot('file')
            qepy_pw.potinit()
        if qepy_pw.starting_scf.get_starting_wfc().strip() != 'file' :
            qepy_pw.starting_scf.set_starting_wfc('file')
            qepy_pw.wfcinit()

        qepy_pw.qepy_calc_energies()
        self.assertTrue(np.isclose(embed.etotal, -552.93477389, atol = 1E-6))
        # qepy_pw.qepy_stop_run(0, what = 'no')
        # qepy_clean_saved()

    @classmethod
    def tearDownClass(cls):
        if comm and comm.rank == 0 :
            path = pathlib.Path('.')
            for f in path.glob('al.*'):
                if f.is_file():
                    f.unlink()
                else :
                    shutil.rmtree(f)


if __name__ == "__main__":
    unittest.main()
