#!/bin/bash
# Amarel (Rutgers HPC): source inside SLURM jobs on main-redhat compute nodes.
# Head node: amarel-new.hpc.rutgers.edu (RHEL 9.6)
# Do NOT use mpirun/mpiexec on RHEL 9 compute nodes (segfault).
# Multi-rank: srun --mpi=pmi2 -n N   (SLURM MpiDefault=none on Amarel)
# Serial:     srun -n 1

source /etc/profile.d/modules.sh
module load intel/18.0.5

export BUILD_ROOT="${BUILD_ROOT:-$HOME/qe_build}"
export PATH="$BUILD_ROOT/fakebin:$BUILD_ROOT/venv_py39/bin:$PATH"

export CC=gcc CXX=g++ FC=ifort F90=ifort
export I_MPI_CC=gcc I_MPI_CXX=g++ I_MPI_FC=ifort I_MPI_F77=ifort
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
ulimit -s unlimited

export qedir="$BUILD_ROOT/q-e"
export C_INCLUDE_PATH="$BUILD_ROOT/python39/include/python3.9"
export PKG_CONFIG_PATH="$BUILD_ROOT/python39/lib/pkgconfig:${PKG_CONFIG_PATH:-}"

# Optional: activate venv for interactive use
if [ -f "$BUILD_ROOT/venv_py39/bin/activate" ]; then
  source "$BUILD_ROOT/venv_py39/bin/activate"
fi
