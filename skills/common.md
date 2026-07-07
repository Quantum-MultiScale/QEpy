# Common steps (all platforms)

Platform skills (`qe72_qepy_*_skill.md`) add OS-specific prerequisites, compiler setup, `configure`, and `make.inc` edits. This file collects steps that are **the same everywhere**.

Reference this file from any platform skill to avoid duplicating instructions.

---

## Environment variables

Set these in your build directory before cloning:

```bash
export BUILD_ROOT="$PWD"              # e.g. ~/qe_build
export QE_ROOT="$BUILD_ROOT/q-e"
export QEPY_ROOT="$BUILD_ROOT/QEpy"
export VENV_NAME="${VENV_NAME:-venv_qepy}"
export VENV_DIR="$BUILD_ROOT/$VENV_NAME"
```

**Agent instruction:** ask the user for `VENV_NAME` if not provided. Default: `venv_qepy`.

---

## Clone Quantum ESPRESSO 7.2

```bash
mkdir -p "$BUILD_ROOT"
cd "$BUILD_ROOT"

git clone \
  --branch qe-7.2 \
  --single-branch \
  https://gitlab.com/QEF/q-e.git \
  "$QE_ROOT"

cd "$QE_ROOT"
git submodule update --init --recursive
git describe --tags --exact-match    # expect: qe-7.2
git rev-parse HEAD                     # record for reproducibility
```

---

## Clone QEpy

If you already have the QEpy repository (e.g. you are reading skills from a checkout), set `QEPY_ROOT` to that path instead of cloning again.

```bash
cd "$BUILD_ROOT"

git clone https://github.com/Quantum-MultiScale/QEpy.git "$QEPY_ROOT"
cd "$QEPY_ROOT"
git checkout dev
git rev-parse HEAD
```

---

## Python virtual environment

Create (if missing):

```bash
cd "$BUILD_ROOT"
# Use Python from your platform skill (e.g. python3.10, python3.11)
"$PYTHON" -m venv "$VENV_DIR"
```

Or source the shared check script after setting `VENV_DIR` and `CC`:

```bash
source "$QEPY_ROOT/skills/check_qepy_venv.sh"   # or path to your QEpy clone
check_qepy_venv || exit 1
```

Install build dependencies:

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
python -m pip show f90wrap
meson --version
ninja --version
```

---

## Build all of Quantum ESPRESSO

Platform skill must be followed for `configure` and `make.inc` **before** this step.

**macOS:** if you wrote `$BUILD_ROOT/env.sh` in the platform skill (§7), run `source "$BUILD_ROOT/env.sh"` at the start of this step — and in **every new shell session** before `make`. Compiler exports do not persist across terminals.

```bash
cd "$QE_ROOT"

make clean || true
find . -name '*.o' -delete
find . -name '*.mod' -delete
find . -name '*.a' -delete

make all
```

Do **not** build only `pw.x`. QEpy requires objects and modules from:

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

Verify:

```bash
find "$QE_ROOT/atomic" -name 'ld1inc.mod'
test -f "$QE_ROOT/GWW/minpack/dpmpar.o"
ls "$QE_ROOT/CPV/src/"*.o | head -3
"$QE_ROOT/bin/pw.x" < /dev/null 2>&1 | head -3
```

---

## Build and install QEpy

**macOS:** `source "$BUILD_ROOT/env.sh"` first; add the `gmake` → `make` shim before `pip install` (see `qe72_qepy_macos_accelerate_skill.md` §11).

```bash
source "$VENV_DIR/bin/activate"
check_qepy_venv 2>/dev/null || true

cd "$QEPY_ROOT"
rm -rf build dist
rm -rf qepy.egg-info 2>/dev/null || true

qedir="$QE_ROOT" \
python -m pip install \
  --no-build-isolation \
  --no-cache-dir \
  -v .
```

`--no-build-isolation` ensures the venv provides `f90wrap==0.2.14`, `meson`, and `ninja`.

Expected completion:

```text
Successfully built qepy
Successfully installed qepy-...
```

---

## Test QEpy (mandatory procedure)

**Do not** run imports from inside `$QEPY_ROOT` — the source tree shadows the installed package.

```bash
source "$VENV_DIR/bin/activate"
cd /tmp

python -c "import qepy; print(qepy.__file__)"
python -c "import qepy; import qepy.qepylibs; print('QEpy import successful')"
```

`qepy.__file__` must be under `$VENV_DIR/.../site-packages/`.

---

## Full success check

See [`README.md`](README.md#success-criteria) for platform-specific BLAS verification (`otool` on macOS, `ldd` on Linux).

---

## Shared scripts

| Script | Purpose |
|--------|---------|
| [`check_qepy_venv.sh`](check_qepy_venv.sh) | Source and run `check_qepy_venv` |
| [`preflight_macos.sh`](preflight_macos.sh) | macOS toolchain check before building |
