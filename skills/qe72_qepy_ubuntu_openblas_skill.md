# Skill: Build Quantum ESPRESSO 7.2 and QEpy on Ubuntu with Open MPI and OpenBLAS

## Which skill to use

| Goal | Skill file |
|------|------------|
| **Ubuntu — Open MPI + OpenBLAS** (`apt`, no Intel installer) | `qe72_qepy_ubuntu_openblas_skill.md` (this file) |
| **Ubuntu — Intel MPI + oneMKL** | `qe72_qepy_ubuntu_intel_skill.md` |
| **RHEL 9 — Open MPI + OpenBLAS** | `qe72_qepy_rhel9_openblas_skill.md` |
| **RHEL 9 — Intel MPI + oneMKL** | `qe72_qepy_rhel9_intel_skill.md` |
| **macOS default** — Apple Accelerate | `qe72_qepy_macos_accelerate_skill.md` |
| **Intel Mac with oneMKL** | `qe72_qepy_macos_mkl_skill.md` |

Use **this skill** as the default Ubuntu path when you want an open-source stack from `apt`: **GCC/GFortran 14**, **Open MPI**, **OpenBLAS**, and **FFTW**.

If Intel oneAPI (Intel MPI + MKL) is installed or required, use `qe72_qepy_ubuntu_intel_skill.md` instead.

**Agent instruction:** on Ubuntu, ask whether Intel oneAPI is available. If yes and the user wants MKL/Intel MPI, switch to the Intel skill. Otherwise use this skill. Ask for the QEpy venv name (default `venv_qepy`).

---

## Purpose

This skill gives a reproducible, start-to-finish procedure for building:

- Quantum ESPRESSO tag `qe-7.2`
- QEpy compatible with QE 7.2
- a dedicated Python virtual environment (user-chosen name; default `venv_qepy`)
- GCC/GFortran 14
- Open MPI and FFTW from Ubuntu repositories
- OpenBLAS for BLAS and LAPACK

Tested layout targets **Ubuntu 24.04 LTS**. **Ubuntu 22.04 LTS** is supported with the compiler notes in section 3.

The Quantum ESPRESSO 7.2 release is tagged `qe-7.2` in the official QEF GitLab repository.

**Important:** use one compiler stack consistently for QE, Open MPI wrappers, and QEpy. Set `OMPI_CC` and `OMPI_FC` to the same `gcc` / `gfortran` used for the build.

---

# 1. Verify the system

```bash
lsb_release -a
uname -m
```

Expected:

```text
Ubuntu 24.04 LTS   # or 22.04 LTS
x86_64
```

On `aarch64`, package paths use `/usr/lib/aarch64-linux-gnu` instead of `x86_64-linux-gnu`.

---

# 2. Set library architecture path

```bash
export DEB_LIBDIR="/usr/lib/$(uname -m)-linux-gnu"
echo "DEB_LIBDIR=$DEB_LIBDIR"
ls "$DEB_LIBDIR"/libopenblas.so
```

---

# 3. Install prerequisites

Update package lists:

```bash
sudo apt update
```

## Ubuntu 24.04 LTS (recommended)

```bash
sudo apt install -y \
  git make wget curl gfortran-14 gcc-14 g++-14 \
  openmpi-bin libopenmpi-dev \
  libfftw3-dev \
  libopenblas-dev liblapack-dev \
  python3.12 python3.12-venv python3-pip
```

Set compiler variables:

```bash
export CC=gcc-14
export FC=gfortran-14
export F77="$FC"
export F90="$FC"
export CXX=g++-14
export PYTHON=python3.12
```

## Ubuntu 22.04 LTS

GCC 14 may be unavailable. Use GCC 12 from the default repositories:

```bash
sudo apt install -y \
  git make wget curl gfortran-12 gcc-12 g++-12 \
  openmpi-bin libopenmpi-dev \
  libfftw3-dev \
  libopenblas-dev liblapack-dev \
  python3.11 python3.11-venv python3-pip
```

```bash
export CC=gcc-12
export FC=gfortran-12
export F77="$FC"
export F90="$FC"
export CXX=g++-12
export PYTHON=python3.11
```

Do not build QE 7.2 with GCC 15 because of the bundled MBD `f_c_string` conflict. Prefer GCC 14; GCC 12 is an acceptable fallback on 22.04.

Verify:

```bash
"$CC" --version
"$FC" --version
which mpif90
mpif90 --showme:command
ls /usr/include/fftw3.f03
ls "$DEB_LIBDIR"/libopenblas.so
"$PYTHON" --version
```

---

# 4. Load the compiler and MPI environment

Point Open MPI at the selected GNU compilers:

```bash
export OMPI_CC="$CC"
export OMPI_FC="$FC"
export PATH="/usr/bin:$PATH"
```

Verify the MPI wrapper uses the intended Fortran compiler:

```bash
mpif90 --showme:command
```

If it reports `/usr/bin/gfortran` instead of `gfortran-14` (or `gfortran-12`), ensure `update-alternatives` or explicit `OMPI_FC` is set and retry in a fresh shell.

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

## Create

```bash
cd "$BUILD_ROOT"
"$PYTHON" -m venv "$VENV_DIR"
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
    *) echo "FAIL: Python $ver (need 3.10–3.12)"; fail=1 ;;
  esac

  local py_arch gcc_arch
  py_arch="$(file -b "$py" | awk -F', ' '/ELF/ {print $2; exit}' | awk '{print $1}')"
  gcc_arch="$(file -b "$(command -v "$CC")" | awk -F', ' '/ELF/ {print $2; exit}' | awk '{print $1}')"
  if [ -n "$py_arch" ] && [ -n "$gcc_arch" ] && [ "$py_arch" != "$gcc_arch" ]; then
    echo "FAIL: Python arch $py_arch != compiler arch $gcc_arch"
    fail=1
  else
    echo "OK: architecture check passed"
  fi

  return $fail
}

check_qepy_venv || exit 1
```

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

---

# 9. Configure Quantum ESPRESSO

Reassert environment:

```bash
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
  BLAS_LIBS="-L$DEB_LIBDIR -lopenblas" \
  LAPACK_LIBS="-L$DEB_LIBDIR -lopenblas"
```

---

# 10. Required `make.inc` corrections

Use the compiler names you selected (`gcc-14` / `gfortran-14` or `gcc-12` / `gfortran-12`):

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

IFLAGS = -I. -I$(TOPDIR)/include -I/usr/include
FFT_LIBS = -L/usr/lib/x86_64-linux-gnu -lfftw3

BLAS_LIBS  = -L/usr/lib/x86_64-linux-gnu -lopenblas
LAPACK_LIBS = -L/usr/lib/x86_64-linux-gnu -lopenblas

LDFLAGS =
```

On `aarch64`, replace `x86_64-linux-gnu` with `aarch64-linux-gnu` or use `$(DEB_LIBDIR)` when editing manually.

Remove if present:

```text
-lblas
-llapack
-framework Accelerate
-lmkl_
```

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

export OMPI_CC="$CC"
export OMPI_FC="$FC"

cd "$QEPY_ROOT"
rm -rf build dist qepy.egg-info

qedir="$QE_ROOT" \
python -m pip install \
  --no-build-isolation \
  --no-cache-dir \
  -v .
```

---

# 13. Test QEpy

```bash
cd /tmp
python -c "import qepy; import qepy.qepylibs; print(qepy.__file__)"
```

---

# 14. Troubleshooting

## `gcc-14` not found on Ubuntu 22.04

Use GCC 12 as in section 3, or upgrade to Ubuntu 24.04.

## MPI wrapper uses wrong compiler

```bash
export OMPI_CC="$CC"
export OMPI_FC="$FC"
mpif90 --showme:command
```

Rebuild QE from clean objects if the wrong compiler was used.

## Wrong BLAS linked

```bash
grep -E '^(BLAS_LIBS|LAPACK_LIBS)' "$QE_ROOT/make.inc"
ldd "$QE_ROOT/bin/pw.x" | grep -E 'openblas|mkl|blas'
```

For OpenBLAS, expect `libopenblas.so`. For MKL, use `qe72_qepy_ubuntu_intel_skill.md`.

## `fftw3.f03` missing

```bash
sudo apt install libfftw3-dev
```

## `laxlib.h` preprocessing failure

Ensure:

```make
CC  = gcc-14
CPP = gcc-14 -E -P
```

## Need Intel MKL or Intel MPI

Use `qe72_qepy_ubuntu_intel_skill.md`.

---

# 15. Condensed full procedure (Ubuntu 24.04)

```bash
export DEB_LIBDIR="/usr/lib/$(uname -m)-linux-gnu"

sudo apt update
sudo apt install -y \
  git make wget curl gfortran-14 gcc-14 g++-14 \
  openmpi-bin libopenmpi-dev libfftw3-dev libopenblas-dev \
  python3.12 python3.12-venv python3-pip

export CC=gcc-14 FC=gfortran-14 F77="$FC" F90="$FC"
export OMPI_CC="$CC" OMPI_FC="$FC"
export PYTHON=python3.12

mkdir -p "$HOME/qe_build" && cd "$HOME/qe_build"
export BUILD_ROOT="$PWD" QE_ROOT="$PWD/q-e" QEPY_ROOT="$PWD/QEpy"
export VENV_NAME="${VENV_NAME:-venv_qepy}" VENV_DIR="$BUILD_ROOT/$VENV_NAME"

# clone QE + QEpy; create venv; pip install deps (sections 6–8)

cd "$QE_ROOT"
./configure CC="$CC" F77="$FC" F90="$FC" MPIF90=mpif90 \
  CFLAGS="-fPIC" FFLAGS="-fPIC -fallow-argument-mismatch" \
  BLAS_LIBS="-L$DEB_LIBDIR -lopenblas" LAPACK_LIBS="-L$DEB_LIBDIR -lopenblas"
# fix make.inc (section 10)
make all

cd "$QEPY_ROOT"
qedir="$QE_ROOT" python -m pip install --no-build-isolation --no-cache-dir -v .
```

---

## Design choices

- **Ubuntu 24.04 LTS** is the primary target; **22.04** uses GCC 12 when GCC 14 is unavailable.
- **OpenBLAS** from `libopenblas-dev` provides BLAS and LAPACK.
- **Open MPI** from `libopenmpi-dev` is the default MPI.
- **For Intel MPI + MKL**, use `qe72_qepy_ubuntu_intel_skill.md`.
