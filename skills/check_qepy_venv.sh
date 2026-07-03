#!/usr/bin/env bash
# Source this file, then run: check_qepy_venv
#
# Required:
#   VENV_DIR   path to virtual environment
#   CC         C compiler used for QE (for architecture check)
#
# Optional:
#   TOOLCHAIN_PREFIX   e.g. Homebrew prefix — warn if Python is elsewhere
#   PYTHON_VERSIONS    space-separated allowed minors, default "3.10 3.11 3.12"

check_qepy_venv() {
  local fail=0
  local py="${VENV_DIR}/bin/python"
  local allowed="${PYTHON_VERSIONS:-3.10 3.11 3.12}"

  echo "=== Checking ${VENV_DIR} ==="

  if [ -z "${VENV_DIR:-}" ]; then
    echo "FAIL: VENV_DIR is not set"
    return 1
  fi

  if [ ! -x "$py" ]; then
    echo "FAIL: $py not found or not executable"
    return 1
  fi

  if [ -z "${CC:-}" ] || ! command -v "$CC" >/dev/null 2>&1; then
    echo "FAIL: CC is not set or not found ($CC)"
    return 1
  fi

  local ver ok_ver=0
  ver="$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  for v in $allowed; do
    if [ "$ver" = "$v" ]; then
      ok_ver=1
      break
    fi
  done
  if [ "$ok_ver" -eq 0 ]; then
    echo "FAIL: Python $ver (allowed: $allowed)"
    fail=1
  else
    echo "OK: Python $ver"
  fi

  local py_arch gcc_arch
  py_arch="$(file -b "$py" | awk '{print $NF}')"
  gcc_arch="$(file -b "$(command -v "$CC")" | awk '{print $NF}')"
  if [ -n "$py_arch" ] && [ -n "$gcc_arch" ] && [ "$py_arch" != "$gcc_arch" ]; then
    echo "FAIL: Python is $py_arch but $CC is $gcc_arch"
    fail=1
  else
    echo "OK: Python architecture matches toolchain (${py_arch:-unknown})"
  fi

  if [ -n "${TOOLCHAIN_PREFIX:-}" ]; then
    if "$py" -c "import sys; sys.exit(0 if sys.executable.startswith('${TOOLCHAIN_PREFIX}') else 1)" 2>/dev/null; then
      echo "OK: Python from $TOOLCHAIN_PREFIX"
    else
      echo "WARN: Python is not from $TOOLCHAIN_PREFIX (mixed prefixes may cause link errors)"
    fi
  fi

  if [ -f "$VENV_DIR/pyvenv.cfg" ] && grep -q 'include-system-site-packages = true' "$VENV_DIR/pyvenv.cfg"; then
    echo "WARN: include-system-site-packages = true (prefer false)"
  else
    echo "OK: isolated virtual environment"
  fi

  return $fail
}
