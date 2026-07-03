.. _faq:


==========================
Frequently Asked Questions
==========================

Installation
============

What is the `tddft=yes`?
------------------------

  Support real-time TDDFT by using `ce-tddft <https://github.com/dceresoli/ce-tddft>`__. And the real-time TDDFT also support adding/replacing external potential.

Can I use CMake for QE installation?
------------------------------------

  No. Please use the traditional `configure` way to compile QE.

Running
=======

*Error in routine allocate_fft* or *Error in routine  fft_type_set*
-------------------------------------------------------------------

  The qepy has to be imported before the mpi4py package. The simplest approach to fix is add ``import qepy`` as the first line of the script.

Some Intel MKL errors occur. What do I do?
----------------------------------------------

  Try:

   .. code:: shell

    export LD_PRELOAD=/opt/intel/oneapi/mkl/latest/lib/libmkl_rt.so

Some Intel MPI errors occur.
----------------------------------------------

  Try:

   .. code:: shell

    export LD_PRELOAD=/opt/intel/oneapi/mpi/latest/lib/libmpifort.so

Why can’t I read the wavefunctions? Why does it hang?
-----------------------------------------------------

-  There are two different ways to store wavefunctions in QE, which is controls by PW parameter `wf_collect <http://www.quantum-espresso.org/Doc/INPUT_PW.html#idm68>`__.  In doubt, simply use one processor to read.

-  If the wavefunctions were stored by old version QE (<6.4) or `eQE <http://eqe.rutgers.edu>`__, please use the old version of QEpy by:

   .. code:: shell

    python -m pip install qepy==6.5.0

Some f90wrap errors occur. What do I do?
----------------------------------------

  Please try install the latest `f90wrap <https://github.com/jameskermode/f90wrap>`__ . e.g.

   .. code:: shell

    python -m pip install --upgrade f90wrap

Signal: Segmentation fault...
-----------------------------

-  `QEpy` and `mpi4py` should installed with same compiler. If not, try reinstall the `mpi4py` by:

   .. code:: shell

    python -m pip install mpi4py --no-cache-dir

BAD TERMINATION OF ONE OF YOUR APPLICATION PROCESSES
----------------------------------------------------

Without `mpi4py`, the QEpy still can parallel running, but you cannot control the parallel. If you want to run a different job, you have to restart the script or the jupyter kernel.
With `mpi4py` to run the parallel QEpy, you can add ``comm`` to ``Driver``, or directly use ``comm.py2f()`` in the function.


Bugs
====

GCC
---
   For new version of gcc (eg. gcc=11.2) with LTO supported or under conda environment, if you met the problem when you install the QEpy_:

       +  *lto1: fatal error:...*

   Try disable link-time-optimization by add ``-fno-lto`` to the variable **FFLAGS** and **CFLAGS**.


Gfortran
--------

   #. For gfortran>=10.0 sometimes still works, but will has error:

      -  *Type mismatch between actual argument...*

      Try to add ``-fallow-argument-mismatch`` to the variable **FFLAGS** (e.g. ``FFLAGS='-fPIC -fallow-argument-mismatch'``).


   #. For a few versions of BLAS library, will raise error:

      -  *Segmentation fault - invalid memory reference...*

      This is due to the `zdotc` function of external libraries. More details to `here <https://gitlab.com/QEF/q-e/-/wikis/Support/zdotc-crash>`__. One solution is append the ``-ff2c`` to **CFLAGS**  of QE. For example, the following can be used for MacOS with Apple silicon:

     .. code:: shell

        ./configure FFLAGS='-fPIC -fallow-argument-mismatch -ff2c -fno-second-underscore' CFLAGS='-fPIC -arch arm64' CPP='gcc -E' LDFLAGS=-headerpad_max_install_names


Intel Compiler
--------------

   #. If you met any problems like the following, please try a newer Intel compiler or GNU compiler.

       +  *[MPID_nem_tmi_pending_ssend_dequeue]: ERROR: can not find matching ssend...*
       +  The initial density totally wrong with more than one nodes.

   #. The gcc version between 4.8-9.2 are supported by intel compiler, which upgraded until 2022.1 version. More details to `here <https://community.intel.com/t5/Intel-oneAPI-Data-Parallel-C/Compilation-issues-with-ICPC-2021-4-and-C-14/td-p/1318571>`__.

      + *...error: attribute "__malloc__" does not take arguments...*

OpenMPI
-------

   If you met some problems like the following:

   -  *mca_base_component_repository_open: unable to open
      mca_patcher_overwrite...*

   Please update to latest version of OpenMPI, or fix with ``patchelf``
   (`openmpi=2.1.1 <https://github.com/open-mpi/ompi/issues/3705>`__):

   .. code:: shell

      #!/bin/sh
      prefix="/usr/lib/x86_64-linux-gnu/openmpi"
      for filename in $(ls $prefix/lib/openmpi/*.so); do
          patchelf --add-needed libmpi.so.20 $filename
          patchelf --set-rpath "\$ORIGIN/.." $filename
      done


.. _QEpy: https://github.com/Quantum-MultiScale/QEpy
.. _DFTpy: http://dftpy.rutgers.edu

MacOS
-----

   #. For some versions of the MacOS, maybe you will has error:

      - *Illegal Instruction: 4...*

      Try to add ``-mmacosx-version-min=10.14`` to the **FFLAGS**. 

     
   #. *clang: error: no input files...*

      Redefine *CPP* as *CPP=gcc -E* in `make.inc <https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf>`__.

   #. *changing install names or rpaths can't be redone for...*

      Add ``-headerpad_max_install_names`` to the **LDFLAGS**.

QE
--
   #. *compilation aborted for mbd_c_api.F90*

      *ifx* not works for mbd until `#60 <https://github.com/libmbd/libmbd/pull/60>`__. The easiest way to fix is running the following before `make`

   .. code:: shell

      export LIBMBD_C_API=0


Abandon
=======
  - Read old format XML file

    The old format (**-D__OLDXML**) has been deprecated since `version 6.4 <https://gitlab.com/QEF/q-e/-/releases/qe-6.4>`__. ``oldxml`` allows you to read the output (wavefunctions, etc) from an old XML file. Last version to support it is `qepy==6.5.0`.
