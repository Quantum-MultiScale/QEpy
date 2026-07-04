# Skill: Build Quantum ESPRESSO 7.2 and QEpy on RHEL 9 with Intel MPI and MKL

## Bare metal / VM vs HPC cluster

| Environment | Use this skill? | Notes |
|-------------|-----------------|-------|
| **RHEL 9 VM or workstation** (you have `sudo`, can run `dnf` and the oneAPI installer) | **Yes — this file** | Full procedure below with `gcc-toolset-14`, `dnf`, and `/opt/intel/oneapi` |
| **HPC cluster** (no `sudo`, only `module load …`, SLURM/PBS) | **No — use the site skill** | Do **not** run `sudo dnf` or the oneAPI installer. Load site modules, submit builds via the scheduler, and use the cluster launcher (`srun`, `mpirun`, etc.) documented for that system. Example: [`qe72_qepy_amarel_skill.md`](qe72_qepy_amarel_skill.md) (Rutgers Amarel). Generic HPC notes: [§16 HPC clusters](#16-hpc-clusters-with-environment-modules-no-sudo). |

**Agent instruction:** if the user is on a shared cluster, SSH login node, or says they cannot use `sudo`, treat this as **HPC** and follow §16 plus any site-specific skill — not the `dnf`/installer sections.

---

## Which skill to use

| Goal | Skill file |
|------|------------|
| **HPC cluster (no sudo, modules only)** | Site skill, e.g. [`qe72_qepy_amarel_skill.md`](qe72_qepy_amarel_skill.md) |
| **Ubuntu — Intel MPI + oneMKL** (Linux default) | `qe72_qepy_ubuntu_intel_skill.md` |
| **RHEL 9 — Intel MPI + oneMKL** (Linux default, **sudo required**) | `qe72_qepy_rhel9_intel_skill.md` (this file) |
| **Ubuntu — Open MPI + OpenBLAS** (open-source alternative) | `qe72_qepy_ubuntu_openblas_skill.md` |
| **RHEL 9 — Open MPI + OpenBLAS** (open-source alternative) | `qe72_qepy_rhel9_openblas_skill.md` |
| **macOS default** — Apple Accelerate | `qe72_qepy_macos_accelerate_skill.md` |
| **Intel Mac with oneMKL** — archived Intel oneAPI 2023.x | `qe72_qepy_macos_mkl_skill.md` |

Use **this skill** as the **standard RHEL 9 / Linux path**: **Intel MPI + oneMKL** from Intel oneAPI. Install the [Intel oneAPI Base Toolkit](https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit.html) (MKL + Intel MPI) or load site modules before starting.

For a build using only EL9 `dnf` packages (Open MPI + OpenBLAS), use `qe72_qepy_rhel9_openblas_skill.md`.

**Agent instruction:** on RHEL 9, use this skill by default. If Intel oneAPI is not available and cannot be installed, or the user explicitly wants open-source packages only, fall back to the OpenBLAS skill. Ask for the QEpy venv name (default `venv_qepy`).

---

## Purpose

This skill gives a reproducible, start-to-finish procedure for building:

- Quantum ESPRESSO tag `qe-7.2`
- QEpy compatible with QE 7.2
- a dedicated Python 3.11 virtual environment (user-chosen name; default `venv_qepy`)
- GCC/GFortran 14 from `gcc-toolset-14`
- Intel MPI from Intel oneAPI
- Intel oneMKL for BLAS and LAPACK
- FFTW from EL9 repositories

The Quantum ESPRESSO 7.2 release is tagged `qe-7.2` in the official QEF GitLab repository.

**Agent instruction:** before creating or reusing a virtual environment, ask the user what name they want for the QEpy Python environment. If they have no preference, use `venv_qepy`.

**Important:** use one compiler stack consistently for QE, Intel MPI wrappers, and QEpy. After enabling `gcc-toolset-14`, point Intel MPI at those compilers with `I_MPI_*` variables and keep the toolset `bin` directory early in `PATH`.

---

# 1. Verify the system

Confirm RHEL 9 or a compatible EL9 derivative:

```bash
cat /etc/redhat-release
uname -m
```

Expected examples:

```text
Red Hat Enterprise Linux release 9.x
x86_64
```

This procedure is written for `x86_64`. Adapt package names if you are on `aarch64` (Intel oneAPI component availability may differ).

Check for root/sudo access — system packages and the Intel installer require it. **On HPC clusters you typically do not have sudo**; use §16 and a site skill instead of this section.

---

# 2. Enable required repositories

Enable CodeReady Builder if you need additional development packages:

## RHEL 9

```bash
sudo subscription-manager repos \
  --enable codeready-builder-for-rhel-9-$(uname -m)-rpms
```

## Rocky Linux 9 / AlmaLinux 9

```bash
sudo dnf config-manager --set-enabled crb
```

Refresh metadata:

```bash
sudo dnf makecache
```

---

# 3. Install EL9 prerequisites

Install GCC toolset 14, FFTW, Python, and basic tools. MPI and BLAS/LAPACK come from Intel oneAPI.

```bash
sudo dnf install -y \
  git make wget which \
  gcc-toolset-14 \
  gcc-toolset-14-gcc \
  gcc-toolset-14-gcc-gfortran \
  gcc-toolset-14-gcc-c++ \
  fftw-devel \
  python3.11 \
  python3.11-devel \
  python3.11-pip
```

Verify:

```bash
rpm -q gcc-toolset-14-gcc-gfortran fftw-devel python3.11
ls /usr/include/fftw3.f03
```

---

# 4. Install Intel oneAPI (MKL + Intel MPI)

Download the Intel oneAPI Base Toolkit for Linux from Intel's official distribution channel. The Base Toolkit includes oneMKL and Intel MPI.

Typical installation root:

```text
/opt/intel/oneapi
```

## Offline / interactive installer

After downloading the Base Kit installer:

```bash
chmod +x ./l_BaseKit_p_*.sh
sudo ./l_BaseKit_p_*.sh
```

Select at minimum:

- Intel oneAPI Math Kernel Library (oneMKL)
- Intel MPI Library

## Silent install example

Use only after verifying options with `./l_BaseKit_p_*.sh -h`:

```bash
sudo ./l_BaseKit_p_*.sh -a --silent --eula accept
```

## Verify installation

```bash
test -f /opt/intel/oneapi/setvars.sh
ls /opt/intel/oneapi/mkl/latest/lib/libmkl_core.so
ls /opt/intel/oneapi/mpi/latest/bin/mpif90
```

If your site already provides oneAPI through modules, skip the installer and load the site module instead (see section 15).

---

# 5. Initialize oneAPI, MKL, and Intel MPI

Source oneAPI and GCC toolset 14 in this order:

```bash
source /opt/rh/gcc-toolset-14/enable
source /opt/intel/oneapi/setvars.sh
```

Define compiler paths:

```bash
export GCC_ROOT="/opt/rh/gcc-toolset-14/root/usr"
export CC="$GCC_ROOT/bin/gcc"
export FC="$GCC_ROOT/bin/gfortran"
export F77="$FC"
export F90="$FC"
export CXX="$GCC_ROOT/bin/g++"
```

Point Intel MPI at the toolset GNU compilers:

```bash
export I_MPI_CC="$CC"
export I_MPI_FC="$FC"
export I_MPI_F77="$FC"
export I_MPI_CXX="$CXX"
```

Put toolset and Intel MPI wrappers on `PATH`:

```bash
export MPI_ROOT="/opt/intel/oneapi/mpi/latest"
export PATH="$GCC_ROOT/bin:$MPI_ROOT/bin:$PATH"
```

Locate MKL:

```bash
export MKLROOT="${MKLROOT:-/opt/intel/oneapi/mkl/latest}"

if [ -d "$MKLROOT/lib/intel64" ]; then
    export MKLLIB="$MKLROOT/lib/intel64"
else
    export MKLLIB="$MKLROOT/lib"
fi
```

Select the LP64 interface library for GFortran:

```bash
if ls "$MKLLIB"/libmkl_gf_lp64.* >/dev/null 2>&1; then
    export MKL_INTERFACE_LIB=mkl_gf_lp64
elif ls "$MKLLIB"/libmkl_intel_lp64.* >/dev/null 2>&1; then
    export MKL_INTERFACE_LIB=mkl_intel_lp64
else
    echo "No LP64 oneMKL interface library found in $MKLLIB" >&2
    exit 1
fi
```

Verify:

```bash
echo "MKLROOT=$MKLROOT"
echo "MKLLIB=$MKLLIB"
echo "MKL_INTERFACE_LIB=$MKL_INTERFACE_LIB"
"$CC" --version
"$FC" --version
which mpif90
mpif90 -show 2>/dev/null || mpif90 --version
test -f "$MKLROOT/include/mkl.h"
ls "$MKLLIB"/libmkl_core.*
```

Expected:

- `gcc` / `gfortran` report version 14.x from the toolset
- `mpif90` resolves under `/opt/intel/oneapi/mpi/...`
- Intel MPI uses the toolset compilers via `I_MPI_FC` / `I_MPI_CC`

Use sequential MKL threading initially:

```bash
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

Do not mix GCC toolset 14 with GCC 15 module files. Do not mix stock `/usr/bin/gfortran` with toolset-built QE objects.

---

# 6. Verify the MKL link line before building QE

Create a small Fortran BLAS test:

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
```

Compile:

```bash
"$FC" /tmp/test_mkl.f90 \
  -L"$MKLLIB" \
  -l"$MKL_INTERFACE_LIB" \
  -lmkl_sequential \
  -lmkl_core \
  -lpthread \
  -lm \
  -Wl,-rpath,"$MKLLIB" \
  -o /tmp/test_mkl
```

Run:

```bash
/tmp/test_mkl
```

Expected:

```text
11.0000000000000
```

Confirm dynamic linkage:

```bash
ldd /tmp/test_mkl | grep -i mkl
```

Do not continue until this test succeeds.

---

# 7. Create a clean working directory

```bash
mkdir -p "$HOME/qe_build"
cd "$HOME/qe_build"
```

Define reusable paths:

```bash
export BUILD_ROOT="$PWD"
export QE_ROOT="$BUILD_ROOT/q-e"
export QEPY_ROOT="$BUILD_ROOT/QEpy"
```

**Ask the user** which name to use for the QEpy Python virtual environment. If they have no preference, use:

```text
venv_qepy
```

```bash
export VENV_NAME="${VENV_NAME:-venv_qepy}"
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"
echo "QEpy virtual environment: $VENV_DIR"
```

---

# 8. Clone Quantum ESPRESSO 7.2

```bash
git clone \
  --branch qe-7.2 \
  --single-branch \
  https://gitlab.com/QEF/q-e.git \
  "$QE_ROOT"

cd "$QE_ROOT"
git submodule update --init --recursive
git describe --tags --exact-match
git rev-parse HEAD
```

Expected tag:

```text
qe-7.2
```

---

# 9. Clone QEpy

```bash
cd "$BUILD_ROOT"
git clone https://github.com/Quantum-MultiScale/QEpy.git "$QEPY_ROOT"
cd "$QEPY_ROOT"
git checkout dev
git rev-parse HEAD
```

---

# 10. Create or verify the Python environment

Re-load the build environment:

```bash
source /opt/rh/gcc-toolset-14/enable
source /opt/intel/oneapi/setvars.sh
```

## Create a new environment

```bash
cd "$BUILD_ROOT"
python3.11 -m venv "$VENV_DIR"
```

## Reuse an existing environment

If `$VENV_DIR` already exists, run the compatibility checks below instead of recreating it.

## Compatibility checks

```bash
check_qepy_venv() {
  local fail=0
  local py="$VENV_DIR/bin/python"

  echo "=== Checking $VENV_DIR ==="

  if [ ! -x "$py" ]; then
    echo "FAIL: $py not found or not executable"
    return 1
  fi

  local ver
  ver="$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  case "$ver" in
    3.10|3.11|3.12)
      echo "OK: Python $ver"
      ;;
    *)
      echo "FAIL: Python $ver (need 3.10, 3.11, or 3.12)"
      fail=1
      ;;
  esac

  local py_arch gcc_arch
  py_arch="$(file -b "$py" | awk -F': ' '/architecture/ {print $2; exit}')"
  gcc_arch="$(file -b "$CC" | awk -F': ' '/architecture/ {print $2; exit}')"
  if [ "$py_arch" != "$gcc_arch" ]; then
    echo "FAIL: Python is $py_arch but $CC is $gcc_arch"
    fail=1
  else
    echo "OK: Python architecture $py_arch matches toolchain"
  fi

  if [ -f "$VENV_DIR/pyvenv.cfg" ] && grep -q 'include-system-site-packages = true' "$VENV_DIR/pyvenv.cfg"; then
    echo "WARN: include-system-site-packages = true (prefer false)"
  else
    echo "OK: isolated virtual environment"
  fi

  return $fail
}

check_qepy_venv || {
  echo "Virtual environment is not compatible with this build." >&2
  exit 1
}
```

Activate and install build dependencies:

```bash
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install \
  "numpy<2" \
  "f90wrap==0.2.14" \
  meson \
  ninja \
  packaging
```

Verify:

```bash
python --version
file "$(which python)"
python -m pip show f90wrap
meson --version
ninja --version
```

---

# 11. Configure Quantum ESPRESSO

Reassert the full environment:

```bash
source /opt/rh/gcc-toolset-14/enable
source /opt/intel/oneapi/setvars.sh

export GCC_ROOT="/opt/rh/gcc-toolset-14/root/usr"
export CC="$GCC_ROOT/bin/gcc"
export FC="$GCC_ROOT/bin/gfortran"
export F77="$FC"
export F90="$FC"
export CXX="$GCC_ROOT/bin/g++"

export I_MPI_CC="$CC"
export I_MPI_FC="$FC"
export I_MPI_F77="$FC"
export I_MPI_CXX="$CXX"

export MPI_ROOT="/opt/intel/oneapi/mpi/latest"
export PATH="$GCC_ROOT/bin:$MPI_ROOT/bin:$PATH"

export MKLROOT="${MKLROOT:-/opt/intel/oneapi/mkl/latest}"
if [ -d "$MKLROOT/lib/intel64" ]; then
    export MKLLIB="$MKLROOT/lib/intel64"
else
    export MKLLIB="$MKLROOT/lib"
fi

export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

Enter the QE source tree:

```bash
cd "$QE_ROOT"
```

Run `configure` with position-independent code and MKL:

```bash
./configure \
  CC="$CC" \
  F77="$FC" \
  F90="$FC" \
  MPIF90=mpif90 \
  CFLAGS="-fPIC" \
  FFLAGS="-fPIC -fallow-argument-mismatch" \
  BLAS_LIBS="-L$MKLLIB -l$MKL_INTERFACE_LIB -lmkl_sequential -lmkl_core -lpthread -lm" \
  LAPACK_LIBS=""
```

The configure step creates `make.inc`.

---

# 12. Required `make.inc` corrections

Open:

```bash
nano "$QE_ROOT/make.inc"
```

## Compiler definitions

```make
F90     = /opt/rh/gcc-toolset-14/root/usr/bin/gfortran
MPIF90  = mpif90
CC      = /opt/rh/gcc-toolset-14/root/usr/bin/gcc
CPP     = /opt/rh/gcc-toolset-14/root/usr/bin/gcc -E -P
```

`CC` must not contain `-E -P`.

## Preprocessor flags

```make
CPPFLAGS = $(DFLAGS) $(IFLAGS)
```

## Position-independent compiler flags

```make
CFLAGS = -fPIC $(DFLAGS) $(IFLAGS) $(CUDA_CFLAGS)

FFLAGS = -fPIC -fallow-argument-mismatch

F90FLAGS = $(FFLAGS) -cpp $(FDFLAGS) \
           $(CUDA_F90FLAGS) $(IFLAGS) $(MODFLAGS)
```

QEpy needs QE object files compiled with `-fPIC`.

## FFTW and MKL include paths

Keep FFTW separate from MKL for this configuration:

```make
MKLROOT = /opt/intel/oneapi/mkl/latest
MKLLIB  = $(MKLROOT)/lib/intel64

IFLAGS = -I. -I$(TOPDIR)/include \
         -I/usr/include \
         -I$(MKLROOT)/include
```

If `MKLROOT` is versioned rather than `latest`, use that exact path.

```make
FFT_LIBS = -L/usr/lib64 -lfftw3
```

## BLAS and LAPACK (oneMKL)

Use the GNU Fortran interface if available:

```make
LDFLAGS = -L$(MKLLIB) -Wl,-rpath,$(MKLLIB)

BLAS_LIBS = -L$(MKLLIB) \
            -lmkl_gf_lp64 \
            -lmkl_sequential \
            -lmkl_core \
            -lpthread -lm

LAPACK_LIBS =
```

If only `libmkl_intel_lp64` is installed, replace `-lmkl_gf_lp64` with `-lmkl_intel_lp64`.

Remove stale alternatives if `configure` inserted them:

```make
-lblas
-llapack
-lopenblas
-framework Accelerate
```

Check the Fortran FFTW interface:

```bash
ls /usr/include/fftw3.f03
```

---

# 13. Build all of Quantum ESPRESSO

Clean first if this is not a fresh tree:

```bash
cd "$QE_ROOT"

make clean || true
find . -name '*.o' -delete
find . -name '*.mod' -delete
find . -name '*.a' -delete
```

Build the full suite:

```bash
make all
```

Do not build only `pw.x`.

QEpy requires object and module files from several components, including:

- `atomic` / `ld1`
- `CPV`
- `GWW/minpack`
- `KS_Solvers`
- `Modules`
- `UtilXlib`
- `LAXlib`
- `FFTXlib`
- `upflib`
- `XClib`
- `MBD`

Verify key files:

```bash
find "$QE_ROOT/atomic" -name 'ld1inc.mod'
ls "$QE_ROOT/GWW/minpack/dpmpar.o"
ls "$QE_ROOT/CPV/src/"*.o | head
```

Test the main executable:

```bash
"$QE_ROOT/bin/pw.x" < /dev/null 2>&1 | head -5
file "$QE_ROOT/bin/pw.x"
ldd "$QE_ROOT/bin/pw.x" | grep -E 'mkl|mpi|fftw'
```

Confirm MKL linkage:

```bash
ldd "$QE_ROOT/bin/pw.x" | grep -i mkl
```

Confirm OpenBLAS or system BLAS were not linked:

```bash
ldd "$QE_ROOT/bin/pw.x" | grep -E 'openblas|libblas|liblapack'
```

Ideally the second command returns no output.

---

# 14. Configure MKL runtime and build QEpy

Set runtime behavior:

```bash
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

Optional: add to the venv activation script:

```bash
cat >> "$VENV_DIR/bin/activate" <<EOF

# QE/QEpy Intel oneAPI runtime
export MKLROOT="$MKLROOT"
export MKLLIB="$MKLLIB"
export LD_LIBRARY_PATH="$MKLLIB:\${LD_LIBRARY_PATH:-}"
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export I_MPI_CC=$CC
export I_MPI_FC=$FC
EOF
```

Activate the environment and reload the toolchain:

```bash
source "$VENV_DIR/bin/activate"
check_qepy_venv

source /opt/rh/gcc-toolset-14/enable
source /opt/intel/oneapi/setvars.sh

export GCC_ROOT="/opt/rh/gcc-toolset-14/root/usr"
export CC="$GCC_ROOT/bin/gcc"
export FC="$GCC_ROOT/bin/gfortran"
export I_MPI_CC="$CC"
export I_MPI_FC="$FC"
export PATH="$GCC_ROOT/bin:/opt/intel/oneapi/mpi/latest/bin:$PATH"
```

Enter QEpy:

```bash
cd "$QEPY_ROOT"
rm -rf build dist
rm -rf qepy.egg-info 2>/dev/null || true
```

Install:

```bash
qedir="$QE_ROOT" \
python -m pip install \
  --no-build-isolation \
  --no-cache-dir \
  -v .
```

---

# 15. Test QEpy correctly

Do not test from inside the QEpy repository.

```bash
cd /tmp
python -c "import qepy; print(qepy.__file__)"
python -c "import qepy; import qepy.qepylibs; print('QEpy import successful')"
```

The import path should be inside:

```text
$VENV_DIR/lib/python3.11/site-packages/
```

Verify that QEpy shared libraries link MKL:

```bash
QEPY_SITE="$(
python - <<'PY'
from pathlib import Path
import qepy
print(Path(qepy.__file__).resolve().parent)
PY
)"

find "$QEPY_SITE" -name '*.so' -print0 |
while IFS= read -r -d '' lib; do
    if ldd "$lib" 2>/dev/null | grep -qi mkl; then
        echo "MKL linked: $lib"
        ldd "$lib" | grep -i mkl
    fi
done
```

At least some QEpy shared libraries should show oneMKL dependencies.

---

# 16. HPC clusters with environment modules (no sudo)

Use this section when the machine is a **shared HPC cluster**: no root, no `dnf install`, no oneAPI `.sh` installer — only **pre-loaded environment modules** and **batch jobs** (SLURM, PBS, LSF, etc.).

## What changes on HPC

| Bare metal (§1–15) | HPC cluster |
|--------------------|-------------|
| `sudo dnf install …` | **`module load`** compiler, MPI, MKL (names vary by site) |
| `./l_BaseKit_p_*.sh` installer | Site provides Intel/oneAPI or legacy Intel Parallel Studio modules |
| Interactive build on login node | **Submit builds to compute nodes** via `#SBATCH` / `sbatch` |
| `mpirun` / direct execution | Often **`srun`** (SLURM) or site wrapper; verify on a 1-rank smoke test first |
| `python3-devel` on same node | Compute nodes may lack headers — copy includes or build QEpy on head node |
| `venv_qepy` default | Use **`python -m venv --copies`**; **never conda** for QEpy (Meson breaks) |
| Shared nodes | Prefer **`#SBATCH --exclusive`** when allowed |

## Module discovery

```bash
module avail 2>&1 | grep -iE 'intel|oneapi|gcc|mkl|mpi|openmpi'
module spider intel
```

Common patterns (names differ by site):

```bash
module load intel/18.0.5          # legacy Parallel Studio (MKL + Intel MPI)
# or
module load gcc-toolset/14 oneapi # EL9 + community oneAPI module tree
```

After loading modules:

1. Re-export `CC`, `FC`, `I_MPI_CC`, `I_MPI_FC`, `MKLROOT`, and `MKLLIB`.
2. Run `check_qepy_venv`.
3. Confirm `which mpif90` or `which mpiifort` points to the intended MPI — not a mixed stack.
4. Test **`srun -n 1 pw.x`** (or site launcher) before multi-rank jobs.

Do not mix Intel MPI with Open MPI libraries in the same build.

## SLURM batch template (exclusive)

```bash
#!/bin/bash
#SBATCH --partition=YOUR_PARTITION
#SBATCH --exclusive
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=0
#SBATCH --time=03:00:00

source /etc/profile.d/modules.sh
module load intel/18.0.5   # site-specific

export BUILD_ROOT=$HOME/qe_build
export qedir=$BUILD_ROOT/q-e
export PATH=$BUILD_ROOT/venv_py39/bin:$PATH
export I_MPI_CC=gcc I_MPI_FC=ifort
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
ulimit -s unlimited

# build or test on compute node — not the login node
```

## QEpy pytest on HPC

- **Serial (validated on many legacy Intel-MPI clusters):** `srun -n 1 python -m pytest -v test_pwscf.py test_readfile.py`
- **Parallel (`pytest --with-mpi`, n≥2):** requires a working PMI/MPI stack on compute nodes. Older Intel MPI (2018) + SLURM may fail at `MPI_Init` / `PMI_KVS_Get`; use serial tests until the site upgrades MPI or documents a working launcher.
- Tests already guard user-visible output with `if driver.is_root:`; if parallel pytest works but lines appear twice, that is usually **both ranks running the pytest collector** — use `pytest --with-mpi` (not plain `srun -n 2 pytest` without it).

## Site-specific skills

| Cluster | Skill |
|---------|--------|
| Rutgers Amarel | [`qe72_qepy_amarel_skill.md`](qe72_qepy_amarel_skill.md) |

If no site skill exists, document the loaded modules, launcher, and any `make.inc` fixes in the user's project README before running a full build.

---

# 17. Troubleshooting

## Intel MPI uses the wrong compiler

Symptom: `mpif90 -show` or verbose output references `/usr/bin/gfortran`.

Fix:

```bash
source /opt/rh/gcc-toolset-14/enable
export GCC_ROOT="/opt/rh/gcc-toolset-14/root/usr"
export I_MPI_CC="$GCC_ROOT/bin/gcc"
export I_MPI_FC="$GCC_ROOT/bin/gfortran"
export PATH="$GCC_ROOT/bin:/opt/intel/oneapi/mpi/latest/bin:$PATH"
```

Rebuild QE from clean objects if the wrong compiler was used initially.

## `MKLROOT` is empty

```bash
source /opt/intel/oneapi/setvars.sh
echo "$MKLROOT"
```

or set it manually to the versioned MKL directory under `/opt/intel/oneapi/mkl/`.

## `ld: library not found for -lmkl_*`

Check:

```bash
echo "$MKLLIB"
ls "$MKLLIB"/libmkl_*
```

Correct `MKLLIB` to `$MKLROOT/lib/intel64` when that directory exists.

## Runtime cannot find `libmkl_core.so`

Ensure `make.inc` contains:

```make
-Wl,-rpath,$(MKLLIB)
```

and temporarily export:

```bash
export LD_LIBRARY_PATH="$MKLLIB:${LD_LIBRARY_PATH:-}"
```

## QE still links OpenBLAS or system BLAS

Remove from `make.inc`:

```text
-lopenblas
-lblas
-llapack
-framework Accelerate
```

Clean and rebuild.

## Incompatible Python virtual environment

Run `check_qepy_venv` from section 10.

## `fftw3.f03` is missing

```bash
sudo dnf install fftw-devel
```

## `laxlib.h` preprocessing failure

Fix:

```make
CC  = /opt/rh/gcc-toolset-14/root/usr/bin/gcc
CPP = /opt/rh/gcc-toolset-14/root/usr/bin/gcc -E -P
```

## GCC 15 MBD conflict (`f_c_string`)

Use `gcc-toolset-14` consistently. Do not build QE 7.2 with GCC 15.

## Missing `GWW/minpack` or `ld1inc.mod`

```bash
cd "$QE_ROOT"
make all
```

## QEpy cannot find Meson

```bash
source "$VENV_DIR/bin/activate"
python -m pip install meson ninja
```

## `import qepy` fails with `qepy.__config__` missing

```bash
cd /tmp
python -c "import qepy; print(qepy.__file__)"
```

---

# 18. Condensed full procedure

```bash
# EL9 packages
sudo subscription-manager repos \
  --enable codeready-builder-for-rhel-9-$(uname -m)-rpms
sudo dnf install -y \
  git make wget which \
  gcc-toolset-14 gcc-toolset-14-gcc gcc-toolset-14-gcc-gfortran \
  fftw-devel python3.11 python3.11-devel python3.11-pip

# Install Intel oneAPI Base Toolkit (MKL + Intel MPI), then:
source /opt/rh/gcc-toolset-14/enable
source /opt/intel/oneapi/setvars.sh

export GCC_ROOT="/opt/rh/gcc-toolset-14/root/usr"
export CC="$GCC_ROOT/bin/gcc"
export FC="$GCC_ROOT/bin/gfortran"
export F77="$FC"
export F90="$FC"
export I_MPI_CC="$CC"
export I_MPI_FC="$FC"
export PATH="$GCC_ROOT/bin:/opt/intel/oneapi/mpi/latest/bin:$PATH"

export MKLROOT="${MKLROOT:-/opt/intel/oneapi/mkl/latest}"
export MKLLIB="$MKLROOT/lib/intel64"
if ls "$MKLLIB"/libmkl_gf_lp64.* >/dev/null 2>&1; then
    export MKL_INTERFACE_LIB=mkl_gf_lp64
else
    export MKL_INTERFACE_LIB=mkl_intel_lp64
fi
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1

# Working directory
mkdir -p "$HOME/qe_build" && cd "$HOME/qe_build"
export BUILD_ROOT="$PWD"
export QE_ROOT="$BUILD_ROOT/q-e"
export QEPY_ROOT="$BUILD_ROOT/QEpy"
export VENV_NAME="${VENV_NAME:-venv_qepy}"
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"

# Clone sources
git clone --branch qe-7.2 --single-branch \
  https://gitlab.com/QEF/q-e.git "$QE_ROOT"
cd "$QE_ROOT" && git submodule update --init --recursive
cd "$BUILD_ROOT"
git clone https://github.com/Quantum-MultiScale/QEpy.git "$QEPY_ROOT"
cd "$QEPY_ROOT" && git checkout dev

# Python environment
cd "$BUILD_ROOT"
python3.11 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install \
  "numpy<2" "f90wrap==0.2.14" meson ninja packaging

# Configure QE
cd "$QE_ROOT"
./configure \
  CC="$CC" F77="$FC" F90="$FC" MPIF90=mpif90 \
  CFLAGS="-fPIC" \
  FFLAGS="-fPIC -fallow-argument-mismatch" \
  BLAS_LIBS="-L$MKLLIB -l$MKL_INTERFACE_LIB -lmkl_sequential -lmkl_core -lpthread -lm" \
  LAPACK_LIBS=""

# Edit make.inc:
#   toolset gcc/gfortran paths
#   CPP = gcc -E -P
#   -fPIC flags
#   FFTW from /usr/lib64
#   MKL BLAS/LAPACK with rpath
#   no OpenBLAS / -lblas / -llapack

make all

# Build QEpy
cd "$QEPY_ROOT"
rm -rf build dist qepy.egg-info
qedir="$QE_ROOT" python -m pip install --no-build-isolation --no-cache-dir -v .

# Test
cd /tmp
python -c "import qepy; import qepy.qepylibs; print(qepy.__file__)"
ldd "$QE_ROOT/bin/pw.x" | grep -i mkl
```

---

## Design choices

- **QE 7.2 is pinned** because this is the version verified with this QEpy build.
- **GCC toolset 14 is used** for GFortran to avoid GCC 15 / MBD conflicts while keeping a supported Fortran compiler on EL9.
- **Intel MPI + oneMKL** are the standard linear algebra and parallelism stack on Linux for this skill.
- **Sequential MKL** (`mkl_sequential`) avoids OpenMP-runtime conflicts with MPI during initial bring-up.
- **Homebrew FFTW** from EL9 is retained so FFT and BLAS/LAPACK changes can be validated independently.
- **LP64 MKL interface** matches QE's conventional Fortran BLAS/LAPACK calls; prefer `mkl_gf_lp64` with GFortran.
- **`make all` is required** because QEpy links components beyond `pw.x`.
- **For Open MPI + OpenBLAS on EL9**, use `qe72_qepy_rhel9_openblas_skill.md` (open-source fallback).
