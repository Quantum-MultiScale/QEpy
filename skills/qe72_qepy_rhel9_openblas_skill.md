# Skill: Build Quantum ESPRESSO 7.2 and QEpy on RHEL 9 with Open MPI and OpenBLAS

## Which skill to use

| Goal | Skill file |
|------|------------|
| **Ubuntu — Intel MPI + oneMKL** (Linux default) | `qe72_qepy_ubuntu_intel_skill.md` |
| **RHEL 9 — Intel MPI + oneMKL** (Linux default) | `qe72_qepy_rhel9_intel_skill.md` |
| **Ubuntu — Open MPI + OpenBLAS** (open-source alternative) | `qe72_qepy_ubuntu_openblas_skill.md` |
| **RHEL 9 — Open MPI + OpenBLAS** (open-source alternative) | `qe72_qepy_rhel9_openblas_skill.md` (this file) |
| **macOS default** — Apple Accelerate | `qe72_qepy_macos_accelerate_skill.md` |
| **Intel Mac with oneMKL** — archived Intel oneAPI 2023.x | `qe72_qepy_macos_mkl_skill.md` |

Use **this skill** as an **open-source alternative** when Intel oneAPI is unavailable or the user explicitly wants a fully open-source stack from EL9 repositories: **gcc-toolset-14**, **Open MPI**, **OpenBLAS**, and **FFTW**. No Intel oneAPI installation is required.

For the standard Linux stack (Intel MPI + oneMKL), use `qe72_qepy_rhel9_intel_skill.md`.

**Agent instruction:** use this skill only when Intel oneAPI is **not** present or the user prefers open-source packages. Otherwise use the Intel RHEL skill. Ask for the QEpy venv name (default `venv_qepy`).

---

## Purpose

This skill gives a reproducible, start-to-finish procedure for building:

- Quantum ESPRESSO tag `qe-7.2`
- QEpy compatible with QE 7.2
- a dedicated Python 3.11 virtual environment (user-chosen name; default `venv_qepy`)
- GCC/GFortran 14 from `gcc-toolset-14`
- Open MPI and FFTW from EL9 repositories
- OpenBLAS for BLAS and LAPACK

Supported distributions: RHEL 9, Rocky Linux 9, AlmaLinux 9, and other EL9 variants.

The Quantum ESPRESSO 7.2 release is tagged `qe-7.2` in the official QEF GitLab repository.

**Important:** use one compiler stack consistently for QE, Open MPI wrappers, and QEpy. After enabling `gcc-toolset-14`, keep its `bin` directory first in `PATH` and set `OMPI_CC` / `OMPI_FC`.

---

# 1. Verify the system

```bash
cat /etc/redhat-release
uname -m
```

Expected:

```text
Red Hat Enterprise Linux release 9.x   # or Rocky/Alma 9.x
x86_64
```

Adapt package names on `aarch64` if needed.

---

# 2. Enable required repositories

`openblas-devel` requires CodeReady Builder (CRB) on RHEL 9.

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

# 3. Install prerequisites

```bash
sudo dnf install -y \
  git make wget which \
  gcc-toolset-14 \
  gcc-toolset-14-gcc \
  gcc-toolset-14-gcc-gfortran \
  gcc-toolset-14-gcc-c++ \
  openmpi \
  openmpi-devel \
  fftw-devel \
  openblas-devel \
  lapack-devel \
  python3.11 \
  python3.11-devel \
  python3.11-pip
```

Verify:

```bash
rpm -q gcc-toolset-14-gcc-gfortran openmpi-devel fftw-devel openblas-devel python3.11
ls /usr/include/fftw3.f03
ls /usr/lib64/libopenblas.so
```

---

# 4. Load the compiler and MPI environment

```bash
source /opt/rh/gcc-toolset-14/enable

export GCC_ROOT="/opt/rh/gcc-toolset-14/root/usr"
export CC="$GCC_ROOT/bin/gcc"
export FC="$GCC_ROOT/bin/gfortran"
export F77="$FC"
export F90="$FC"
export CXX="$GCC_ROOT/bin/g++"

export PATH="$GCC_ROOT/bin:/usr/lib64/openmpi/bin:$PATH"

export OMPI_CC="$CC"
export OMPI_FC="$FC"
```

Verify:

```bash
"$CC" --version
"$FC" --version
which mpif90
mpif90 --showme:command
file "$CC" "$FC" "$(which mpif90)"
```

Expected:

- `gcc` / `gfortran` report version 14.x from the toolset
- `mpif90` resolves to `/usr/lib64/openmpi/bin/mpif90` or similar
- the MPI wrapper invokes toolset `gfortran`, not `/usr/bin/gfortran`

If the wrapper still uses the stock compiler:

```bash
export PATH="/opt/rh/gcc-toolset-14/root/usr/bin:/usr/lib64/openmpi/bin:$PATH"
export OMPI_CC=/opt/rh/gcc-toolset-14/root/usr/bin/gcc
export OMPI_FC=/opt/rh/gcc-toolset-14/root/usr/bin/gfortran
```

Do not mix GCC toolset 14 with GCC 15 module files.

---

# 5. Create a clean working directory

```bash
mkdir -p "$HOME/qe_build"
cd "$HOME/qe_build"
```

```bash
export BUILD_ROOT="$PWD"
export QE_ROOT="$BUILD_ROOT/q-e"
export QEPY_ROOT="$BUILD_ROOT/QEpy"
export VENV_NAME="${VENV_NAME:-venv_qepy}"
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"
echo "QEpy virtual environment: $VENV_DIR"
```

---

# 6. Clone Quantum ESPRESSO 7.2

```bash
git clone \
  --branch qe-7.2 \
  --single-branch \
  https://gitlab.com/QEF/q-e.git \
  "$QE_ROOT"

cd "$QE_ROOT"
git submodule update --init --recursive
git describe --tags --exact-match
```

---

# 7. Clone QEpy

```bash
cd "$BUILD_ROOT"
git clone https://github.com/shaoxc/qepy.git "$QEPY_ROOT"
cd "$QEPY_ROOT"
git checkout dev
```

---

# 8. Create or verify the Python environment

```bash
source /opt/rh/gcc-toolset-14/enable
export GCC_ROOT="/opt/rh/gcc-toolset-14/root/usr"
export CC="$GCC_ROOT/bin/gcc"
```

## Create

```bash
cd "$BUILD_ROOT"
python3.11 -m venv "$VENV_DIR"
```

## Compatibility checks

```bash
check_qepy_venv() {
  local fail=0
  local py="$VENV_DIR/bin/python"

  [ -x "$py" ] || { echo "FAIL: $py missing"; return 1; }

  local ver
  ver="$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  case "$ver" in
    3.10|3.11|3.12) echo "OK: Python $ver" ;;
    *) echo "FAIL: Python $ver"; fail=1 ;;
  esac

  local py_arch gcc_arch
  py_arch="$(file -b "$py" | awk -F': ' '/architecture/ {print $2; exit}')"
  gcc_arch="$(file -b "$CC" | awk -F': ' '/architecture/ {print $2; exit}')"
  [ "$py_arch" = "$gcc_arch" ] || { echo "FAIL: arch mismatch"; fail=1; }

  return $fail
}

check_qepy_venv
```

```bash
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install \
  "numpy<2" "f90wrap==0.2.14" meson ninja packaging
```

---

# 9. Configure Quantum ESPRESSO

Reload environment:

```bash
source /opt/rh/gcc-toolset-14/enable
export GCC_ROOT="/opt/rh/gcc-toolset-14/root/usr"
export CC="$GCC_ROOT/bin/gcc"
export FC="$GCC_ROOT/bin/gfortran"
export PATH="$GCC_ROOT/bin:/usr/lib64/openmpi/bin:$PATH"
export OMPI_CC="$CC"
export OMPI_FC="$FC"
```

```bash
cd "$QE_ROOT"

./configure \
  CC="$CC" \
  F77="$FC" \
  F90="$FC" \
  MPIF90=mpif90 \
  CFLAGS="-fPIC" \
  FFLAGS="-fPIC -fallow-argument-mismatch" \
  BLAS_LIBS="-L/usr/lib64 -lopenblas" \
  LAPACK_LIBS="-L/usr/lib64 -lopenblas"
```

---

# 10. Required `make.inc` corrections

```make
F90     = /opt/rh/gcc-toolset-14/root/usr/bin/gfortran
MPIF90  = mpif90
CC      = /opt/rh/gcc-toolset-14/root/usr/bin/gcc
CPP     = /opt/rh/gcc-toolset-14/root/usr/bin/gcc -E -P

CPPFLAGS = $(DFLAGS) $(IFLAGS)

CFLAGS = -fPIC $(DFLAGS) $(IFLAGS) $(CUDA_CFLAGS)
FFLAGS = -fPIC -fallow-argument-mismatch
F90FLAGS = $(FFLAGS) -cpp $(FDFLAGS) \
           $(CUDA_F90FLAGS) $(IFLAGS) $(MODFLAGS)

IFLAGS = -I. -I$(TOPDIR)/include -I/usr/include
FFT_LIBS = -L/usr/lib64 -lfftw3

BLAS_LIBS  = -L/usr/lib64 -lopenblas
LAPACK_LIBS = -L/usr/lib64 -lopenblas

LDFLAGS =
```

Remove if present:

```text
-lblas
-llapack
-framework Accelerate
-lmkl_
```

Do not combine OpenBLAS with MKL or generic reference BLAS in the same build.

---

# 11. Build all of Quantum ESPRESSO

```bash
cd "$QE_ROOT"
make clean || true
find . -name '*.o' -delete
find . -name '*.mod' -delete
find . -name '*.a' -delete
make all
```

Verify:

```bash
find "$QE_ROOT/atomic" -name 'ld1inc.mod'
ls "$QE_ROOT/GWW/minpack/dpmpar.o"
"$QE_ROOT/bin/pw.x" < /dev/null 2>&1 | head -5
ldd "$QE_ROOT/bin/pw.x" | grep openblas
```

---

# 12. Build QEpy

```bash
source "$VENV_DIR/bin/activate"
check_qepy_venv

source /opt/rh/gcc-toolset-14/enable
export GCC_ROOT="/opt/rh/gcc-toolset-14/root/usr"
export CC="$GCC_ROOT/bin/gcc"
export FC="$GCC_ROOT/bin/gfortran"
export PATH="$GCC_ROOT/bin:/usr/lib64/openmpi/bin:$PATH"
export OMPI_CC="$CC"
export OMPI_FC="$FC"

cd "$QEPY_ROOT"
rm -rf build dist qepy.egg-info

qedir="$QE_ROOT" \
python -m pip install --no-build-isolation --no-cache-dir -v .
```

---

# 13. Test QEpy

```bash
cd /tmp
python -c "import qepy; import qepy.qepylibs; print(qepy.__file__)"
```

---

# 14. HPC clusters with environment modules

```bash
module load gcc-toolset/14
module load openmpi/4.x
```

Confirm `mpif90 --showme:command` matches the loaded GFortran. If the site provides Intel oneAPI instead, switch to `qe72_qepy_rhel9_intel_skill.md`.

---

# 15. Troubleshooting

## `openblas-devel` not found

Enable CRB (section 2), then retry `dnf install openblas-devel`.

## MPI wrapper uses wrong compiler

```bash
export PATH="/opt/rh/gcc-toolset-14/root/usr/bin:/usr/lib64/openmpi/bin:$PATH"
export OMPI_CC=/opt/rh/gcc-toolset-14/root/usr/bin/gcc
export OMPI_FC=/opt/rh/gcc-toolset-14/root/usr/bin/gfortran
```

## Wrong BLAS linked

```bash
grep -E '^(BLAS_LIBS|LAPACK_LIBS)' "$QE_ROOT/make.inc"
ldd "$QE_ROOT/bin/pw.x" | grep -E 'openblas|mkl|blas'
```

For OpenBLAS, expect `libopenblas.so`. If you need MKL, use the Intel skill instead — do not mix.

## Need Intel MKL or Intel MPI

Use `qe72_qepy_rhel9_intel_skill.md`. Do not install both stacks into the same `make.inc`.

Other issues (`fftw3.f03`, `laxlib.h`, GCC 15 MBD, missing `ld1inc.mod`, QEpy Meson): same fixes as in the Intel skill, substituting Open MPI paths for Intel MPI.

---

# 16. Condensed full procedure

```bash
sudo subscription-manager repos \
  --enable codeready-builder-for-rhel-9-$(uname -m)-rpms
sudo dnf install -y \
  git make wget which \
  gcc-toolset-14 gcc-toolset-14-gcc gcc-toolset-14-gcc-gfortran \
  openmpi openmpi-devel fftw-devel openblas-devel lapack-devel \
  python3.11 python3.11-devel python3.11-pip

source /opt/rh/gcc-toolset-14/enable
export GCC_ROOT="/opt/rh/gcc-toolset-14/root/usr"
export CC="$GCC_ROOT/bin/gcc"
export FC="$GCC_ROOT/bin/gfortran"
export PATH="$GCC_ROOT/bin:/usr/lib64/openmpi/bin:$PATH"
export OMPI_CC="$CC" OMPI_FC="$FC"

mkdir -p "$HOME/qe_build" && cd "$HOME/qe_build"
export BUILD_ROOT="$PWD" QE_ROOT="$PWD/q-e" QEPY_ROOT="$PWD/QEpy"
export VENV_NAME="${VENV_NAME:-venv_qepy}" VENV_DIR="$BUILD_ROOT/$VENV_NAME"

# clone QE, QEpy; create venv; pip install deps (see sections 6–8)

cd "$QE_ROOT"
./configure CC="$CC" F77="$FC" F90="$FC" MPIF90=mpif90 \
  CFLAGS="-fPIC" FFLAGS="-fPIC -fallow-argument-mismatch" \
  BLAS_LIBS="-L/usr/lib64 -lopenblas" LAPACK_LIBS="-L/usr/lib64 -lopenblas"
# fix make.inc (section 10)
make all

cd "$QEPY_ROOT"
qedir="$QE_ROOT" python -m pip install --no-build-isolation --no-cache-dir -v .
```

---

## Design choices

- **Open-source fallback** — use when Intel oneAPI is unavailable or not desired.
- **OpenBLAS** provides both BLAS and LAPACK via `/usr/lib64/libopenblas.so`.
- **Open MPI** from EL9 is the MPI implementation for this skill.
- **GCC toolset 14** avoids GCC 15 / QE 7.2 MBD conflicts.
- **Standard Linux stack (Intel MPI + MKL):** use `qe72_qepy_rhel9_intel_skill.md`.
