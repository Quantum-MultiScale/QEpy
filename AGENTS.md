# Instructions for AI coding agents

This file guides agents (Cursor, Gemini, Copilot, etc.) that help users build **Quantum ESPRESSO 7.2** and **QEpy from source**.

## Start here

1. Read [`skills/README.md`](skills/README.md) and select **exactly one** skill for the user's OS and stack.
2. **Default choices:**
   - **macOS** → `skills/qe72_qepy_macos_accelerate_skill.md`
   - **Ubuntu / RHEL 9 / Rocky / Alma** → Intel skill (`ubuntu_intel` or `rhel9_intel`)
   - **Colab / no Intel oneAPI** → `skills/qe72_qepy_ubuntu_openblas_skill.md`
3. Use OpenBLAS Linux skills only when Intel oneAPI is **not** installed or the user explicitly wants open-source packages only.
4. Use macOS MKL skill only when the user **explicitly** needs oneMKL on Intel Mac (archived oneAPI 2023.x).

## Before building

- Ask the user for the **Python virtual environment name**. Default: `venv_qepy`.
- Confirm **disk space** and **sudo/apt/brew** access if installing prerequisites.
- On Linux, install Intel oneAPI (MKL + Intel MPI) before building unless using the OpenBLAS fallback skill.
- On macOS, run [`skills/preflight_macos.sh`](skills/preflight_macos.sh) and follow its recommended skill.
- On macOS, run the Homebrew detection loop from the accelerate skill and pick **one** prefix (`/opt/homebrew`, `~/homebrew`, or `/usr/local`).
- Do not mix compiler stacks (e.g. `/usr/local` gcc with `/opt/homebrew` libraries).
- For shared steps (clone, venv, `make all`, QEpy install, test), see [`skills/common.md`](skills/common.md).

## Required workflow

Follow the chosen skill **in order**. Do not skip steps.

| Phase | Requirement |
|-------|-------------|
| QE clone | tag `qe-7.2`, `git submodule update --init --recursive` |
| QE configure | `-fPIC`, explicit BLAS/LAPACK per skill |
| QE build | **`make all`**, not only `pw.x` |
| `make.inc` | Apply all corrections listed in the skill |
| Python venv | Run compatibility checks before QEpy install |
| QEpy install | `qedir="$QE_ROOT" pip install --no-build-isolation .` |
| Test | **`cd /tmp`** then `import qepy; import qepy.qepylibs` |

## Virtual environment

- Set `VENV_NAME` (default `venv_qepy`) and `VENV_DIR="$BUILD_ROOT/$VENV_NAME"`.
- If reusing an existing venv, source [`skills/check_qepy_venv.sh`](skills/check_qepy_venv.sh) and run `check_qepy_venv` (set `CC` and optional `TOOLCHAIN_PREFIX` / `HOMEBREW_PREFIX` on macOS).
- Install build deps in the venv: `numpy<2`, `f90wrap==0.2.14`, `meson`, `ninja`, `packaging`.

## Verification checkpoints

Stop and show output after:

```bash
# Toolchain
"$CC" --version && "$FC" --version
mpif90 --showme:command 2>/dev/null || mpif90 -show 2>/dev/null || true

# After make all
find "$QE_ROOT/atomic" -name 'ld1inc.mod' | head -1
ls "$QE_ROOT/GWW/minpack/dpmpar.o"

# After QEpy install (from /tmp)
python -c "import qepy; print(qepy.__file__)"
```

If a checkpoint fails, fix before continuing.

## Do not

- Use `pip install qepy` from PyPI when the user asked for a **fresh QE-linked source build**.
- Test `import qepy` from inside the QEpy source directory.
- Let `configure` auto-detect BLAS on macOS without setting Accelerate.
- Mix OpenBLAS and MKL in one build.
- Build QE with GCC 15 (use GCC 14 or gcc-toolset-14 / gcc-14).
- Commit or push unless the user asks.

## PyPI install (different path)

If the user only wants a quick install **without** building QE locally:

```bash
python -m pip install qepy
```

See [`README.md`](README.md). That path does not use these skills.

## Success

The build is complete when [`skills/README.md`](skills/README.md) success criteria all pass.
