#!/usr/bin/env bash
# macOS preflight check for QE 7.2 + QEpy builds.
# Usage: ./preflight_macos.sh
# Does not install packages — reports status and recommends a skill file.

set -euo pipefail

SKILL_ACCEL="qe72_qepy_macos_accelerate_skill.md"
SKILL_MKL="qe72_qepy_macos_mkl_skill.md"
FAIL=0
WARN=0

ok()   { echo "OK: $*"; }
fail() { echo "FAIL: $*"; FAIL=1; }
warn() { echo "WARN: $*"; WARN=1; }

echo "=== QEpy macOS preflight ==="
echo "Machine: $(uname -m) — $(sw_vers -productName 2>/dev/null || echo macOS) $(sw_vers -productVersion 2>/dev/null || true)"
echo

# --- Homebrew detection ---
SELECTED_BREW=""
SELECTED_PREFIX=""
SELECTED_ARCH=""

for brew in /opt/homebrew/bin/brew /usr/local/bin/brew "$HOME/homebrew/bin/brew"; do
  if [ -x "$brew" ]; then
    prefix="$("$brew" --prefix)"
    gcc="$prefix/bin/gcc-14"
    if [ -x "$gcc" ]; then
      arch="$(file -b "$gcc" | awk '{print $NF}')"
      echo "Found Homebrew: $brew (prefix=$prefix, gcc-14=$arch)"
      if [ "$(uname -m)" = "arm64" ] && [ "$arch" = "arm64" ]; then
        SELECTED_BREW="$brew"
        SELECTED_PREFIX="$prefix"
        SELECTED_ARCH="$arch"
      elif [ -z "$SELECTED_BREW" ]; then
        SELECTED_BREW="$brew"
        SELECTED_PREFIX="$prefix"
        SELECTED_ARCH="$arch"
      fi
    else
      echo "  (no gcc-14 at $prefix)"
    fi
  fi
done

echo
if [ -z "$SELECTED_BREW" ]; then
  fail "No Homebrew with gcc-14 found. Install: brew install gcc@14 open-mpi fftw python@3.10"
else
  ok "Selected Homebrew: $SELECTED_BREW"
  ok "HOMEBREW_PREFIX=$SELECTED_PREFIX (gcc-14 arch: $SELECTED_ARCH)"
  if [ "$(uname -m)" = "arm64" ] && [ "$SELECTED_ARCH" = "x86_64" ]; then
    warn "Apple Silicon Mac using x86_64 Homebrew (Rosetta). Build works but pw.x will not be native arm64."
    warn "For native arm64, install Homebrew at /opt/homebrew or ~/homebrew with arm64 gcc-14."
  fi
fi

# --- Skill recommendation ---
RECOMMENDED_SKILL="$SKILL_ACCEL"
if [ -f /opt/intel/oneapi/setvars.sh ] && [ -d /opt/intel/oneapi/mkl ]; then
  warn "Intel oneAPI detected at /opt/intel/oneapi"
  echo "  Default skill: $SKILL_ACCEL"
  echo "  If you need oneMKL: $SKILL_MKL"
else
  echo
  echo "Recommended skill: $RECOMMENDED_SKILL"
fi

# --- Xcode CLI ---
echo
if xcode-select -p >/dev/null 2>&1; then
  ok "Xcode Command Line Tools: $(xcode-select -p)"
else
  fail "Xcode Command Line Tools missing. Run: xcode-select --install"
fi

# --- Tools (if Homebrew selected) ---
if [ -n "$SELECTED_PREFIX" ]; then
  echo
  echo "=== Tool checks ($SELECTED_PREFIX) ==="
  BREW_BIN="$SELECTED_PREFIX/bin"
  BREW_OPT="$SELECTED_PREFIX/opt"

  for cmd in "$BREW_BIN/gcc-14" "$BREW_BIN/gfortran-14" "$BREW_BIN/mpif90"; do
    if [ -x "$cmd" ]; then
      ok "$(basename "$cmd") ($("$cmd" --version 2>&1 | head -1))"
    else
      fail "Missing $cmd — brew install gcc@14 open-mpi"
    fi
  done

  if [ -f "$BREW_OPT/fftw/include/fftw3.f03" ] || [ -f "$SELECTED_PREFIX/include/fftw3.f03" ]; then
    ok "fftw3.f03 present"
  else
    fail "fftw3.f03 missing — brew install fftw"
  fi

  PY310="$BREW_OPT/python@3.10/bin/python3.10"
  if [ -x "$PY310" ]; then
    ok "python3.10 ($("$PY310" --version 2>&1))"
  else
    fail "python@3.10 missing — brew install python@3.10"
  fi

  if [ -x "$BREW_BIN/mpif90" ] && [ -x "$BREW_BIN/gfortran-14" ]; then
    export PATH="$BREW_BIN:$PATH"
    export OMPI_CC="$BREW_BIN/gcc-14"
    export OMPI_FC="$BREW_BIN/gfortran-14"
    wrapper="$("$BREW_BIN/mpif90" --showme:command 2>/dev/null || true)"
    if echo "$wrapper" | grep -q gfortran-14; then
      ok "mpif90 wraps gfortran-14"
    else
      warn "mpif90 may not use gfortran-14: $wrapper"
      echo "  export OMPI_CC=$BREW_BIN/gcc-14"
      echo "  export OMPI_FC=$BREW_BIN/gfortran-14"
    fi

    mpif90_fc="$(OMPI_FC="$BREW_BIN/gfortran-14" "$BREW_BIN/mpif90" -show 2>/dev/null | awk '{print $1}' || true)"
    if [ -n "$mpif90_fc" ] && [ "$mpif90_fc" = "$BREW_BIN/gfortran-14" ]; then
      ok "mpif90 -show resolves to gfortran-14 with OMPI_FC set"
    else
      warn "mpif90 does not resolve to gfortran-14 even with OMPI_FC (got: ${mpif90_fc:-unknown})"
      warn "Source env.sh before every make step; consider rebuilding QE after fixing."
    fi

    wrapper_data=""
    for f in "$SELECTED_PREFIX/opt/open-mpi/share/openmpi/mpifort-wrapper-data.txt" \
             "$SELECTED_PREFIX/share/openmpi/mpifort-wrapper-data.txt" \
             "$SELECTED_PREFIX/Cellar/open-mpi"/*/share/openmpi/mpifort-wrapper-data.txt; do
      [ -f "$f" ] && wrapper_data="$f" && break
    done
    if [ -n "$wrapper_data" ]; then
      if grep -q 'compiler:fortran:absolute' "$wrapper_data" 2>/dev/null; then
        baked="$(grep 'compiler:fortran:absolute' "$wrapper_data" 2>/dev/null | head -1 | sed 's/.*absolute://' || true)"
        if [ -n "$baked" ] && ! echo "$baked" | grep -q 'gfortran-14'; then
          warn "Open MPI baked-in Fortran compiler: $baked"
          warn "Always export OMPI_FC=$BREW_BIN/gfortran-14 and source env.sh before make"
          echo "  cat $wrapper_data | grep absolute"
        else
          ok "Open MPI wrapper default includes gfortran-14"
        fi
      else
        ok "Open MPI wrapper uses PATH for gfortran — still set OMPI_FC and source env.sh before make"
      fi
    fi
  fi

  if [ -x "$BREW_BIN/gmake" ]; then
    sys_make_ver="$(/usr/bin/make --version 2>/dev/null | head -1 || true)"
    gmake_ver="$("$BREW_BIN/gmake" --version 2>/dev/null | head -1 || true)"
    if [ -n "$sys_make_ver" ] && [ "$sys_make_ver" != "$gmake_ver" ]; then
      ok "gmake available ($gmake_ver)"
      warn "Use gmake via PATH shim when building QEpy (Apple make: $sys_make_ver)"
    else
      ok "gmake present"
    fi
  else
    warn "gmake missing — brew install make (needed for QEpy build; installed as gmake)"
  fi
fi

# --- Disk space ---
echo
avail="$(df -g "$HOME" 2>/dev/null | awk 'NR==2 {print $4}' || df -h "$HOME" | awk 'NR==2 {print $4}')"
if [ -n "$avail" ]; then
  echo "Free space under \$HOME: ${avail} (recommend ≥ 10 GB for full QE build)"
fi

# --- Suggested exports ---
if [ -n "$SELECTED_BREW" ]; then
  echo
  echo "=== Suggested shell setup ==="
  cat <<EOF
eval "\$($SELECTED_BREW shellenv)"
export HOMEBREW_PREFIX="$SELECTED_PREFIX"
export BREW_BIN="\$HOMEBREW_PREFIX/bin"
export BREW_OPT="\$HOMEBREW_PREFIX/opt"
export CC="\$BREW_BIN/gcc-14"
export FC="\$BREW_BIN/gfortran-14"
export OMPI_CC="\$CC"
export OMPI_FC="\$FC"
export PATH="\$BREW_BIN:\$PATH"
export PYTHON="\$BREW_OPT/python@3.10/bin/python3.10"
export BUILD_ROOT="\${BUILD_ROOT:-\$HOME/qe_build}"
export VENV_NAME="\${VENV_NAME:-venv_qepy}"
# After first configure: source "\$BUILD_ROOT/env.sh" before every make / QEpy build
EOF
fi

echo
if [ "$FAIL" -ne 0 ]; then
  echo "Preflight FAILED — fix issues above before starting the skill."
  exit 1
fi
if [ "$WARN" -ne 0 ]; then
  echo "Preflight passed with warnings."
  exit 0
fi
echo "Preflight passed. Proceed with skills/$RECOMMENDED_SKILL"
exit 0
