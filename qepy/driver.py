import csv
import numpy as np
import tempfile
from functools import wraps
import qepy
import qepy.qepy_modules # import the QE MPI first
from qepy.core import env, qepy_clean_saved, QEpyLibs
from qepy.io import QEInput

def gathered(function):
    @wraps(function)
    def wrapper(self, **kwargs):
        out = kwargs.get('out', None)
        gather = kwargs.get('gather', True)
        if out is None : out = self.create_array(gather=gather, kind='rho')
        if gather and self.nproc > 1 :
            arr = self.create_array(gather=False, kind='rho')
        else :
            arr = out
        #
        kwargs['out'] = arr
        results = function(self, **kwargs)
        #
        if gather and self.nproc > 1 :
            self.qepy_pw.qepy_mod.qepy_get_value(arr, out, gather = True)
            if isinstance(results, (tuple, list)):
                results = out, *results[1:]
            else :
                results = out
        return results
    return wrapper

class Driver(metaclass=QEpyLibs):
    """
    The driver of QEpy.

    Parameters
    ----------
    inputfile : str
        Name of QE input file
    comm : object
        Parallel communicator
    ldescf : bool
        If True, also print the SCF correction term for each SCF cycle
    iterative : bool
        Run SCF or real-time TDDFT one iteration at a time
    task : str
        Task to be performed by the driver :

          - 'scf' : Self consistent field
          - 'nscf' : initialization of Driver from previous SCF calculation
          - 'optical' : Optical absorption spectrum (real-time TDDFT with ce-tddft of Davide Ceresoli)
          - 'tddfpt_davidson' : TDDFPT with davidson algorithm

    embed : object (Fortran)
        embed object itialized in the Fortran side of QEpy needed to communicate with QE.
    prefix : str
        prefix of QE input/output
    outdir : str
        The output directory of QE
    logfile : str, file or bool
        The screen output of QE. If it is a file descriptor, it should open with 'w+'.

          - None : Show on the screen.
          - str  : Save to the given file.
          - True : Save to the temporary file, see also :func:`qepy.driver.Driver.get_output`.

    outdir : str
        The output directory of QE
    qe_options : dict
        A dictionary with input parameters for QE to generate QE input file.
        See class QEInput
    prog : str
        The name of QE program, default is `pw` which is pw.x in QE.
    progress : bool
        If True, will continue run the QE without cleaning the workspace. Most times used for running TDDFT after scf.
    atoms : object
        An ase Atoms to generate the input file.
    needwf : bool
        If False, will not read wavefunctions and skip wavefunction-related initialization.
    kwargs : dict
        Other options

    .. note::

         - The bool `gather` parameter in functions means the data is gathered on root or distributed on all cpus.
         - Units in QEpy are Bohr and Rydberg. These differ from ASE's units. Please, be careful!

             + positions : Bohr
             + lattice : Bohr
             + energy : Ry
             + forces : Ry/Bohr
             + stress : Ry/Bohr**3
             + potential : Ry
             + density : 1.0/Bohr**3

    """
    POTNAMES = {'external' : 0, 'localpp' : 1, 'hartree' : 2, 'xc' : 4}
    FORCENAMES = {'ewald' : 1, 'localpp' : 2, 'nlcc' : 4}
    STRESSNAMES = {'ewald' : 1, 'localpp' : 2, 'hartree' : 4, 'xc': 8}

    def __init__(self, inputfile = None, comm = None, ldescf = True, iterative = False,
             task = 'scf', embed = None, prefix = None, outdir = None, logfile = None,
             qe_options = None, prog = 'pw', progress = False, atoms = None, needwf = True,
             **kwargs):
        self.task = task
        self.embed = embed
        self.comm = comm
        self.inputfile = inputfile
        self.iterative = iterative
        self.prefix = prefix
        self.outdir = outdir
        self.logfile = logfile
        self.qe_options = qe_options
        self.prog = prog
        self.progress = progress
        self.atoms = atoms
        self.needwf = needwf
        #
        if embed is None:
            self.embed.ldescf = ldescf
            self.embed.iterative = iterative
            self.embed.tddft.iterative = iterative
        #
        self.comm = comm
        self.qepy = qepy
        self.qeinput = QEInput()
        #
        self.driver_initialize()

    def __getattr__(self, attr):
        return getattr(type(self), attr)
        # return _getattr_qepylibs(self, attr)

    def _init_log(self):
        """_initialize the QE output."""
        self.fileobj_interact = False
        if self.logfile in [None, False]:
            self.fileobj = None
        else :
            # self.qepy_pw.qepy_mod.qepy_set_stdout(self.logfile)
            if self.logfile is True:
                self.fileobj_interact = True
                self.fileobj = tempfile.NamedTemporaryFile('w+')
            elif hasattr(self.logfile, 'write'):
                self.fileobj = self.logfile
            else :
                self.fileobj = open(self.logfile, 'w+')
        env['STDOUT'] = self.fileobj
        return self.fileobj

    @property
    def embed(self):
        if self._embed is None :
            self._embed = self.qepy_pw.qepy_common.embed_base()
        return self._embed

    @embed.setter
    def embed(self, value):
        self._embed = value

    @property
    def comm(self):
        return self._comm

    @comm.setter
    def comm(self, value):
        """Sets the MPI communicator with value given by mpi4py"""
        if value is True:
            try:
                from mpi4py import MPI
                value = MPI.COMM_WORLD
            except Exception:
                value = None
        self._comm = value
        if hasattr(self.comm, 'py2f') :
            self._commf = self.comm.py2f()
        else :
            self._commf = self.comm

    @property
    def commf(self):
        return self._commf

    @property
    def is_root(self):
        """Whether it is the root.

        If the comm is set, root is rank == 0.
        If comm not set, root is ionode of QE.
        """
        if hasattr(self.comm, 'rank'):
            return self.comm.rank == 0
        else :
            return self.qepy_modules.io_global.get_ionode()

    @property
    def nproc(self):
        if hasattr(self.comm, 'size'):
            return self.comm.size
        else :
            return self.qepy_modules.mp_world.get_nproc()

    @property
    def qe_is_mpi(self):
        return bool(self.qepy_pw.qepy_common.get_is_mpi())

    @property
    def qe_is_openmp(self):
        return bool(self.qepy_pw.qepy_common.get_is_openmp())

    def restart(self, prog=None, **kwargs):
        """Restart the driver losing all information about the previous driver"""
        prog = prog or self.prog
        self.driver_initialize()

    def driver_initialize(self, **kwargs):
        """ Initialize the driver

        Parameters
        ----------
        inputfile : str
            Name of QE input file
        commf : object
            mpi4py parallel communicator to be sent to Fortran
        task : str
            Task to be performed by the driver :

             - 'scf' : Self consistent field
             - 'nscf' : initialization of Driver from previous SCF calculation
             - 'optical' : Optical absorption spectrum (real-time TDDFT with ce-tddft of Davide Ceresoli)

        qe_options: dict
            A dictionary with input parameters for QE to generate QE input file.

        """
        # stop the last driver and save new driver
        if not self.progress :
            if hasattr(env['DRIVER'], 'stop'): env['DRIVER'].stop()
            env['DRIVER'] = self
        #
        self._init_log()
        self.qepy_pw.qepy_common.set_embed(self.embed)
        #
        inputfile=self.inputfile
        commf=self.commf
        task=self.task
        qe_options = self.qe_options
        prog = self.prog
        #
        if qe_options :
            inputfile, basefile = 'input_tmp.in', inputfile
            self.qeinput.write_qe_input(inputfile, atoms = self.atoms, basefile=basefile, qe_options=qe_options, prog=prog)
        #
        if task == 'optical' :
            self.tddft_initialize(inputfile=inputfile, commf = commf, **kwargs)
        elif task.startswith('tddfpt_'):
            self.tddfpt_initialize(inputfile=inputfile, commf = commf, **kwargs)
        elif task == 'nscf' :
            inputobj = self.qepy_pw.qepy_common.input_base()
            if self.prefix : inputobj.prefix = self.prefix
            if self.outdir : inputobj.tmp_dir = str(self.outdir) + '/'
            if commf : inputobj.my_world_comm = commf
            self.qepy_pw.qepy_initial(inputobj)
            # tmpdir = inputobj.tmp_dir.decode().strip() + inputobj.prefix.decode().strip() + '.save' + '/'
            if self.needwf :
                self.qepy_pw.read_file()
            else :
                self.qepy_pw.read_file_new(False)
            if self.needwf :
                self.qepy_pw.qepy_mod.qepy_open_files()
        else :
            self.qepy_pw.qepy_pwscf(inputfile, commf)
            if self.embed.iterative :
                self.qepy_modules.control_flags.set_niter(1)
        #
        self.density = np.zeros((1, 1))
        self.iter = 0

    def tddft_initialize(self, inputfile = None, commf = None, **kwargs):
        """ Initialize the tddft

        Parameters
        ----------
        inputfile : str
            Name of QE input file, which also contains `&inputtddft` section.
        commf : object
            mpi4py parallel communicator to be sent to Fortran
        """
        if inputfile is None : inputfile = self.inputfile
        if commf is None : commf = self.commf
        #
        if self.progress :
            self.qepy_pw.wvfct.get_array_g2kin()
            self.qepy_cetddft.qepy_tddft_readin(inputfile)
        else :
            self.qepy_cetddft.qepy_tddft_main_initial(inputfile, commf)
            self.qepy_pw.read_file()
        self.qepy_cetddft.qepy_tddft_main_setup()

    def tddfpt_initialize(self, inputfile = None, commf = None, **kwargs):
        """ Initialize the tddft

        Parameters
        ----------
        inputfile : str
            Name of QE input file, which also contains `&inputtddft` section.
        commf : object
            mpi4py parallel communicator to be sent to Fortran
        """
        if inputfile is None : inputfile = self.inputfile
        if commf is None : commf = self.commf
        #
        if self.progress :
            raise AttributeError("Not support 'progress' now")
            # self.qepy_pw.wvfct.get_array_g2kin()
            # self.qepy_cetddft.qepy_tddft_readin(inputfile)
        else :
            if self.task != 'tddfpt_davidson' :
                raise ValueError("Only support 'davidson' algorithm now.")
            # Fix the io problem if the job directly started after a PW calculation
            self.qepy_modules.control_flags.set_io_level(1)
            #
            self.qepy_tddfpt.qepy_lr_dav_main_initial(inputfile)

    def diagonalize(self, print_level = 2, nscf = False, **kwargs):
        """Diagonalize the Hamiltonian

        Parameters
        ----------
        print_level :
            The level of output of QE
        """
        self.embed.lmovecell = False
        self.iter += 1
        if self.task == 'optical' :
            self.qepy_cetddft.qepy_molecule_optical_absorption()
        elif self.task == 'tddfpt_davidson' :
            if self.qepy_tddfpt.lr_dav_variables.get_if_check_orth():
                self.qepy_tddfpt.lr_dav_debug.check_orth()
            self.qepy_tddfpt.lr_dav_routines.one_dav_step()
            self.qepy_tddfpt.lr_dav_routines.dav_calc_residue()
            self.qepy_tddfpt.lr_dav_routines.dav_expan_basis()
        elif nscf :
            self.embed.task = 'nscf'
            self.qepy_pw.qepy_electrons_scf(print_level, 0)
        else :
            self.embed.mix_coef = -1.0
            self.qepy_pw.qepy_electrons_scf(print_level, 0)

    def propagate(self, **kwargs):
        return self.diagonalize(**kwargs)

    def mix(self, mix_coef = 0.7, print_level = 2):
        """Mix the density with the QE density mixing

        Parameters
        ----------
        print_level :
            The level of output of QE
        """
        if self.task == 'optical' : return
        self.embed.mix_coef = mix_coef
        self.qepy_pw.qepy_electrons_scf(print_level, 0)

    def check_convergence(self, **kwargs):
        """Check the convergence of the SCF"""
        if self.task == 'scf' :
            converged = bool(self.qepy_modules.control_flags.get_conv_elec())
            if converged and not self.embed.initial : self.end_scf()
        elif self.task == 'tddfpt_davidson' :
            converged = bool(self.qepy_tddfpt.lr_dav_variables.get_dav_conv())
        else:
            converged = False
        return converged

    def get_scf_error(self, **kwargs):
        """Return the error of the SCF compared to previous cycle"""
        if self.embed.iterative :
            return self.embed.dnorm
        else :
            return self.qepy_modules.control_flags.get_scf_error()

    def get_scf_steps(self, **kwargs):
        """Return the number of SCF steps"""
        if self.embed.iterative :
            return self.iter
        else :
            return self.qepy_modules.control_flags.get_n_scf_steps()

    def scf(self, print_level = 2, maxiter = None, original = False, nscf = False, **kwargs):
        """Run the scf/tddft until converged or reached the maximum number of iterations"""
        if maxiter is not None and not self.embed.iterative :
            self.qepy_modules.control_flags.set_niter(maxiter)
        if self.task == 'optical' :
            self.qepy_cetddft.qepy_molecule_optical_absorption()
        elif self.task=='tddfpt_davidson' :
            self.tddfpt_davidson_scf()
        elif nscf :
            self.embed.task = 'nscf'
            self.qepy_pw.qepy_electrons_scf(print_level, 0)
        elif not self.embed.iterative and self.embed.exttype < 2 :
            # Use electrons to support hybrid xc functional
            return self.electrons(original=original)
        else :
            self.qepy_pw.qepy_electrons_scf(print_level, 0)
        return self.embed.etotal

    def optical_absorption(self, **kwargs):
        return self.scf(**kwargs)

    def tddfpt_davidson_scf(self, **kwargs):
        max_iter = self.qepy_tddfpt.lr_dav_variables.get_max_iter()
        self.scf_conv_type = 'maxiter'
        for dav_iter in range(max_iter):
            # if self.qepy_tddfpt.lr_dav_variables.get_if_check_orth():
                # self.qepy_tddfpt.lr_dav_debug.check_orth()
            # self.qepy_tddfpt.lr_dav_routines.one_dav_step()
            # self.qepy_tddfpt.lr_dav_routines.dav_calc_residue()
            # self.qepy_tddfpt.lr_dav_routines.dav_expan_basis()
            self.diagonalize(**kwargs)
            if self.qepy_tddfpt.lr_dav_variables.get_dav_conv():
                self.scf_conv_type = 'conv'
                break
            if self.qepy_modules.check_stop.check_stop_now():
                self.qepy_tddfpt.lr_dav_routines.lr_write_restart_dav()
                self.scf_conv_type = 'maxtime'
                break
        self.tddfpt_davidson_interpret(**kwargs)

    def tddfpt_davidson_interpret(self, **kwargs):
        self.qepy_tddfpt.lr_dav_routines.interpret_eign('END')
        lplot_drho = self.qepy_tddfpt.lr_dav_variables.get_lplot_drho()
        if lplot_drho:
            self.qepy_tddfpt.lr_dav_routines.plot_drho()

    def non_scf(self, **kwargs):
        """Single "non-selfconsistent" calculation"""
        # fix some saved variables from last scf calculations
        self.qepy_modules.control_flags.set_lscf(0)
        self.qepy_modules.control_flags.set_lbfgs(0)
        self.qepy_modules.control_flags.set_lmd(0)
        self.qepy_modules.control_flags.set_lwf(0)
        #
        self.qepy_pw.non_scf()
        return self.qepy_pw.ener.get_etot()

    def electrons(self, original = False, **kwargs):
        """Execute original QE routine "electrons" """
        if original :
            self.qepy_pw.electrons()
        else :
            self.qepy_pw.qepy_electrons()
        return self.qepy_pw.ener.get_etot()

    def end_scf(self, nscf = False, **kwargs):
        """Ends the SCF and cleans the SCF workspace. Only run when in iterative mode (i.e., one cycle at a time)"""
        if self.embed.iterative :
            if self.task == 'optical' :
                self.embed.tddft.finish = True
                self.qepy_cetddft.qepy_molecule_optical_absorption()
            else :
                self.embed.finish = True
                self.qepy_pw.qepy_electrons_scf(0, 0)

    def stop(self, exit_status = 0, what = 'all', print_flag = 0, **kwargs):
        """Stop the driver. This must be done anytime a new driver is created.
        This method is invoked automatically if a running driver is detected. Only
        one driver can run at any given time.

        Parameters
        ----------
        exit_status : int
            0 : QE will remove it temporary files
        print_flag : int
            0 : Not print time informations
        what : str
             see :func:`qepy.driver.Driver.save`.
        """
        if self.task == 'optical' :
            self.tddft_stop(exit_status, print_flag = print_flag, what = what, **kwargs)
        elif self.task == 'tddfpt_davidson' :
            self.tddfpt_davidson_stop(exit_status, print_flag = print_flag, what = what, **kwargs)
        else :
            if not self.embed.initial : self.end_scf()
            self.qepy_pw.qepy_stop_run(exit_status, print_flag = print_flag, what = what, finalize = False)

        if hasattr(self.fileobj, 'close'): self.fileobj.close()
        qepy_clean_saved()
        # qepy_clean_saved(self.qepy_modules)
        # qepy_clean_saved(self.qepy_pw)
        # if self.task == 'optical' :
            # qepy_clean_saved(self.qepy_cetddft)
        #
        env['DRIVER'] = None
        env['STDOUT'] = None

    def tddft_restart(self, istep=None, **kwargs):
        """Restarts the TDDFT from previous interrupted run.

        Parameters
        ----------
        istep : int
            Start number of steps, just for output.
        """
        self.qepy_cetddft.qepy_tddft_mod.qepy_cetddft_wfc2rho()
        if istep is not None :
            self.embed.tddft.istep = istep

    def tddft_stop(self, exit_status = 0, what = 'no', print_flag = 0, **kwargs):
        """Stops TDDFT run"""
        if not self.embed.tddft.initial : self.end_scf()
        #! Do not save the PW files, otherwise the initial wfcs will be overwritten.
        self.qepy_pw.qepy_stop_run(exit_status, print_flag = print_flag, what = 'no', finalize = False)
        self.qepy_cetddft.qepy_stop_tddft(exit_status)

    def tddfpt_davidson_stop(self, exit_status = 0, what = 'no', print_flag = 0, **kwargs):
        """Stops TDDFPT run"""
        self.qepy_tddfpt.qepy_lr_dav_main_finalise()

    def save(self, what = 'all', **kwargs):
        """
        Save the QE data to the disk in original QE files that can be accessed via post-processing
        or read with a QEpy driver

        Parameters
        ----------
        what : str

          * what = 'all' : write xml data file, charge density, wavefunctions
                           (for final data);
          * what = 'config' : write xml data file and charge density; also,
                              for nks=1, wavefunctions in plain binary format
                              (see why in comments below). For intermediate
                              or incomplete results;
          * what = 'config-nowf' : write xml data file and charge density only;
                           (save density);
          * what = 'config-init' : write xml data file only excluding final results
                                   (for dry run, can be called at early stages).

          see PW/src/punch.f90
        """
        self.qepy_pw.punch(what)
        # self.qepy_pw.close_files(False)

    def update_run_options(self, qe_options = {}, **kwargs):
        pass

    def get_energy(self, **kwargs):
        """Return the total energy.
        Nota bene: Only use for regular QE runs (i.e., not when doing embedding)."""
        if abs(self.qepy_pw.ener.get_etot()) > 1E-16 :
            energy = self.qepy_pw.ener.get_etot()
        elif abs(self.embed.etotal) > 1E-16 :
            energy = self.embed.etotal
        else :
            energy = self.calc_energy(**kwargs)
        return energy

    def calc_energy(self, **kwargs):
        """Calculate the energy with PW2CASINO of QE.
        Use this only if you have a good reason to use it! For example
        embedding calculations."""
        self.qepy_pw.qepy_calc_energies()
        return self.embed.etotal

    def update_ions(self, positions = None, lattice = None, update = 0, **kwargs):
        """update the ions of QE. This is used for dynamic runs.

        Parameters
        ----------
        positions : np.ndarray (n, 3)
            positions of ions
        lattice : 3x3 matrix
            lattice of ions
        update : int
             - 0 : update everything (default)
             - 1 : only update atomic information, not update potential

        """
        positions = positions.T
        if lattice is not None :
            lattice = lattice.T
            if not self.qepy_pw.cellmd.get_lmovecell():
                raise ValueError(" Lattice update only works for variable-cell simulations.\n Please restart the QEpy with calculation= 'vc-relax' or 'vc-md'")
            self.qepy_pw.qepy_mod.qepy_update_ions(positions, update, lattice)
        else :
            self.qepy_pw.qepy_mod.qepy_update_ions(positions, update)

    def pwscf_restart(self, starting_pot='file', starting_wfc='file'):
        """Read PW ouput/restart files.

        Parameters
        ----------
        """
        self.qepy_pw.qepy_mod.qepy_restart_from_xml()
        if self.qepy_pw.basis.get_starting_pot().strip() != starting_pot :
            self.qepy_pw.basis.set_starting_pot(starting_pot)
            self.qepy_pw.potinit()
        if self.qepy_pw.basis.get_starting_wfc().strip() != starting_wfc :
            self.qepy_pw.basis.set_starting_wfc(starting_wfc)
            self.qepy_pw.wfcinit()

    def create_array(self, gather = True, kind = 'rho', out = None):
        """Returns an empty array in real space.
        Nota bene: this is for real-space arrays like the density (rho) and potentials."""
        if out is not None: return out
        if kind == 'rho' :
            nspin = self.qepy_pw.lsda_mod.get_nspin()
            if gather and self.nproc > 1 :
                nr = self.get_number_of_grid_points(gather = gather)
                if self.embed.dfftp.mype == 0:
                    out = np.zeros((np.prod(nr), nspin), order = 'F')
                else :
                    out = np.zeros((1, nspin), order = 'F')
            else :
                nnr = self.embed.dfftp.nnr
                out = np.zeros((nnr, nspin), order = 'F')
        else :
            raise ValueError('Only support "rho"')
        return out

    def get_density(self, gather = True, out = None):
        """Returns valence pseudodensity array in real space."""
        if out is None : out = self.create_array(gather=gather, kind='rho')
        self.qepy_pw.qepy_mod.qepy_get_rho(out, gather = gather)
        return out

    def get_core_density(self, gather = True, out = None):
        """Returns core density array in real space."""
        if out is None : out = self.create_array(gather=gather, kind='rho')
        self.qepy_pw.qepy_mod.qepy_get_rho_core(out, gather = gather)
        return out

    def get_kinetic_energy_density(self, gather = True, out = None):
        """Returns KS kinetic energy density array in real space."""
        if out is None : out = self.create_array(gather=gather, kind='rho')
        self.qepy_pw.qepy_mod.qepy_get_tau(out, gather = gather)
        return out

    def get_wave_function(self, band=None, kpt=0):
        """Returns wave-function array in real space."""
        self.qepy_pw.qepy_mod.qepy_get_evc(kpt + 1)
        nrs = np.zeros(3, dtype = 'int32')
        self.qepy_pw.qepy_mod.qepy_get_grid_smooth(nrs)
        if self.is_root :
            wf = np.empty(np.prod(nrs), order = 'F', dtype = np.complex128)
        else :
            wf = np.empty(1, order = 'F', dtype = np.complex128)
        if band is None :
            band = np.arange(self.get_number_of_bands())
        else :
            band = np.asarray(band)
            if band.ndim == 0 : band = [band]
        wfs = []
        for ibnd in band :
            self.qepy_pw.qepy_mod.qepy_get_wf(kpt + 1, ibnd + 1, wf)
            wfs.append(wf.copy())
        return wfs

    def get_dipole_tddft(self):
        """Return the total dipole computed by a TDDFT run.
        Nota bene: only available during TDDFT runs."""
        # dipole = self.qepy_cetddft.qepy_tddft_common.get_array_dipole().copy()
        dipole = self.embed.tddft.dipole
        return dipole

    def set_density(self, density, gather = True, **kwargs):
        """Set density array in real space."""
        #
        density = self.create_array(gather=gather, kind='rho', out=density)
        if density.ndim != 2 : raise ValueError("The array should be 2-d.")
        #
        if gather and self.nproc > 1 :
            self.qepy_pw.qepy_mod._mp_bcast_group_real_2(density)
        self.qepy_pw.qepy_mod.qepy_set_rho(density, gather = gather)


    def set_external_potential(self, potential, exttype = None, gather = True, extene  = None, **kwargs):
        """Set an external potential in addition to the ones already included in the QEpy run
        according to the logic enumerated below.

        Parameters
        ----------
        potential : (nnr, nspin)
            The external potential
        exttype : list or int
            The type of external potential. It can be a list of name or a integer.
            e.g.  `exttype = ('localpp', 'xc')` or `exttype = 5`. `external` stands for an
            additional external potential.

                 ==== ============================== ===
                 type potential                      bin
                 ==== ============================== ===
                  0   external                       000
                  1   localpp                        001
                  2   hartree                        010
                  4   xc                             100
                 ==== ============================== ===

        """
        if exttype is not None :
            if not isinstance(exttype, int): exttype = self.potname2type(exttype)
            self.embed.exttype = exttype
        if extene is not None :
            self.embed.extene = extene
        else :
            self.embed.extene = 0.0
        #
        potential = self.create_array(gather=gather, kind='rho', out=potential)
        if potential.ndim != 2 : raise ValueError("The array should be 2-d.")
        #
        if gather and self.nproc > 1 :
            self.qepy_pw.qepy_mod._mp_bcast_group_real_2(potential)
        self.qepy_pw.qepy_mod.qepy_set_extpot(potential, gather = gather)

    def get_output(self):
        """Return the output of QE.

        It depends on the `logfile` of the initialization of the driver :

          - None : return None.
          - str  : return all outputs.
          - True : It will return the output from last time.
        """
        if self.fileobj is not None :
            if self.fileobj_interact :
                self.fileobj.flush()
                self.fileobj.seek(0)
                lines = self.fileobj.readlines()
                self.fileobj.close()
                #
                self._init_log()
                #
                return lines
            else :
                self.fileobj.seek(0)
                return self.fileobj.readlines()
        else :
            return None

    @gathered
    def get_elf(self, gather = True, out = None, **kwargs):
        """Return electron localization function."""
        self.qepy_pp.do_elf(out)
        return out

    @gathered
    def get_rdg(self, gather = True, out = None, **kwargs):
        """Return reduced density gradient."""
        self.qepy_pp.do_rdg(out)
        return out
#-----------------------------------------------------------------------

    @gathered
    def get_local_pp(self, gather = True, out = None, **kwargs):
        """Return local component of the pseudopotential."""
        for i in range(out.shape[1]):
            out[:, i] = self.qepy_pw.scf.get_array_vltot()
        return out

    @gathered
    def get_hartree(self, gather = True, out = None, add=False, **kwargs):
        """Return information about Hartree energy:
            tuple (potential, energy, total charge)
        """
        if not add : out[:] = 0.0
        ehart, charge = self.qepy_pw.v_h(self.embed.rho.of_g[:,0], out)
        return out, ehart, charge

    @gathered
    def get_exchange_correlation(self, gather = True, out = None, tau=None, **kwargs):
        """Return information about the exchange-correlation:
        LDA, GGA: tuple (potential, energy, v*rho)
        MGGA:     tuple (potential, energy, v*rho, tau)

        TODO :
            The interface will changed in the new version of QE!

        Note :
            For metaGGA, only return scattered tau
        """
        etxc = vtxc = 0.0
        rho_obj = self.embed.rho
        rho_core = self.qepy_pw.scf.get_array_rho_core()
        rhog_core = self.qepy_pw.scf.get_array_rhog_core()
        is_meta = self.qepy_xclib.dft_setting_routines.xclib_dft_is('meta')
        if is_meta:
            if tau is None : tau = out*0.0
            self.qepy_pw.v_xc_meta(rho_obj, rho_core, rhog_core, etxc, vtxc, out, tau)
            return out, etxc, vtxc, tau
        else :
            etxc, vtxc = self.qepy_pw.v_xc(rho_obj, rho_core, rhog_core, out)
            return out, etxc, vtxc

    @gathered
    def get_density_functional(self, gather = True, out = None, add = False, **kwargs):
        """Return effective potential information.

        Note :
            Then final potential is saved in the v_obj
        """
        rho_obj = self.embed.rho
        rho_core = self.qepy_pw.scf.get_array_rho_core()
        rhog_core = self.qepy_pw.scf.get_array_rhog_core()
        v_obj = self.embed.v
        etotefield = 0.0
        #
        v_obj.of_r[:] = 0.0
        ehart, etxc, vtxc, eth, charge = self.qepy_pw.qepy_v_of_rho(rho_obj, rho_core, rhog_core, etotefield, v_obj)
        info = [ehart, etxc, vtxc, eth, etotefield, charge]
        if add :
            out += v_obj.of_r
        else :
            out[:] = v_obj.of_r
        return out, info

    def get_hartree_potential(self, gather = True, out = None, **kwargs):
        return self.get_hartree(gather=gather, out=out, **kwargs)[0]

    def get_exchange_correlation_potential(self, gather = True, out = None, **kwargs):
        return self.get_exchange_correlation(gather=gather, out=out, **kwargs)[0]

    def get_density_functional_potential(self, gather = True, out = None, **kwargs):
        return self.get_density_functional(gather=gather, out=out, **kwargs)[0]

    def get_effective_potential(self, gather = True, out = None, **kwargs):
        out = self.get_local_pp(gather=gather, out=out, **kwargs)
        out = self.get_density_functional_potential(gather=gather, out=out, add = True, **kwargs)
        return out
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------
    #ASE Calculator
    def get_potential_energy(self, **kwargs):
        """Return the potential energy."""
        return self.get_energy()

    def get_forces(self, icalc = 0, ignore = (), **kwargs):
        """Return the total forces. (n, 3)

        Parameters
        ----------
        icalc : int

            ===== ============================= ===
            icalc without                       bin
            ===== ============================= ===
              0   all                           000
              1   no ewald                      001
              2   no localpp                    010
              4   no nlcc                       100
            ===== ============================= ===
        ignore : list
            ignore some forces, which does same job as `icalc`.

              - ewald (1)
              - localpp (2)
              - nlcc (4)
        """
        if len(ignore) > 0 : icalc = self.forcename2type(ignore)
        self.qepy_pw.qepy_forces(icalc)
        forces = self.qepy_pw.force_mod.get_array_force().T
        return forces

    def get_stress(self, icalc = 0, ignore = (), **kwargs):
        """Return the total stress. (3, 3)

        Parameters
        ----------
        icalc : int

            ===== ============================= ====
            icalc without                       bin
            ===== ============================= ====
              1   no ewald                      0001
              2   no localpp                    0010
              4   no hartree                    0100
              8   no xc                         1000
            ===== ============================= ====
        ignore : list
            ignore some stress, which does same job as `icalc`.

              - ewald (1)
              - localpp (2)
              - hartree (4)
              - xc (8)
        """
        stress = np.zeros((3, 3), order='F')
        if len(ignore) > 0 : icalc = self.stressname2type(ignore)
        self.qepy_pw.qepy_stress(stress, icalc=icalc)
        return stress

    #ASE DFTCalculator
    @classmethod
    def get_number_of_bands(cls):
        """Return the number of bands."""
        return cls.qepy_pw.wvfct.get_nbnd()

    @classmethod
    def get_xc_functional(cls):
        """Return the XC-functional identifier.

        'LDA', 'PBE', ..."""
        return cls.qepy_modules.funct.get_dft_short().decode("utf-8")

    @classmethod
    def get_bz_k_points(cls):
        """Return all the k-points in the 1. Brillouin zone.

        The coordinates are relative to reciprocal latice vectors."""
        return cls.qepy_pw.klist.get_array_xk()

    @classmethod
    def get_number_of_spins(cls):
        """Return the number of spins in the calculation.

        Spin-paired calculations: 1, spin-polarized calculation: 2."""
        return cls.qepy_pw.lsda_mod.get_nspin()

    @classmethod
    def get_spin_polarized(cls):
        """Is it a spin-polarized calculation?"""
        return bool(cls.qepy_pw.lsda_mod.get_lsda())

    @classmethod
    def get_ibz_k_points(cls):
        """Return k-points in the irreducible part of the Brillouin zone.

        The coordinates are relative to reciprocal latice vectors."""
        xk = cls.qepy_pw.klist.get_array_xk()[:, :cls.get_number_of_k_points()].T
        return xk @ cls.qepy_modules.cell_base.get_array_at()

    @classmethod
    def get_k_point_weights(cls):
        """Weights of the k-points.

        The sum of all weights is one."""
        return cls.qepy_pw.klist.get_array_wk()[:cls.get_number_of_k_points()]

    def get_pseudo_density(self, spin=None, pad=True, gather = True):
        """Return pseudo-density array.

        If *spin* is not given, then the total density is returned.
        Otherwise, the spin up or down density is returned (spin=0 or
        1)."""
        density = self.get_density(gather = gather)
        if spin is None :
            return density.sum(axis=1)
        else :
            return density[:, spin]

    @classmethod
    def get_pseudo_wave_function(cls, band=None, kpt=0, spin=0, broadcast=True,
                                 pad=True):
        """Return pseudo-wave-function array."""
        cls.qepy_pw.qepy_mod.qepy_get_evc(kpt + 1)
        evc = cls.qepy_modules.wavefunctions.get_array_evc()
        if band is None :
            return evc
        else :
            return evc[:, band]

    @classmethod
    def get_eigenvalues(cls, kpt=0, spin=0):
        """Return eigenvalue array."""
        return cls.qepy_pw.wvfct.get_array_et().T[kpt]

    @classmethod
    def get_occupation_numbers(cls, kpt=0, spin=0):
        """Return occupation number array."""
        return cls.qepy_pw.wvfct.get_array_wg().T[kpt]

    @classmethod
    def get_fermi_level(cls):
        """Return the Fermi level."""
        return cls.qepy_pw.ener.get_ef()

    # def initial_wannier(self, initialwannier, kpointgrid, fixedstates,
                        # edf, spin, nbands):
        # """Initial guess for the shape of wannier functions.

        # Use initial guess for wannier orbitals to determine rotation
        # matrices U and C.
        # """
        # raise NotImplementedError

    # def get_wannier_localization_matrix(self, nbands, dirG, kpoint,
                                        # nextkpoint, G_I, spin):
        # """Calculate integrals for maximally localized Wannier functions."""
        # raise NotImplementedError

    @classmethod
    def get_magnetic_moment(cls, **kwargs):
        """Return the total magnetic moment."""
        return cls.qepy_pw.lsda_mod.get_magtot()

    @classmethod
    def get_number_of_grid_points(cls, gather = True):
        """Return the shape of arrays."""
        nr = np.zeros(3, dtype = 'int32')
        cls.qepy_pw.qepy_mod.qepy_get_grid(nr, gather)
        return nr
    #ASE DFTCalculator END
#-----------------------------------------------------------------------

    @classmethod
    def get_number_of_k_points(cls):
        """Return the number of kpoints."""
        return cls.qepy_pw.klist.get_nkstot()

    @classmethod
    def get_volume(cls):
        """Return the volume."""
        return cls.qepy_modules.cell_base.get_omega()

    @classmethod
    def get_ecutrho(cls):
        """Return the cutoff for density."""
        return cls.qepy_modules.gvect.get_ecutrho()

    @classmethod
    def get_ions_lattice(cls):
        """Return the matrix of the lattice vectors in Bohrs."""
        alat = cls.qepy_modules.cell_base.get_alat()
        lattice = cls.qepy_modules.cell_base.get_array_at() * alat
        return lattice.T

    @classmethod
    def get_ions_positions(cls):
        """Return the cartesian positions of ions in Bohrs."""
        alat = cls.qepy_modules.cell_base.get_alat()
        pos = cls.qepy_modules.ions_base.get_array_tau().T * alat
        return pos

    @classmethod
    def get_ions_symbols(cls):
        """Return the symbols of ions."""
        ityp = cls.qepy_modules.ions_base.get_array_ityp() - 1
        nat = cls.qepy_modules.ions_base.get_nat()
        label = cls.qepy_modules.ions_base.get_array_atm().T.view('S3')[:,0].astype('U3')
        label = [x.strip() for x in label]
        symbols = []
        for i in range(nat):
            symbols.append(label[ityp[i]])
        return symbols

    @classmethod
    def data2field(cls, data, cell = None, grid = None, rank = None, cplx=False):
        """QE data to DFTpy DirectField.
        If data is None or small temporary array will return np.zeros(1).
        """
        from dftpy.field import DirectField
        from dftpy.grid import DirectGrid
        #
        if data is None or data.size < 8 : return np.zeros(1)
        #
        if cell is None : cell = cls.get_ions_lattice()
        if grid is None : grid = DirectGrid(lattice=cell, nr=cls.get_number_of_grid_points(), ecut=cls.get_ecutrho(), cplx=cplx)
        if not rank :
            rank = data.shape[1] if data.ndim == 2 else 1
        #
        if data.size != grid.nnrR*rank :
            raise ValueError('The size of data not match the grid,\
                    please check the data or set another grid', data.size, grid.nnrR*rank)
        #
        field = DirectField(grid=grid, data=data.ravel(order='C'), order='F', rank=rank, cplx=cplx)
        return field

    @classmethod
    def field2data(cls, field, data = None):
        """DFTpy DirectField to QE data.
        If the input field is not 3d array, will return np.zeros((1, 1)).
        """
        #
        if field is None or field.ndim < 3 : return np.zeros((1, 1))
        #
        ns = field.shape[0] if field.ndim == 4 else 1
        if data is None :
            nnrR = np.prod(cls.get_number_of_grid_points())
            data = np.empty((nnrR, ns))
        #
        if data.size != field.size :
            raise ValueError('The size of field is different with data,\
                    please check the field or set another data', field.size, data.size)
        #
        if ns == 1 : field = [field]
        for i in range(ns):
            data[:, i] = field[i].ravel(order = 'F')
        return data

    @classmethod
    def get_dftpy_grid(cls, nr = None, cell = None, mp = None, **kwargs):
        """Return the DFTpy DirectGrid from QE."""
        from dftpy.grid import DirectGrid
        if cell is None : cell = cls.get_ions_lattice()
        if nr is None :
            nr = cls.get_number_of_grid_points()
            ecut = cls.get_ecutrho()
        else :
            ecut = None
        grid = DirectGrid(lattice=cell, nr=nr, ecut=ecut, mp=mp, **kwargs)
        return grid

    @classmethod
    def get_ase_atoms(cls):
        """Return the atom.Atoms from QE to ASE (using ASE units)."""
        from ase.atoms import Atoms
        units_Bohr = cls.qepy_modules.constants.BOHR_RADIUS_SI * 1E10
        #
        symbols = cls.get_ions_symbols()
        positions = cls.get_ions_positions() * units_Bohr
        lattice = cls.get_ions_lattice() * units_Bohr
        atoms = Atoms(symbols = symbols, positions = positions, cell = lattice)
        return atoms

    @classmethod
    def get_dftpy_ions(cls):
        """Return the DFTpy.Ions from QE. (with DFTpy units)"""
        from dftpy.ions import Ions
        atoms = cls.get_ase_atoms()
        return Ions.from_ase(atoms)

    @classmethod
    def switch_nlpp(cls, nhm=0, nbetam=0, nkb=0, nh=None, **kwargs):
        """Switch on/off the nonlocal part of the pseudopotential"""
        nhm_ = cls.qepy_upflib.uspp_param.get_nhm()
        nbetam_ = cls.qepy_upflib.uspp_param.get_nbetam()
        nh_ = cls.qepy_upflib.uspp_param.get_array_nh().copy()
        nkb_ = cls.qepy_upflib.uspp.get_nkb()

        if nh is None: nh = nh_ * 0

        cls.qepy_upflib.uspp_param.set_nhm(nhm)
        cls.qepy_upflib.uspp_param.set_nbetam(nbetam)
        cls.qepy_upflib.uspp.set_nkb(nkb)
        cls.qepy_upflib.uspp_param.set_array_nh(nh)

        pp_options = {
            'nhm' : nhm_,
            'nbetam' : nbetam_,
            'nh': nh_,
            'nkb': nkb_,
        }

        return pp_options

    @classmethod
    def update_exchange_correlation(cls, xc=None, libxc=None, **kwargs):
        """Switch XC on the fly"""
        if libxc : xc = None
        cls.qepy_pw.qepy_mod.qepy_set_dft(xc)

    @classmethod
    def sum_band(cls, occupations = None, **kwargs):
        """Same as sum_band of QE with input occupations:

        Parameters
        ----------
        occupations: np.ndarray (nbnd, nk)
            occupation numbers
        """
        cls.qepy_pw.qepy_mod.qepy_sum_band(occupations)

    @staticmethod
    def name2type(dictionary, name):
        if isinstance(name, int):
            value = []
            for k, v in dictionary.items():
                if name & v == v : value.append(k)
        else :
            if isinstance(name, str): name = [name]
            value = 0
            for key in name :
                i = dictionary.get(key, None)
                if i is None :
                    raise AttributeError(f"The key '{key}' not in the given dictionary.")
                value += i
            return value
        return value

    @classmethod
    def potname2type(cls, name):
        return cls.name2type(cls.POTNAMES, name)

    @classmethod
    def forcename2type(cls, name = None):
        return cls.name2type(cls.FORCENAMES, name)

    @classmethod
    def stressname2type(cls, name = None):
        return cls.name2type(cls.STRESSNAMES, name)

    @staticmethod
    def compute_pes(scan_values, compute_energy, scan_label="x", save_csv=None):
        """Compute a potential-energy surface along an arbitrary coordinate.

        This is a general-purpose scanner that evaluates an energy function
        at each point along a 1-D coordinate grid.  The physics (SCF method,
        XC functional, geometry update, etc.) are entirely defined by the
        *compute_energy* callback.

        Parameters
        ----------
        scan_values : array_like
            1-D array of scan-parameter values (e.g. distances in Angstrom).
        compute_energy : callable
            Called as ``compute_energy(value)`` for each element of
            *scan_values*.  Must return **one** of:

            * ``float`` -- a single energy.  Stored under the key
              ``"energy"`` in the results dict.
            * ``dict[str, float]`` -- multiple labelled energies
              (e.g. ``{"PBE": -31.4, "RVV10": -31.5}``).
        scan_label : str, optional
            Human-readable label for the scan coordinate (used in
            screen output and CSV header).  Default ``"x"``.
        save_csv : str or None, optional
            Path to write a CSV file with the results.  ``None`` (default)
            skips writing.

        Returns
        -------
        scan_values : np.ndarray
            The scan grid (as a NumPy array).
        energies : dict[str, np.ndarray]
            ``{label: energy_array}`` with one entry per label returned
            by *compute_energy*.

        Examples
        --------
        Single energy per point (plain QEpy SCF)::

            def calc(d):
                opts = update_geometry(qe_options, d)
                drv = Driver(qe_options=opts, iterative=False, logfile=f'd_{d:.2f}.out')
                E = drv.get_energy()
                drv.stop()
                return E

            grid, energies = Driver.compute_pes(
                np.linspace(2.8, 5.0, 20), calc, scan_label="d (A)")

        Multiple energies per point (e.g. different XC mixes)::

            def calc(d):
                opts = update_geometry(qe_options, d)
                return {"PBE": run_scf(opts, "PBE"),
                        "RVV10": run_scf(opts, "RVV10")}

            grid, energies = Driver.compute_pes(
                np.linspace(2.8, 5.0, 20), calc, scan_label="d (A)",
                save_csv="pes.csv")
        """
        scan_values = np.asarray(scan_values, dtype=float)
        n_points = len(scan_values)

        print(f"PES scan: {n_points} points along {scan_label}")
        print("=" * 60)

        energies = None
        labels = None

        for i, val in enumerate(scan_values):
            print(f"\n[{i + 1}/{n_points}] {scan_label} = {val:.6f}")

            result = compute_energy(val)

            if isinstance(result, (int, float, np.floating)):
                result = {"energy": float(result)}

            if energies is None:
                labels = list(result.keys())
                energies = {lab: np.zeros(n_points) for lab in labels}

            for lab, eng in result.items():
                energies[lab][i] = eng
                print(f"  {lab}: E = {eng:.10f}")

        print("\n" + "=" * 60)
        print("PES scan complete.")

        if save_csv and energies is not None:
            with open(save_csv, "w", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow([scan_label] + [f"E_{l}" for l in labels])
                for i, val in enumerate(scan_values):
                    writer.writerow(
                        [f"{val:.6f}"] + [f"{energies[l][i]:.12f}" for l in labels]
                    )
            print(f"Results saved to {save_csv}")

        return scan_values, energies
