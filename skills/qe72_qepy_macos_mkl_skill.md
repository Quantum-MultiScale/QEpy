# Skill: Build Quantum ESPRESSO 7.2 and QEpy with Intel oneMKL on Intel macOS

## Which skill to use

| Goal | Skill file |
|------|------------|
| **Default macOS build** — Apple Accelerate for BLAS/LAPACK | `qe72_qepy_macos_accelerate_skill.md` |
| **Intel Mac with oneMKL** — archived Intel oneAPI 2023.x | `qe72_qepy_macos_mkl_skill.md` (this file) |
| **Ubuntu — Intel MPI + oneMKL** (Linux default) | `qe72_qepy_ubuntu_intel_skill.md` |
| **RHEL 9 — Intel MPI + oneMKL** (Linux default) | `qe72_qepy_rhel9_intel_skill.md` |
| **Ubuntu — Open MPI + OpenBLAS** (open-source alternative) | `qe72_qepy_ubuntu_openblas_skill.md` |
| **RHEL 9 — Open MPI + OpenBLAS** (open-source alternative) | `qe72_qepy_rhel9_openblas_skill.md` |

Use **this skill** only when you need Intel oneMKL on an Intel Mac (`x86_64`). For Apple Silicon or for the default macOS setup, use the Accelerate skill instead.

---

## Purpose

This procedure builds a reproducible Intel-macOS installation of:

- Quantum ESPRESSO tag `qe-7.2`
- QEpy from its `dev` branch
- Intel oneMKL for BLAS and LAPACK
- Homebrew FFTW
- GCC/GFortran 14
- Open MPI
- a dedicated Python 3.10 virtual environment (user-chosen name; default `venv_qepy`)

It is intended for an Intel Mac or an Apple Silicon Mac running the build under Rosetta with x86_64 Homebrew:

```bash
uname -m
```

Expected output:

```text
x86_64
```

Do not use this procedure for a native **arm64** QE build. Intel oneMKL for macOS supports Intel 64 only, and Intel discontinued macOS support beginning with oneAPI 2024.0. Use the last macOS-supported 2023.x oneAPI/oneMKL release.

**Agent instruction:** before creating or reusing a virtual environment, ask the user what name they want for the QEpy Python environment. If they have no preference, use `venv_qepy`.

**Important:** use one Homebrew prefix consistently for the entire build. On Intel Macs this is normally `/usr/local`.

---

# 1. Verify platform and Homebrew

Confirm you are building for `x86_64`:

```bash
uname -m
```

Load Intel/Rosetta Homebrew:

```bash
eval "$(/usr/local/bin/brew shellenv)"
export HOMEBREW_PREFIX="$(brew --prefix)"
export BREW_BIN="$HOMEBREW_PREFIX/bin"
export BREW_OPT="$HOMEBREW_PREFIX/opt"
```

Verify:

```bash
echo "HOMEBREW_PREFIX=$HOMEBREW_PREFIX"
file "$BREW_BIN/gcc-14" "$BREW_BIN/gfortran-14" "$BREW_BIN/mpif90"
"$BREW_BIN/gcc-14" -dumpmachine
```

Expected:

```text
HOMEBREW_PREFIX=/usr/local
x86_64-apple-darwin*
```

If `gcc-14` is `arm64`, you are on the wrong Homebrew. Use `/usr/local/bin/brew`, not `/opt/homebrew` or `~/homebrew`. For native arm64 builds with Apple Accelerate, switch to `qe72_qepy_macos_accelerate_skill.md`.

Install Apple command-line tools if needed:

```bash
xcode-select --install
```

Install build dependencies:

```bash
brew install git python@3.10 gcc@14 open-mpi fftw make
```

---

# 2. Obtain Intel oneMKL for macOS

Intel oneAPI 2024.0 and newer do not support macOS. Obtain a macOS installer for the 2023.x Intel oneAPI Base Toolkit or the standalone Intel oneMKL component from Intel's archived oneAPI downloads.

Recommended release:

```text
Intel oneAPI 2023.2 for macOS, Intel 64
```

The oneAPI Base Toolkit includes oneMKL.

Intel may require signing into an Intel account before downloading an archived installer. Choose the macOS Intel-64 offline or online installer, not a Linux or Apple-Silicon package.

Typical downloaded installer names resemble:

```text
m_BaseKit_p_2023.2.x.dmg
```

or a standalone oneMKL component installer for macOS.

---

# 3. Install oneMKL

## GUI installation

Mount the downloaded DMG:

```bash
open ~/Downloads/m_BaseKit_p_2023.2*.dmg
```

Run the installer and include Intel oneAPI Math Kernel Library.

The default installation root is normally:

```text
/opt/intel/oneapi
```

## Command-line installation

After mounting the DMG, inspect the mounted volume:

```bash
ls /Volumes
```

Locate the installer:

```bash
find /Volumes -maxdepth 3 -type f \
  \( -name 'install.sh' -o -name 'bootstrapper' -o -name 'm_*Kit*.sh' \) \
  2>/dev/null
```

Follow the command-line options shown by the installer itself:

```bash
/path/to/installer --help
```

Because exact archived-installer filenames vary, do not hard-code a filename that has not been verified on the downloaded image.

---

# 4. Initialize and locate oneMKL

If the oneAPI environment setup script exists, source it:

```bash
if [ -f /opt/intel/oneapi/setvars.sh ]; then
    source /opt/intel/oneapi/setvars.sh
fi
```

Check whether `MKLROOT` was set:

```bash
echo "$MKLROOT"
```

If it was not set, locate the installation:

```bash
find /opt/intel/oneapi -type f -name 'libmkl_core.dylib' 2>/dev/null
```

Set `MKLROOT` to the directory containing `include/` and `lib/`.

A common result is:

```bash
export MKLROOT=/opt/intel/oneapi/mkl/2023.2.0
```

Some installations provide a `latest` symlink:

```bash
export MKLROOT=/opt/intel/oneapi/mkl/latest
```

Verify:

```bash
test -f "$MKLROOT/include/mkl.h"
find "$MKLROOT/lib" -name 'libmkl_core.dylib'
```

Set the library directory:

```bash
if [ -d "$MKLROOT/lib/intel64" ]; then
    export MKLLIB="$MKLROOT/lib/intel64"
else
    export MKLLIB="$MKLROOT/lib"
fi
```

Confirm:

```bash
echo "$MKLROOT"
echo "$MKLLIB"
ls "$MKLLIB"/libmkl_core.*
```

---

# 5. Select the oneMKL interface library

Quantum ESPRESSO uses the conventional LP64 BLAS/LAPACK integer interface.

Inspect the installed MKL interface libraries:

```bash
ls "$MKLLIB"/libmkl_*lp64* 2>/dev/null
```

Select the GNU Fortran interface if the package contains it:

```bash
if ls "$MKLLIB"/libmkl_gf_lp64.* >/dev/null 2>&1; then
    export MKL_INTERFACE_LIB=mkl_gf_lp64
elif ls "$MKLLIB"/libmkl_intel_lp64.* >/dev/null 2>&1; then
    export MKL_INTERFACE_LIB=mkl_intel_lp64
else
    echo "No LP64 oneMKL interface library found in $MKLLIB"
    return 1 2>/dev/null || exit 1
fi
```

Display the selection:

```bash
echo "$MKL_INTERFACE_LIB"
```

Older macOS oneMKL packages often provide `libmkl_intel_lp64`; some distributions may also provide `libmkl_gf_lp64`. QE calls the traditional Fortran BLAS/LAPACK interfaces and does not require the oneMKL Fortran 95 module libraries.

Use the sequential threading layer initially:

```text
mkl_sequential
```

This avoids OpenMP-runtime conflicts and MPI/OpenMP oversubscription.

---

# 6. Create a clean working directory

Choose a parent directory:

```bash
mkdir -p "$HOME/Documents/QEPy_on_mac"
cd "$HOME/Documents/QEPy_on_mac"
```

Define paths:

```bash
export BUILD_ROOT="$PWD"
export QE_ROOT="$BUILD_ROOT/q-e"
export QEPY_ROOT="$BUILD_ROOT/QEpy"
```

**Ask the user** which name to use for the QEpy Python virtual environment. If they have no preference, use the default:

```text
venv_qepy
```

Record the choice:

```bash
export VENV_NAME="${VENV_NAME:-venv_qepy}"
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"
echo "QEpy virtual environment: $VENV_DIR"
```

Use a distinct build directory name when comparing with Accelerate builds, for example:

```text
qe_mkl/    # this MKL build
```

---

# 7. Clone Quantum ESPRESSO 7.2

Clone the exact official tag:

```bash
git clone \
  --branch qe-7.2 \
  --single-branch \
  https://gitlab.com/QEF/q-e.git \
  "$QE_ROOT"
```

Initialize submodules:

```bash
cd "$QE_ROOT"
git submodule update --init --recursive
```

Verify the release:

```bash
git describe --tags --exact-match
```

Expected:

```text
qe-7.2
```

Record the exact commit:

```bash
git rev-parse HEAD
```

---

# 8. Clone QEpy

Clone QEpy:

```bash
cd "$BUILD_ROOT"
git clone https://github.com/Quantum-MultiScale/QEpy.git "$QEPY_ROOT"
```

Use the branch tested with this procedure:

```bash
cd "$QEPY_ROOT"
git checkout dev
```

Record the exact commit for reproducibility:

```bash
git rev-parse HEAD
```

For a long-lived deployment, save that hash and later replace `git checkout dev` with:

```bash
git checkout <recorded-commit>
```

---

# 9. Create or verify the Python environment

Ensure Intel Homebrew is active:

```bash
eval "$(/usr/local/bin/brew shellenv)"
export HOMEBREW_PREFIX="$(brew --prefix)"
export BREW_BIN="$HOMEBREW_PREFIX/bin"
export BREW_OPT="$HOMEBREW_PREFIX/opt"
```

## Create a new environment

If `$VENV_DIR` does not exist yet:

```bash
cd "$BUILD_ROOT"
"$BREW_OPT/python@3.10/bin/python3.10" -m venv "$VENV_DIR"
```

## Reuse an existing environment

If `$VENV_DIR` already exists, run the compatibility checks below before proceeding.

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
  if [ "$ver" != "3.10" ]; then
    echo "FAIL: Python $ver (need 3.10)"
    fail=1
  else
    echo "OK: Python $ver"
  fi

  local py_arch gcc_arch
  py_arch="$(file -b "$py" | awk -F': ' '/architecture/ {print $2; exit}')"
  gcc_arch="$(file -b "$BREW_BIN/gcc-14" | awk -F': ' '/architecture/ {print $2; exit}')"
  if [ "$py_arch" != "$gcc_arch" ]; then
    echo "FAIL: Python is $py_arch but gcc-14 is $gcc_arch"
    fail=1
  else
    echo "OK: Python architecture $py_arch matches toolchain"
  fi

  if ! "$py" -c "import sys; sys.exit(0 if sys.executable.startswith('$HOMEBREW_PREFIX') else 1)"; then
    echo "WARN: Python is not from $HOMEBREW_PREFIX"
  else
    echo "OK: Python from $HOMEBREW_PREFIX"
  fi

  return $fail
}

check_qepy_venv || {
  echo "Virtual environment is not compatible with this build." >&2
  exit 1
}
```

Activate the environment:

```bash
source "$VENV_DIR/bin/activate"
```

Install build dependencies:

```bash
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

# 10. Configure a consistent compiler stack

Set GCC/GFortran 14 from Homebrew:

```bash
export CC="$BREW_BIN/gcc-14"
export FC="$BREW_BIN/gfortran-14"
export F77="$FC"
export F90="$FC"
export PATH="$BREW_BIN:$PATH"
```

Force Open MPI to use the same compilers:

```bash
export OMPI_CC="$CC"
export OMPI_FC="$FC"
```

Verify:

```bash
"$CC" --version
"$FC" --version
"$BREW_BIN/mpif90" --showme:command
```

Do not mix GFortran 14 and GFortran 15 object or module files.

---

# 11. Configure Quantum ESPRESSO

Enter the QE repository:

```bash
cd "$QE_ROOT"
```

Run configure:

```bash
./configure \
  CC="$CC" \
  F77="$FC" \
  F90="$FC" \
  MPIF90="$BREW_BIN/mpif90" \
  CFLAGS="-fPIC" \
  FFLAGS="-fPIC -fallow-argument-mismatch" \
  BLAS_LIBS="-L$MKLLIB -l$MKL_INTERFACE_LIB -lmkl_sequential -lmkl_core -lpthread -lm" \
  LAPACK_LIBS=""
```

The configure step creates `make.inc`.

---

# 12. Correct and verify `make.inc`

Open:

```bash
nano "$QE_ROOT/make.inc"
```

Ensure that the compiler definitions are:

```make
F90     = /usr/local/bin/gfortran-14
MPIF90  = /usr/local/bin/mpif90
CC      = /usr/local/bin/gcc-14
CPP     = /usr/local/bin/gcc-14 -E -P
```

Adjust paths if `HOMEBREW_PREFIX` is not `/usr/local`.

Never place `-E -P` in `CC`.

Use:

```make
CPPFLAGS = $(DFLAGS) $(IFLAGS)
LDFLAGS  = -L$(MKLLIB) -Wl,-rpath,$(MKLLIB)
```

Ensure position-independent code:

```make
CFLAGS = -fPIC $(DFLAGS) $(IFLAGS) $(CUDA_CFLAGS)

FFLAGS = -fPIC -fallow-argument-mismatch

F90FLAGS = $(FFLAGS) -cpp $(FDFLAGS) \
           $(CUDA_F90FLAGS) $(IFLAGS) $(MODFLAGS)
```

Use Homebrew FFTW and MKL headers:

```make
IFLAGS = -I. -I$(TOPDIR)/include \
         -I/usr/local/opt/fftw/include \
         -I/opt/intel/oneapi/mkl/latest/include
```

If `MKLROOT` is versioned rather than `latest`, insert that exact path.

Keep FFTW separate from MKL:

```make
FFT_LIBS = -L/usr/local/opt/fftw/lib -lfftw3
```

Replace the system BLAS/LAPACK definitions completely.

Example using `mkl_intel_lp64`:

```make
MKLROOT = /opt/intel/oneapi/mkl/latest
MKLLIB  = $(MKLROOT)/lib/intel64

BLAS_LIBS = -L$(MKLLIB) \
            -lmkl_intel_lp64 \
            -lmkl_sequential \
            -lmkl_core \
            -lpthread -lm

LAPACK_LIBS =
```

If `libmkl_gf_lp64.dylib` exists and was selected, use `-lmkl_gf_lp64` instead of `-lmkl_intel_lp64`.

Do not retain:

```make
-lblas
-llapack
-framework Accelerate
```

in `BLAS_LIBS` or `LAPACK_LIBS`, because they may cause the system libraries to resolve symbols before MKL.

Remove unnecessary LLVM paths unless another component explicitly needs them:

```make
-I/usr/local/opt/llvm/include
-L/usr/local/opt/llvm/lib
```

Check FFTW Fortran interface:

```bash
ls "$BREW_OPT/fftw/include/fftw3.f03"
```

---

# 13. Verify the MKL link line before building QE

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

Expected numerical result:

```text
11.0000000000000
```

Confirm dynamic linkage:

```bash
otool -L /tmp/test_mkl | grep -i mkl
```

Do not continue until this test succeeds.

---

# 14. Build all Quantum ESPRESSO components

For a fresh clone:

```bash
cd "$QE_ROOT"
make all
```

For a rebuild after changing BLAS/LAPACK:

```bash
cd "$QE_ROOT"

make clean || true
find . -name '*.o' -delete
find . -name '*.mod' -delete
find . -name '*.a' -delete

make all
```

Use `make all`, not only `make pw`.

QEpy needs objects and modules from:

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

Check required objects:

```bash
find "$QE_ROOT/atomic" -name 'ld1inc.mod'
ls "$QE_ROOT/GWW/minpack/dpmpar.o"
ls "$QE_ROOT/CPV/src/"*.o | head
```

---

# 15. Verify that Quantum ESPRESSO uses MKL

Inspect `pw.x`:

```bash
otool -L "$QE_ROOT/bin/pw.x" | grep -i mkl
file "$QE_ROOT/bin/pw.x"
```

You should see at least:

```text
libmkl_core.dylib
libmkl_sequential.dylib
libmkl_intel_lp64.dylib
```

or:

```text
libmkl_gf_lp64.dylib
```

depending on the installed interface library.

Check that the system BLAS was not linked:

```bash
otool -L "$QE_ROOT/bin/pw.x" | \
  grep -E 'Accelerate|libblas|liblapack'
```

Ideally this returns no output.

Test the executable:

```bash
"$QE_ROOT/bin/pw.x" < /dev/null 2>&1 | head -5
```

---

# 16. Configure oneMKL runtime behavior

For a sequential MKL build, set:

```bash
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

This is appropriate when using MPI parallelism and avoids oversubscription.

You may add these to the activation workflow:

```bash
cat >> "$VENV_DIR/bin/activate" <<EOF

# QE/QEpy oneMKL runtime
export MKLROOT="$MKLROOT"
export MKLLIB="$MKLLIB"
export DYLD_LIBRARY_PATH="$MKLLIB:\${DYLD_LIBRARY_PATH:-}"
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export OMPI_CC=$BREW_BIN/gcc-14
export OMPI_FC=$BREW_BIN/gfortran-14
EOF
```

On current macOS releases, embedded `rpath` is preferable to relying only on `DYLD_LIBRARY_PATH`, but exporting it is useful during development and diagnostics.

---

# 17. Build and install QEpy

Activate the dedicated environment:

```bash
source "$VENV_DIR/bin/activate"
check_qepy_venv
```

Re-source oneAPI if needed:

```bash
if [ -f /opt/intel/oneapi/setvars.sh ]; then
    source /opt/intel/oneapi/setvars.sh
fi
```

Restore the compiler selection:

```bash
export CC="$BREW_BIN/gcc-14"
export FC="$BREW_BIN/gfortran-14"
export OMPI_CC="$CC"
export OMPI_FC="$FC"
export PATH="$BREW_BIN:$PATH"
```

Enter QEpy:

```bash
cd "$QEPY_ROOT"
```

Remove stale build products:

```bash
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

`--no-build-isolation` ensures that the build uses:

```text
f90wrap==0.2.14
meson
ninja
```

from the dedicated environment.

---

# 18. Test QEpy outside the source tree

Do not test from within the QEpy repository because the local source package can shadow the installed package.

Use:

```bash
cd /tmp
python -c "import qepy; print(qepy.__file__)"
```

The path should be inside:

```text
$VENV_DIR/lib/python3.10/site-packages/
```

Test the compiled extension libraries:

```bash
python -c \
  "import qepy; import qepy.qepylibs; print('QEpy import successful')"
```

---

# 19. Verify that QEpy loads MKL

Locate QEpy shared libraries:

```bash
QEPY_SITE="$(
python - <<'PY'
from pathlib import Path
import qepy
print(Path(qepy.__file__).resolve().parent)
PY
)"
```

Then:

```bash
find "$QEPY_SITE" -name '*.so' -print0 |
while IFS= read -r -d '' lib; do
    if otool -L "$lib" | grep -qi mkl; then
        echo "MKL linked: $lib"
        otool -L "$lib" | grep -i mkl
    fi
done
```

At least some of the QEpy shared libraries should show oneMKL dependencies.

---

# 20. Troubleshooting

## Wrong skill for this machine

If you are on Apple Silicon and want a native arm64 build, use `qe72_qepy_macos_accelerate_skill.md` with `/opt/homebrew` or `~/homebrew`. oneMKL is not available for native arm64 macOS.

## Incompatible Python virtual environment

Run `check_qepy_venv` from section 9. The venv must use Python 3.10 `x86_64` from `/usr/local` Homebrew.

## oneMKL cannot be downloaded for current macOS

Intel discontinued macOS support beginning with oneAPI 2024.0.

Use an archived 2023.x macOS Intel-64 installer. Do not download a current Linux-only oneAPI release and expect it to work on macOS.

## `MKLROOT` is empty

Source:

```bash
source /opt/intel/oneapi/setvars.sh
```

or set it manually to the versioned MKL directory.

## `ld: library not found for -lmkl_*`

Check:

```bash
echo "$MKLLIB"
ls "$MKLLIB"/libmkl_*
```

Correct `MKLLIB` to either `$MKLROOT/lib` or `$MKLROOT/lib/intel64`.

## `libmkl_gf_lp64` does not exist

Use the installed LP64 interface library:

```text
libmkl_intel_lp64
```

## Runtime cannot find `libmkl_core.dylib`

Ensure that `make.inc` contains:

```make
-Wl,-rpath,$(MKLLIB)
```

and temporarily export:

```bash
export DYLD_LIBRARY_PATH="$MKLLIB:${DYLD_LIBRARY_PATH:-}"
```

## QE still links Accelerate or system BLAS

Remove all of these from `make.inc`:

```text
-framework Accelerate
-lblas
-llapack
```

Clean all object and archive files and rebuild.

## GCC 15 MBD error involving `f_c_string`

Use GCC/GFortran 14 consistently for QE and QEpy.

## QEpy misses `dpmpar.o` or `ld1inc.mod`

Build the full QE suite:

```bash
cd "$QE_ROOT"
make all
```

## `import qepy` cannot find `qepy.__config__`

Test outside the source checkout:

```bash
cd /tmp
python -c "import qepy"
```

---

# 21. Condensed installation sequence

```bash
# Verify Intel / Rosetta x86_64
uname -m

eval "$(/usr/local/bin/brew shellenv)"
export HOMEBREW_PREFIX="$(brew --prefix)"
export BREW_BIN="$HOMEBREW_PREFIX/bin"
export BREW_OPT="$HOMEBREW_PREFIX/opt"

brew install git python@3.10 gcc@14 open-mpi fftw make

# Install archived Intel oneAPI Base Toolkit 2023.2 for macOS Intel 64
# using Intel's installer, then:

source /opt/intel/oneapi/setvars.sh

export MKLROOT="${MKLROOT:-/opt/intel/oneapi/mkl/latest}"

if [ -d "$MKLROOT/lib/intel64" ]; then
    export MKLLIB="$MKLROOT/lib/intel64"
else
    export MKLLIB="$MKLROOT/lib"
fi

if ls "$MKLLIB"/libmkl_gf_lp64.* >/dev/null 2>&1; then
    export MKL_INTERFACE_LIB=mkl_gf_lp64
else
    export MKL_INTERFACE_LIB=mkl_intel_lp64
fi

# Sources
mkdir -p "$HOME/Documents/QEPy_on_mac"
cd "$HOME/Documents/QEPy_on_mac"

export BUILD_ROOT="$PWD"
export QE_ROOT="$BUILD_ROOT/q-e"
export QEPY_ROOT="$BUILD_ROOT/QEpy"

export VENV_NAME="${VENV_NAME:-venv_qepy}"
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"

git clone \
  --branch qe-7.2 \
  --single-branch \
  https://gitlab.com/QEF/q-e.git \
  "$QE_ROOT"

cd "$QE_ROOT"
git submodule update --init --recursive

cd "$BUILD_ROOT"
git clone https://github.com/Quantum-MultiScale/QEpy.git "$QEPY_ROOT"

cd "$QEPY_ROOT"
git checkout dev

# Python environment
cd "$BUILD_ROOT"
if [ ! -d "$VENV_DIR" ]; then
  "$BREW_OPT/python@3.10/bin/python3.10" -m venv "$VENV_DIR"
fi

py="$VENV_DIR/bin/python"
ver="$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
py_arch="$(file -b "$py" | awk -F': ' '/architecture/ {print $2; exit}')"
gcc_arch="$(file -b "$BREW_BIN/gcc-14" | awk -F': ' '/architecture/ {print $2; exit}')"
[ "$ver" = "3.10" ] || { echo "Need Python 3.10" >&2; exit 1; }
[ "$py_arch" = "$gcc_arch" ] || { echo "Python ($py_arch) != gcc-14 ($gcc_arch)" >&2; exit 1; }

source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install \
  "numpy<2" \
  "f90wrap==0.2.14" \
  meson \
  ninja \
  packaging

# Compilers
export CC="$BREW_BIN/gcc-14"
export FC="$BREW_BIN/gfortran-14"
export F77="$FC"
export F90="$FC"
export OMPI_CC="$CC"
export OMPI_FC="$FC"
export PATH="$BREW_BIN:$PATH"

# Configure QE
cd "$QE_ROOT"

./configure \
  CC="$CC" \
  F77="$FC" \
  F90="$FC" \
  MPIF90="$BREW_BIN/mpif90" \
  CFLAGS="-fPIC" \
  FFLAGS="-fPIC -fallow-argument-mismatch" \
  BLAS_LIBS="-L$MKLLIB -l$MKL_INTERFACE_LIB -lmkl_sequential -lmkl_core -lpthread -lm" \
  LAPACK_LIBS=""

# Edit make.inc as described above:
# - GCC/GFortran 14 from $BREW_BIN
# - CPP = gcc-14 -E -P
# - -fPIC
# - Homebrew FFTW
# - MKL BLAS/LAPACK with rpath
# - no Accelerate, -lblas, or -llapack

# Build full QE
make all

# Verify MKL
otool -L "$QE_ROOT/bin/pw.x" | grep -i mkl
file "$QE_ROOT/bin/pw.x"

# Build QEpy
cd "$QEPY_ROOT"
rm -rf build dist qepy.egg-info

qedir="$QE_ROOT" \
python -m pip install \
  --no-build-isolation \
  --no-cache-dir \
  -v .

# Test outside source tree
cd /tmp
python -c \
  "import qepy; import qepy.qepylibs; print(qepy.__file__)"
```

---

## Design choices

- **QE 7.2 is pinned** because this is the version verified with this QEpy build.
- **GCC/GFortran 14 is pinned** because GCC 15 conflicts with the bundled QE 7.2 MBD source.
- **oneMKL 2023.x is pinned** because macOS support ended with oneAPI 2024.0.
- **LP64 is used** because QE uses standard 32-bit BLAS/LAPACK integers.
- **Sequential MKL is used** to avoid OpenMP-runtime conflicts and MPI oversubscription.
- **Homebrew FFTW is retained** so BLAS/LAPACK and FFT changes can be validated independently.
- **`make all` is required** because QEpy links components beyond `pw.x`.
- **A dedicated Python environment is created** so QEpy's Python build dependencies are reproducible.
- **For all other macOS setups**, use `qe72_qepy_macos_accelerate_skill.md`.
