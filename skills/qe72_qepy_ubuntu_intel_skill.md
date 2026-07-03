# Skill: Build Quantum ESPRESSO 7.2 and QEpy on Ubuntu with Intel MPI and MKL

## Which skill to use

| Goal | Skill file |
|------|------------|
| **Ubuntu — Intel MPI + oneMKL** (Linux default) | `qe72_qepy_ubuntu_intel_skill.md` (this file) |
| **RHEL 9 — Intel MPI + oneMKL** (Linux default) | `qe72_qepy_rhel9_intel_skill.md` |
| **Ubuntu — Open MPI + OpenBLAS** (open-source alternative) | `qe72_qepy_ubuntu_openblas_skill.md` |
| **RHEL 9 — Open MPI + OpenBLAS** (open-source alternative) | `qe72_qepy_rhel9_openblas_skill.md` |
| **macOS default** — Apple Accelerate | `qe72_qepy_macos_accelerate_skill.md` |
| **Intel Mac with oneMKL** | `qe72_qepy_macos_mkl_skill.md` |

Use **this skill** as the **standard Ubuntu / Linux path**: **Intel MPI + oneMKL** from Intel oneAPI. Install the [Intel oneAPI Base Toolkit](https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit.html) (MKL + Intel MPI) before starting.

For an open-source stack from `apt` only (Colab, minimal VMs, or no oneAPI), use `qe72_qepy_ubuntu_openblas_skill.md`.

**Agent instruction:** on Ubuntu, use this skill by default. If Intel oneAPI is not installed and cannot be installed, fall back to the OpenBLAS skill. Ask for the QEpy venv name (default `venv_qepy`).

---

## Purpose

This skill builds on Ubuntu with:

- Quantum ESPRESSO tag `qe-7.2`
- QEpy from its `dev` branch
- GCC/GFortran 14 from Ubuntu packages
- Intel MPI and oneMKL from Intel oneAPI
- FFTW from `libfftw3-dev`
- a dedicated Python virtual environment (default `venv_qepy`)

Primary target: **Ubuntu 24.04 LTS**. Ubuntu 22.04 can use `gcc-12` / `gfortran-12` if GCC 14 is unavailable.

**Important:** point Intel MPI at the GNU compilers with `I_MPI_CC` / `I_MPI_FC`. Do not mix OpenBLAS and MKL in the same build.

---

# 1. Verify the system

```bash
lsb_release -a
uname -m
```

---

# 2. Install Ubuntu prerequisites

FFT and Python come from `apt`. MPI and BLAS/LAPACK come from Intel oneAPI.

## Ubuntu 24.04 LTS

```bash
sudo apt update
sudo apt install -y \
  git make wget curl gfortran-14 gcc-14 g++-14 \
  libfftw3-dev \
  python3.12 python3.12-venv python3-pip

export CC=gcc-14
export FC=gfortran-14
export F77="$FC"
export F90="$FC"
export CXX=g++-14
export PYTHON=python3.12
```

## Ubuntu 22.04 LTS

```bash
sudo apt update
sudo apt install -y \
  git make wget curl gfortran-12 gcc-12 g++-12 \
  libfftw3-dev \
  python3.11 python3.11-venv python3-pip

export CC=gcc-12
export FC=gfortran-12
export F77="$FC"
export F90="$FC"
export CXX=g++-12
export PYTHON=python3.11
```

Verify:

```bash
"$CC" --version
ls /usr/include/fftw3.f03
```

---

# 3. Install Intel oneAPI (MKL + Intel MPI)

Download the Intel oneAPI Base Toolkit for Linux. Install to:

```text
/opt/intel/oneapi
```

```bash
chmod +x ./l_BaseKit_p_*.sh
sudo ./l_BaseKit_p_*.sh
```

Select oneMKL and Intel MPI. Silent install (verify `-h` first):

```bash
sudo ./l_BaseKit_p_*.sh -a --silent --eula accept
```

Verify:

```bash
test -f /opt/intel/oneapi/setvars.sh
ls /opt/intel/oneapi/mkl/latest/lib/libmkl_core.so
ls /opt/intel/oneapi/mpi/latest/bin/mpif90
```

---

# 4. Initialize oneAPI, MKL, and Intel MPI

```bash
source /opt/intel/oneapi/setvars.sh

export I_MPI_CC="$CC"
export I_MPI_FC="$FC"
export I_MPI_F77="$FC"
export I_MPI_CXX="$CXX"

export MPI_ROOT="/opt/intel/oneapi/mpi/latest"
export PATH="$MPI_ROOT/bin:$PATH"

export MKLROOT="${MKLROOT:-/opt/intel/oneapi/mkl/latest}"
if [ -d "$MKLROOT/lib/intel64" ]; then
    export MKLLIB="$MKLROOT/lib/intel64"
else
    export MKLLIB="$MKLROOT/lib"
fi

if ls "$MKLLIB"/libmkl_gf_lp64.* >/dev/null 2>&1; then
    export MKL_INTERFACE_LIB=mkl_gf_lp64
elif ls "$MKLLIB"/libmkl_intel_lp64.* >/dev/null 2>&1; then
    export MKL_INTERFACE_LIB=mkl_intel_lp64
else
    echo "No LP64 MKL interface found" >&2
    exit 1
fi

export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

Verify:

```bash
which mpif90
mpif90 -show 2>/dev/null || true
test -f "$MKLROOT/include/mkl.h"
```

---

# 5. Verify the MKL link line

```bash
cat > /tmp/test_mkl.f90 <<'EOF'
program test_mkl
  implicit none
  double precision :: x(2), y(2)
  double precision, external :: ddot
  x = [1.0d0, 2.0d0]
  y = [3.0d0, 4.0d0]
  print *, ddot(2, x, 1, y, 1)
end program test_mkl
EOF

"$FC" /tmp/test_mkl.f90 \
  -L"$MKLLIB" -l"$MKL_INTERFACE_LIB" -lmkl_sequential -lmkl_core \
  -lpthread -lm -Wl,-rpath,"$MKLLIB" -o /tmp/test_mkl

/tmp/test_mkl
ldd /tmp/test_mkl | grep -i mkl
```

Expected output: `11.0000000000000`. Do not continue until this passes.

---

# 6. Working directory and clones

```bash
mkdir -p "$HOME/qe_build" && cd "$HOME/qe_build"
export BUILD_ROOT="$PWD"
export QE_ROOT="$BUILD_ROOT/q-e"
export QEPY_ROOT="$BUILD_ROOT/QEpy"
export VENV_NAME="${VENV_NAME:-venv_qepy}"
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"

git clone --branch qe-7.2 --single-branch \
  https://gitlab.com/QEF/q-e.git "$QE_ROOT"
cd "$QE_ROOT" && git submodule update --init --recursive

cd "$BUILD_ROOT"
git clone https://github.com/Quantum-MultiScale/QEpy.git "$QEPY_ROOT"
cd "$QEPY_ROOT" && git checkout dev
```

---

# 7. Python environment

```bash
cd "$BUILD_ROOT"
"$PYTHON" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install \
  "numpy<2" "f90wrap==0.2.14" meson ninja packaging
```

Use `check_qepy_venv` from `qe72_qepy_ubuntu_openblas_skill.md` section 8 if reusing an existing venv.

---

# 8. Configure Quantum ESPRESSO

```bash
source /opt/intel/oneapi/setvars.sh
export I_MPI_CC="$CC" I_MPI_FC="$FC"
export PATH="/opt/intel/oneapi/mpi/latest/bin:$PATH"

cd "$QE_ROOT"
./configure \
  CC="$CC" F77="$FC" F90="$FC" MPIF90=mpif90 \
  CFLAGS="-fPIC" \
  FFLAGS="-fPIC -fallow-argument-mismatch" \
  BLAS_LIBS="-L$MKLLIB -l$MKL_INTERFACE_LIB -lmkl_sequential -lmkl_core -lpthread -lm" \
  LAPACK_LIBS=""
```

---

# 9. Required `make.inc` corrections

```make
F90     = gfortran-14
MPIF90  = mpif90
CC      = gcc-14
CPP     = gcc-14 -E -P

CPPFLAGS = $(DFLAGS) $(IFLAGS)

CFLAGS = -fPIC $(DFLAGS) $(IFLAGS) $(CUDA_CFLAGS)
FFLAGS = -fPIC -fallow-argument-mismatch
F90FLAGS = $(FFLAGS) -cpp $(FDFLAGS) \
           $(CUDA_F90FLAGS) $(IFLAGS) $(MODFLAGS)

MKLROOT = /opt/intel/oneapi/mkl/latest
MKLLIB  = $(MKLROOT)/lib/intel64

IFLAGS = -I. -I$(TOPDIR)/include -I/usr/include -I$(MKLROOT)/include
FFT_LIBS = -L/usr/lib/x86_64-linux-gnu -lfftw3

LDFLAGS = -L$(MKLLIB) -Wl,-rpath,$(MKLLIB)

BLAS_LIBS = -L$(MKLLIB) \
            -lmkl_gf_lp64 -lmkl_sequential -lmkl_core -lpthread -lm
LAPACK_LIBS =
```

On Ubuntu 22.04 with GCC 12, use `gcc-12` / `gfortran-12`. On `aarch64`, adjust library paths.

Remove: `-lopenblas`, `-lblas`, `-llapack`.

---

# 10. Build QE and QEpy

```bash
cd "$QE_ROOT"
make clean || true
find . -name '*.o' -delete
find . -name '*.mod' -delete
find . -name '*.a' -delete
make all

ldd "$QE_ROOT/bin/pw.x" | grep -i mkl
ldd "$QE_ROOT/bin/pw.x" | grep -E 'openblas|libblas' || true
```

```bash
source "$VENV_DIR/bin/activate"
source /opt/intel/oneapi/setvars.sh
export I_MPI_CC="$CC" I_MPI_FC="$FC"

cd "$QEPY_ROOT"
rm -rf build dist qepy.egg-info
qedir="$QE_ROOT" python -m pip install --no-build-isolation --no-cache-dir -v .
```

---

# 11. Test

```bash
cd /tmp
python -c "import qepy; import qepy.qepylibs; print(qepy.__file__)"
```

---

# 12. Troubleshooting

## Intel MPI uses wrong compiler

```bash
export I_MPI_CC="$CC"
export I_MPI_FC="$FC"
source /opt/intel/oneapi/setvars.sh
```

## `MKLROOT` empty

```bash
source /opt/intel/oneapi/setvars.sh
```

## QE links OpenBLAS

Remove `-lopenblas` from `make.inc` and rebuild clean. Use the OpenBLAS skill if MKL is not required.

## Other issues

See `qe72_qepy_rhel9_intel_skill.md` sections on MKL runtime, missing QE components, and QEpy import errors — the fixes are the same on Ubuntu.

---

# 13. Condensed procedure (Ubuntu 24.04)

```bash
sudo apt update
sudo apt install -y git make wget curl gfortran-14 gcc-14 \
  libfftw3-dev python3.12 python3.12-venv python3-pip
export CC=gcc-14 FC=gfortran-14 PYTHON=python3.12

# Install Intel oneAPI Base Toolkit, then:
source /opt/intel/oneapi/setvars.sh
export I_MPI_CC="$CC" I_MPI_FC="$FC"
export MKLROOT=/opt/intel/oneapi/mkl/latest
export MKLLIB="$MKLROOT/lib/intel64"
export MKL_INTERFACE_LIB=mkl_gf_lp64

# clone, venv, configure with MKL, fix make.inc, make all, build QEpy
```

---

## Design choices

- **Intel oneAPI on Linux** is the standard stack (Intel MPI + oneMKL).
- **GFortran from Ubuntu** drives QE; Intel MPI wraps it via `I_MPI_FC`.
- **Sequential MKL** avoids MPI/OpenMP oversubscription during initial bring-up.
- **Open-source fallback (Open MPI + OpenBLAS):** use `qe72_qepy_ubuntu_openblas_skill.md`.
