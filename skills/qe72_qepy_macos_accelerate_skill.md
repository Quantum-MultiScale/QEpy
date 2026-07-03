# Skill: Build Quantum ESPRESSO 7.2 and QEpy on macOS (Intel and Apple Silicon)

## Which skill to use

| Goal | Skill file |
|------|------------|
| **Default macOS build** — Apple Accelerate for BLAS/LAPACK | `qe72_qepy_macos_accelerate_skill.md` (this file) |
| **Intel Mac with oneMKL** — archived Intel oneAPI 2023.x | `qe72_qepy_macos_mkl_skill.md` |
| **Ubuntu — Intel MPI + oneMKL** (Linux default) | `qe72_qepy_ubuntu_intel_skill.md` |
| **RHEL 9 — Intel MPI + oneMKL** (Linux default) | `qe72_qepy_rhel9_intel_skill.md` |
| **Ubuntu — Open MPI + OpenBLAS** (open-source alternative) | `qe72_qepy_ubuntu_openblas_skill.md` |
| **RHEL 9 — Open MPI + OpenBLAS** (open-source alternative) | `qe72_qepy_rhel9_openblas_skill.md` |

Use **this skill** unless you specifically need Intel oneMKL. Do not let `configure` auto-detect BLAS/LAPACK on macOS; always set Accelerate explicitly as described below.

The obsolete `qe72_qepy_macos_system_blas_skill.md` has been removed. It relied on implicit BLAS detection and is superseded by this skill.

---

## Purpose

This skill gives a reproducible, start-to-finish procedure for building:

- Quantum ESPRESSO tag `qe-7.2`
- QEpy compatible with QE 7.2
- a dedicated Python 3.10 virtual environment (user-chosen name; default `venv_qepy`)
- Homebrew GCC/GFortran 14, Open MPI, and FFTW
- Apple Accelerate for BLAS and LAPACK

It supports two common macOS Homebrew layouts:

| Layout | Typical prefix | Architecture | When to use |
|--------|----------------|--------------|-------------|
| **Intel Homebrew** | `/usr/local` | `x86_64` | Intel Macs, or Apple Silicon Macs running Homebrew under Rosetta |
| **Apple Silicon Homebrew** | `/opt/homebrew` or `~/homebrew` | `arm64` | Apple Silicon Macs with a native arm64 toolchain |

Quantum ESPRESSO requires BLAS and LAPACK. This recipe selects Apple Accelerate explicitly rather than relying on `configure` to discover a system implementation implicitly.

The Quantum ESPRESSO 7.2 release is tagged `qe-7.2` in the official QEF GitLab repository.

**Important:** use one Homebrew prefix consistently for the entire build. Do not mix `/usr/local` compilers with `/opt/homebrew` libraries, or vice versa.

**Agent instruction:** before creating or reusing a virtual environment, ask the user what name they want for the QEpy Python environment. If they have no preference, use `venv_qepy`.

**Before building on macOS:** run [`preflight_macos.sh`](preflight_macos.sh). Shared steps (clone, venv, QE build, QEpy install, test) are in [`common.md`](common.md).

---

# 1. Detect your Homebrew layout

Run these checks before installing anything:

```bash
uname -m
```

Expected values:

```text
x86_64   # Intel Mac, or Apple Silicon terminal running under Rosetta
arm64    # Apple Silicon Mac, native terminal
```

List available Homebrew installations:

```bash
for brew in /opt/homebrew/bin/brew /usr/local/bin/brew "$HOME/homebrew/bin/brew"; do
  if [ -x "$brew" ]; then
    eval "$("$brew" shellenv)"
    echo "brew: $brew"
    echo "  prefix: $(brew --prefix)"
    echo "  gcc-14: $(file "$(brew --prefix)/bin/gcc-14" 2>/dev/null)"
  fi
done
```

Choose the Homebrew whose `gcc-14` architecture matches the build you want:

- **Native arm64 build on Apple Silicon:** pick the Homebrew where `file .../gcc-14` reports `arm64`.
- **x86_64 build (Intel Mac or Rosetta):** pick the Homebrew where `file .../gcc-14` reports `x86_64`.

### Set environment variables

After choosing a Homebrew, load it and define reusable paths:

```bash
# Example for Apple Silicon Homebrew at /opt/homebrew:
eval "$(/opt/homebrew/bin/brew shellenv)"

# Example for Intel/Rosetta Homebrew at /usr/local:
# eval "$(/usr/local/bin/brew shellenv)"

# Example for user-local Apple Silicon Homebrew (no sudo):
# eval "$("$HOME/homebrew/bin/brew" shellenv)"

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

Reference values:

| System | `HOMEBREW_PREFIX` | `gcc-14 -dumpmachine` |
|--------|-------------------|-------------------------|
| Intel Mac | `/usr/local` | `x86_64-apple-darwin*` |
| Apple Silicon (native) | `/opt/homebrew` or `~/homebrew` | `aarch64-apple-darwin*` or `arm64-apple-darwin*` |

Add `brew shellenv` to your shell profile if needed so `mpif90` resolves to the same prefix:

```bash
# Apple Silicon (typical)
eval "$(/opt/homebrew/bin/brew shellenv)"

# Intel / Rosetta
eval "$(/usr/local/bin/brew shellenv)"

# User-local Apple Silicon (no sudo)
eval "$("$HOME/homebrew/bin/brew" shellenv)"
```

---

# 2. Install prerequisites

Install Apple command-line tools if they are not already present:

```bash
xcode-select --install
```

### Apple Silicon Homebrew (arm64)

If `/opt/homebrew` does not exist yet, install Homebrew for Apple Silicon (requires administrator password):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Alternatively, install Homebrew in your home directory without `sudo`:

```bash
mkdir -p "$HOME/homebrew"
curl -fsSL https://github.com/Homebrew/brew/tarball/master | tar xz --strip 1 -C "$HOME/homebrew"
eval "$("$HOME/homebrew/bin/brew" shellenv)"
```

Then install packages:

```bash
brew install git python@3.10 gcc@14 open-mpi fftw make
```

### Intel Homebrew (x86_64)

On Intel Macs, or Apple Silicon Macs using Rosetta Homebrew:

```bash
eval "$(/usr/local/bin/brew shellenv)"
brew install git python@3.10 gcc@14 open-mpi fftw make
```

On Apple Silicon, confirm you are using the intended brew:

```bash
brew --prefix    # /usr/local for Rosetta, /opt/homebrew for native
file "$(brew --prefix)/bin/gcc-14"
```

---

# 3. Create a clean working directory

Choose a parent directory for both repositories:

```bash
mkdir -p "$HOME/Documents/QEPy_on_mac"
cd "$HOME/Documents/QEPy_on_mac"
```

Define reusable paths:

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
export VENV_NAME="${VENV_NAME:-venv_qepy}"   # set by user, or default
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"
```

Use separate build directories when maintaining both architectures, for example:

```text
qe_accelerate/        # x86_64 build via /usr/local Homebrew
qe_native/            # arm64 build via /opt/homebrew or ~/homebrew
```

---

# 4. Clone Quantum ESPRESSO 7.2

Clone the official Quantum ESPRESSO repository directly at the `qe-7.2` tag:

```bash
git clone \
  --branch qe-7.2 \
  --single-branch \
  https://gitlab.com/QEF/q-e.git \
  q-e
```

Enter the repository:

```bash
cd "$QE_ROOT"
```

Confirm the version:

```bash
git describe --tags --exact-match
```

Expected output:

```text
qe-7.2
```

Record the exact commit for reproducibility:

```bash
git rev-parse HEAD
```

Initialize any submodules:

```bash
git submodule update --init --recursive
```

---

# 5. Clone QEpy

Return to the parent directory:

```bash
cd "$BUILD_ROOT"
```

Clone QEpy:

```bash
git clone https://github.com/shaoxc/qepy.git QEpy
```

Enter the repository:

```bash
cd "$QEPY_ROOT"
```

The build used the `dev` branch:

```bash
git checkout dev
```

Record the exact QEpy commit:

```bash
git rev-parse HEAD
```

For a fully reproducible installation, save this commit hash and later check it out explicitly:

```bash
git checkout <saved-qepy-commit>
```

---

# 6. Create or verify the Python environment

Before proceeding, confirm the virtual environment name with the user. Use `venv_qepy` if they have no preference:

```bash
export VENV_NAME="${VENV_NAME:-venv_qepy}"
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"
echo "QEpy virtual environment: $VENV_DIR"
```

Ensure the correct Homebrew is active:

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"   # or /usr/local or ~/homebrew
export HOMEBREW_PREFIX="$(brew --prefix)"
export BREW_BIN="$HOMEBREW_PREFIX/bin"
export BREW_OPT="$HOMEBREW_PREFIX/opt"
```

Determine the target architecture from the chosen compiler toolchain:

```bash
TARGET_ARCH="$(file -b "$BREW_BIN/gcc-14" | awk -F': ' '/architecture/ {print $2; exit}')"
echo "Target QE architecture: $TARGET_ARCH"
```

## Create a new environment

If `$VENV_DIR` does not exist yet:

```bash
cd "$BUILD_ROOT"

"$BREW_OPT/python@3.10/bin/python3.10" -m venv "$VENV_DIR"
```

## Reuse an existing environment

If `$VENV_DIR` already exists, do **not** recreate it automatically. Run the compatibility checks below first. If any check fails, tell the user and either fix the environment or choose a different `VENV_NAME`.

Or source the shared check script (set `VENV_DIR`, `CC`, and optionally `TOOLCHAIN_PREFIX="$HOMEBREW_PREFIX"`):

```bash
source "$QEPY_ROOT/skills/check_qepy_venv.sh"
check_qepy_venv || exit 1
```

## Compatibility checks (inline)

Run these checks before installing QEpy build dependencies or building QEpy. All must pass.

```bash
check_qepy_venv() {
  local fail=0
  local py="$VENV_DIR/bin/python"

  echo "=== Checking $VENV_DIR ==="

  if [ ! -x "$py" ]; then
    echo "FAIL: $py not found or not executable"
    return 1
  fi

  # Python version: QEpy for QE 7.2 expects 3.10
  local ver
  ver="$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [ "$ver" != "3.10" ]; then
    echo "FAIL: Python $ver (need 3.10)"
    fail=1
  else
    echo "OK: Python $ver"
  fi

  # Architecture must match the Homebrew used for QE
  local py_arch gcc_arch
  py_arch="$(file -b "$py" | awk -F': ' '/architecture/ {print $2; exit}')"
  gcc_arch="$(file -b "$BREW_BIN/gcc-14" | awk -F': ' '/architecture/ {print $2; exit}')"
  if [ "$py_arch" != "$gcc_arch" ]; then
    echo "FAIL: Python is $py_arch but gcc-14 is $gcc_arch"
    echo "      Use a venv created with python@3.10 from the same Homebrew prefix."
    fail=1
  else
    echo "OK: Python architecture $py_arch matches toolchain"
  fi

  # Python should come from the same Homebrew prefix as the compilers
  if ! "$py" -c "import sys; sys.exit(0 if sys.executable.startswith('$HOMEBREW_PREFIX') else 1)"; then
    echo "WARN: Python is not from $HOMEBREW_PREFIX"
    echo "      This may still work, but mixed Homebrew prefixes often cause link errors."
  else
    echo "OK: Python from $HOMEBREW_PREFIX"
  fi

  # Isolated environment (no system site-packages)
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

Activate the environment:

```bash
source "$VENV_DIR/bin/activate"
```

Upgrade packaging tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Install the build dependencies:

```bash
python -m pip install \
  "numpy<2" \
  "f90wrap==0.2.14" \
  meson \
  ninja \
  packaging
```

Verify tools and record architecture:

```bash
python --version
file "$(which python)"
python -m pip show f90wrap
meson --version
ninja --version
```

Optional: confirm build dependencies before proceeding to QEpy:

```bash
python -c "import numpy; import f90wrap; import mesonbuild; import ninja; print('QEpy build deps OK')"
```

The Python binary architecture must match your chosen Homebrew (`arm64` or `x86_64`) and the QE binaries you are about to build.

The successful reference environment used Python 3.10 with isolated system packages:

```text
include-system-site-packages = false
```

---

# 7. Configure the compiler toolchain

Set GCC 14 and GFortran 14 explicitly using your Homebrew prefix:

```bash
export HOMEBREW_PREFIX="$(brew --prefix)"
export BREW_BIN="$HOMEBREW_PREFIX/bin"

export CC="$BREW_BIN/gcc-14"
export FC="$BREW_BIN/gfortran-14"
export F77="$BREW_BIN/gfortran-14"
export F90="$BREW_BIN/gfortran-14"
```

Force Open MPI to use the same compiler family:

```bash
export OMPI_CC="$CC"
export OMPI_FC="$FC"
export PATH="$BREW_BIN:$PATH"
```

Confirm:

```bash
"$CC" --version
"$FC" --version
"$BREW_BIN/mpif90" --showme:command
file "$CC" "$FC" "$BREW_BIN/mpif90"
```

The MPI wrapper should resolve to GFortran 14 from the same prefix.

Do not mix GFortran 14 and GFortran 15 module files or runtime libraries.

Do not mix compilers from different Homebrew installations.

---

# 8. Configure Quantum ESPRESSO

Enter the QE source directory:

```bash
cd "$QE_ROOT"
```

Run configure with the required compilers, position-independent-code flags, and Apple Accelerate for BLAS/LAPACK:

```bash
./configure \
  CC="$CC" \
  F77="$FC" \
  F90="$FC" \
  MPIF90="$BREW_BIN/mpif90" \
  CFLAGS="-fPIC" \
  FFLAGS="-fPIC -fallow-argument-mismatch" \
  BLAS_LIBS="-framework Accelerate" \
  LAPACK_LIBS=""
```

Apple's Accelerate framework supplies both BLAS and LAPACK, so the complete framework link is placed in `BLAS_LIBS` and `LAPACK_LIBS` is left empty.

The configure step creates `make.inc`.

---

# 9. Required `make.inc` corrections

Open:

```bash
nano "$QE_ROOT/make.inc"
```

or use another editor.

Replace hardcoded `/usr/local` paths with your `$HOMEBREW_PREFIX`. The following settings are essential.

## Compiler definitions

Use your Homebrew bin directory (examples for both layouts):

```make
# Intel / Rosetta (/usr/local):
F90     = /usr/local/bin/gfortran-14
MPIF90  = /usr/local/bin/mpif90
CC      = /usr/local/bin/gcc-14
CPP     = /usr/local/bin/gcc-14 -E -P

# Apple Silicon (/opt/homebrew or ~/homebrew):
F90     = /opt/homebrew/bin/gfortran-14
MPIF90  = /opt/homebrew/bin/mpif90
CC      = /opt/homebrew/bin/gcc-14
CPP     = /opt/homebrew/bin/gcc-14 -E -P
```

Generic form (substitute your actual prefix):

```make
F90     = $(HOMEBREW_PREFIX)/bin/gfortran-14
MPIF90  = $(HOMEBREW_PREFIX)/bin/mpif90
CC      = $(HOMEBREW_PREFIX)/bin/gcc-14
CPP     = $(HOMEBREW_PREFIX)/bin/gcc-14 -E -P
```

`make.inc` does not expand shell variables — write the full path explicitly.

`CC` must not contain `-E -P`.

Incorrect:

```make
CC = /usr/local/bin/gcc-14 -E -P
```

That only preprocesses C sources and does not create object files.

## Preprocessor flags

Use:

```make
CPPFLAGS = $(DFLAGS) $(IFLAGS)
```

## Position-independent compiler flags

Use:

```make
CFLAGS = -fPIC $(DFLAGS) $(IFLAGS) $(CUDA_CFLAGS)

FFLAGS = -fPIC -fallow-argument-mismatch

F90FLAGS = $(FFLAGS) -cpp $(FDFLAGS) \
           $(CUDA_F90FLAGS) $(IFLAGS) $(MODFLAGS)
```

QEpy needs QE object files compiled with `-fPIC`, because it links them into shared libraries.

## FFTW include path

Use your Homebrew FFTW location:

```make
# Intel / Rosetta:
IFLAGS = -I. -I$(TOPDIR)/include \
         -I/usr/local/opt/fftw/include

# Apple Silicon:
IFLAGS = -I. -I$(TOPDIR)/include \
         -I/opt/homebrew/opt/fftw/include
```

## FFTW library path

```make
# Intel / Rosetta:
FFT_LIBS = -L/usr/local/opt/fftw/lib -lfftw3

# Apple Silicon:
FFT_LIBS = -L/opt/homebrew/opt/fftw/lib -lfftw3
```

## BLAS and LAPACK

Quantum ESPRESSO requires both BLAS and LAPACK. Use Apple Accelerate explicitly on both architectures:

```make
BLAS_LIBS = -framework Accelerate
LAPACK_LIBS =
```

Do not leave old or automatically detected alternatives in these variables. In particular, remove entries such as:

```make
BLAS_LIBS = -lblas
LAPACK_LIBS = -llapack
```

and do not combine Accelerate with `-lopenblas`, `-lblas`, or `-llapack`.

The final QE link order places `LAPACK_LIBS` before `BLAS_LIBS`. Because Accelerate provides both interfaces in one framework, putting the framework once in `BLAS_LIBS` is sufficient.

### Optional OpenBLAS alternative

To use Homebrew OpenBLAS instead:

```bash
brew install openblas
```

Then set (adjust prefix as needed):

```make
OPENBLAS_ROOT = /usr/local/opt/openblas    # Intel / Rosetta
# OPENBLAS_ROOT = /opt/homebrew/opt/openblas  # Apple Silicon

BLAS_LIBS = -L$(OPENBLAS_ROOT)/lib \
            -Wl,-rpath,$(OPENBLAS_ROOT)/lib \
            -lopenblas

LAPACK_LIBS =
```

Use either Accelerate or OpenBLAS, not both. Accelerate is the default recommendation for this macOS skill because it is native to macOS and requires no additional runtime library.

Check that the Fortran interface exists:

```bash
ls "$HOMEBREW_PREFIX/opt/fftw/include/fftw3.f03"
```

## Remove unnecessary LLVM paths

Remove these unless they are required for another component:

```make
-I/usr/local/opt/llvm/include
-L/usr/local/opt/llvm/lib
```

In particular, prefer:

```make
CPPFLAGS = $(DFLAGS) $(IFLAGS)
LDFLAGS  =
```

rather than mixing LLVM and GCC paths.

---

# 10. Build all of Quantum ESPRESSO

Before building, clean old objects if this is not a fresh clone:

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

QEpy requires object and module files from several QE components, including:

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

Also test the main executable:

```bash
"$QE_ROOT/bin/pw.x" < /dev/null 2>&1 | head -5
```

Check the binary architecture:

```bash
file "$QE_ROOT/bin/pw.x"
```

Expected:

```text
# Intel / Rosetta build:
Mach-O 64-bit executable x86_64

# Apple Silicon native build:
Mach-O 64-bit executable arm64
```

Verify that `pw.x` uses Accelerate:

```bash
otool -L "$QE_ROOT/bin/pw.x" | grep -E 'Accelerate|vecLib'
```

A native Accelerate build should show a framework path such as:

```text
/System/Library/Frameworks/Accelerate.framework/...
```

Check that OpenBLAS or generic BLAS/LAPACK were not linked accidentally:

```bash
otool -L "$QE_ROOT/bin/pw.x" | grep -E 'openblas|libblas|liblapack'
```

For the Accelerate configuration, this second command should normally produce no output.

---

# 11. Build QEpy

Activate the dedicated environment:

```bash
source "$VENV_DIR/bin/activate"
```

Re-run compatibility checks if the environment was created earlier in the workflow:

```bash
check_qepy_venv
```

Reassert compiler consistency:

```bash
export HOMEBREW_PREFIX="$(brew --prefix)"
export BREW_BIN="$HOMEBREW_PREFIX/bin"
export CC="$BREW_BIN/gcc-14"
export FC="$BREW_BIN/gfortran-14"
export OMPI_CC="$CC"
export OMPI_FC="$FC"
export PATH="$BREW_BIN:$PATH"
```

Enter the QEpy repository:

```bash
cd "$QEPY_ROOT"
```

Remove stale build products:

```bash
rm -rf build dist
rm -rf qepy.egg-info 2>/dev/null || true
```

Install QEpy:

```bash
qedir="$QE_ROOT" \
python -m pip install \
  --no-build-isolation \
  --no-cache-dir \
  -v .
```

`--no-build-isolation` is important because it forces the build to use the versions installed in `$VENV_NAME`, including:

```text
f90wrap==0.2.14
meson
ninja
```

A successful build ends with:

```text
Successfully built qepy
Successfully installed qepy-...
```

---

# 12. Test QEpy correctly

Do not test from inside the QEpy repository.

The source directory contains a local `qepy/` package that can shadow the installed version and cause:

```text
ModuleNotFoundError: No module named 'qepy.__config__'
```

Move elsewhere:

```bash
cd /tmp
```

Check the imported location:

```bash
python -c "import qepy; print(qepy.__file__)"
```

It should point inside:

```text
$VENV_DIR/lib/python3.10/site-packages/
```

Test the compiled libraries:

```bash
python -c \
  "import qepy; import qepy.qepylibs; print('QEpy import successful')"
```

---

# 13. Troubleshooting

## Incompatible Python virtual environment

Typical symptoms:

```text
FAIL: Python is arm64 but gcc-14 is x86_64
```

or QEpy build/link errors after mixing `/usr/local` and `/opt/homebrew` Python.

Fix:

1. Confirm `VENV_NAME` and `VENV_DIR`.
2. Run `check_qepy_venv` from section 6.
3. If the existing venv is wrong, choose a new name and recreate:

```bash
export VENV_NAME="venv_qepy_arm64"   # example
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"
"$BREW_OPT/python@3.10/bin/python3.10" -m venv "$VENV_DIR"
```

4. Never reuse a venv built with a different Homebrew prefix or architecture.

---

## Wrong Homebrew / mixed architectures

Typical symptoms:

```text
ld: warning: ignoring file ... incompatible architecture (have 'x86_64', need 'arm64')
```

or link errors mixing `/usr/local` and `/opt/homebrew` libraries.

Fix:

1. Pick one Homebrew prefix and load it with `brew shellenv`.
2. Confirm `file "$BREW_BIN/gcc-14"` matches your target architecture.
3. Rebuild QE from a clean tree after correcting `make.inc`.

On Apple Silicon Macs with both brews installed, `which brew` may point to the wrong one. Always call the intended brew explicitly:

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"   # native arm64
# eval "$(/usr/local/bin/brew shellenv)"    # Rosetta x86_64
```

## `laxlib.h` preprocessing failure

Typical output:

```text
warning: missing terminating ' character
cc: error: no input files
```

Fix (use your Homebrew gcc path):

```make
CPP = /opt/homebrew/bin/gcc-14 -E -P
```

---

## C object files are missing

Typical output:

```text
ar: ptrace.o: No such file or directory
ar: copy.o: No such file or directory
```

Cause:

```make
CC = gcc -E -P
```

Fix:

```make
CC  = $BREW_BIN/gcc-14
CPP = $BREW_BIN/gcc-14 -E -P
```

(write the full path in `make.inc`)

---

## `fftw3.f03` is missing

Typical output:

```text
Fatal Error: fftw3.f03: No such file or directory
```

Fix (adjust prefix):

```make
IFLAGS = -I. -I$(TOPDIR)/include \
         -I/opt/homebrew/opt/fftw/include
```

and:

```make
FFT_LIBS = -L/opt/homebrew/opt/fftw/lib -lfftw3
```

---

## GCC 15 MBD conflict

Typical symptom: a collision involving `f_c_string`.

Cause: GCC 15 introduced an intrinsic with that name, while the bundled QE 7.2 MBD source defines its own routine with the same name.

Fix: use GCC/GFortran 14 consistently.

---

## QEpy cannot find Meson

Typical output:

```text
meson: No such file or directory
```

Fix:

```bash
source "$VENV_DIR/bin/activate"
python -m pip install meson ninja
```

---

## Missing `GWW/minpack` object files

Typical output:

```text
ld: file not found: .../GWW/minpack/dpmpar.o
```

Cause: only part of QE was built.

Fix:

```bash
cd "$QE_ROOT"
make all
```

---

## Missing `ld1inc.mod`

Typical output:

```text
Fatal Error: Cannot open module file 'ld1inc.mod'
```

Cause: the QE atomic/ld1 component was not built.

Fix:

```bash
cd "$QE_ROOT"
make all
```

---

## Local QEpy source shadows the installed package

Typical output:

```text
ModuleNotFoundError: No module named 'qepy.__config__'
```

Fix:

```bash
cd /tmp
python -c "import qepy; print(qepy.__file__)"
```

---

## QE links the wrong BLAS/LAPACK implementation

Inspect the generated settings:

```bash
grep -E '^(BLAS_LIBS|LAPACK_LIBS)' "$QE_ROOT/make.inc"
```

For the default native macOS configuration, use:

```make
BLAS_LIBS = -framework Accelerate
LAPACK_LIBS =
```

After changing these variables, remove all old objects and archives before rebuilding:

```bash
cd "$QE_ROOT"
make clean || true
find . -name '*.o' -delete
find . -name '*.mod' -delete
find . -name '*.a' -delete
make all
```

Confirm the result:

```bash
otool -L "$QE_ROOT/bin/pw.x" | grep -E 'Accelerate|vecLib'
```

---

# 14. Condensed full procedure

The script below auto-detects Homebrew. It prefers native arm64 Homebrew on Apple Silicon, then falls back to `/usr/local`.

```bash
# --- Detect Homebrew ---
ARCH="$(uname -m)"
if [ -x /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -x "$HOME/homebrew/bin/brew" ]; then
  eval "$("$HOME/homebrew/bin/brew" shellenv)"
elif [ -x /usr/local/bin/brew ]; then
  eval "$(/usr/local/bin/brew shellenv)"
else
  echo "No Homebrew found. Install Homebrew first." >&2
  exit 1
fi

export HOMEBREW_PREFIX="$(brew --prefix)"
export BREW_BIN="$HOMEBREW_PREFIX/bin"
export BREW_OPT="$HOMEBREW_PREFIX/opt"

echo "Using Homebrew: $HOMEBREW_PREFIX ($(file -b "$BREW_BIN/gcc-14"))"

# Working directory
mkdir -p "$HOME/Documents/QEPy_on_mac"
cd "$HOME/Documents/QEPy_on_mac"

export BUILD_ROOT="$PWD"
export QE_ROOT="$BUILD_ROOT/q-e"
export QEPY_ROOT="$BUILD_ROOT/QEpy"

# Ask user for venv name; default venv_qepy if no preference
export VENV_NAME="${VENV_NAME:-venv_qepy}"
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"
echo "QEpy virtual environment: $VENV_DIR"

# Clone QE 7.2
git clone \
  --branch qe-7.2 \
  --single-branch \
  https://gitlab.com/QEF/q-e.git \
  q-e

cd "$QE_ROOT"
git submodule update --init --recursive
git describe --tags --exact-match

# Clone QEpy
cd "$BUILD_ROOT"
git clone https://github.com/shaoxc/qepy.git QEpy
cd "$QEPY_ROOT"
git checkout dev

# Dedicated Python environment
cd "$BUILD_ROOT"
if [ ! -d "$VENV_DIR" ]; then
  "$BREW_OPT/python@3.10/bin/python3.10" -m venv "$VENV_DIR"
fi

# Run compatibility checks (see section 6 for full check_qepy_venv)
py="$VENV_DIR/bin/python"
ver="$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
py_arch="$(file -b "$py" | awk -F': ' '/architecture/ {print $2; exit}')"
gcc_arch="$(file -b "$BREW_BIN/gcc-14" | awk -F': ' '/architecture/ {print $2; exit}')"
[ "$ver" = "3.10" ] || { echo "Need Python 3.10, got $ver" >&2; exit 1; }
[ "$py_arch" = "$gcc_arch" ] || { echo "Python ($py_arch) != gcc-14 ($gcc_arch)" >&2; exit 1; }

source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install \
  "numpy<2" \
  "f90wrap==0.2.14" \
  meson \
  ninja \
  packaging

# Compiler environment
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
  BLAS_LIBS="-framework Accelerate" \
  LAPACK_LIBS=""

# Edit make.inc — set paths using $HOMEBREW_PREFIX:
#   F90, CC, CPP, MPIF90  -> $BREW_BIN/...
#   IFLAGS FFTW include   -> -I$BREW_OPT/fftw/include
#   FFT_LIBS              -> -L$BREW_OPT/fftw/lib -lfftw3
#   BLAS_LIBS             -> -framework Accelerate
#   LAPACK_LIBS           -> (empty)
#   CPPFLAGS              -> $(DFLAGS) $(IFLAGS)
#   LDFLAGS               -> (empty)
# Remove any -I.../llvm or -L.../llvm entries.

# Build all QE components
make all

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

file "$QE_ROOT/bin/pw.x"
otool -L "$QE_ROOT/bin/pw.x" | grep -E 'Accelerate|vecLib'
```

---

# 15. Quick reference: path substitution

When editing `make.inc`, replace `/usr/local` with your actual prefix:

| Variable | Intel / Rosetta (`/usr/local`) | Apple Silicon (`/opt/homebrew` or `~/homebrew`) |
|----------|-------------------------------|------------------------------------------------|
| `CC` | `/usr/local/bin/gcc-14` | `/opt/homebrew/bin/gcc-14` |
| `F90` | `/usr/local/bin/gfortran-14` | `/opt/homebrew/bin/gfortran-14` |
| `MPIF90` | `/usr/local/bin/mpif90` | `/opt/homebrew/bin/mpif90` |
| `CPP` | `/usr/local/bin/gcc-14 -E -P` | `/opt/homebrew/bin/gcc-14 -E -P` |
| FFTW include | `-I/usr/local/opt/fftw/include` | `-I/opt/homebrew/opt/fftw/include` |
| FFTW lib | `-L/usr/local/opt/fftw/lib -lfftw3` | `-L/opt/homebrew/opt/fftw/lib -lfftw3` |
| `BLAS_LIBS` | `-framework Accelerate` | `-framework Accelerate` |
| `LAPACK_LIBS` | *(empty)* | *(empty)* |
| Expected `pw.x` arch | `x86_64` | `arm64` |
| QEpy venv (default) | `$BUILD_ROOT/venv_qepy` | `$BUILD_ROOT/venv_qepy` |

Both layouts use Apple Accelerate for linear algebra. The main difference is the Homebrew prefix and resulting binary architecture. The Python venv name is user-configurable via `VENV_NAME`; the venv must use Python 3.10 from the same Homebrew prefix and architecture as the QE build.

For Intel oneMKL on Intel Macs, use `qe72_qepy_macos_mkl_skill.md` instead.
