# QE 7.2 + QEpy build skills

Step-by-step recipes for a **fresh Quantum ESPRESSO 7.2 build** and a **QEpy install linked to that build**.

These skills are for **source builds**. They are **not** a substitute for `pip install qepy` from PyPI, which uses prebuilt wheels and does not require a local QE tree.

---

## Quick choice

```
What OS?
├── macOS          → qe72_qepy_macos_accelerate_skill.md   (default)
│                    qe72_qepy_macos_mkl_skill.md          (Intel Mac + oneMKL only)
├── Ubuntu         → qe72_qepy_ubuntu_intel_skill.md       (default: Intel MPI + MKL)
│                    qe72_qepy_ubuntu_openblas_skill.md   (open-source: Open MPI + OpenBLAS)
├── RHEL 9 / Rocky / Alma 9
│   ├── VM / workstation (sudo, dnf)  → qe72_qepy_rhel9_intel_skill.md   (Intel MPI + MKL)
│   │                                   qe72_qepy_rhel9_openblas_skill.md (Open MPI + OpenBLAS)
│   └── HPC cluster (no sudo, modules) → site skill, e.g. qe72_qepy_amarel_skill.md
│                                        + rhel9_intel §16 (generic HPC)
└── Amarel (Rutgers HPC)
                   → qe72_qepy_amarel_skill.md            (site: intel/18, SLURM, srun)
```

**If unsure:** Accelerate on macOS; **Intel oneAPI (Intel MPI + MKL) on Linux**. Use OpenBLAS skills only when Intel oneAPI is unavailable or the user explicitly wants an open-source-only stack.

---

## macOS (default path)

| Situation | Skill |
|-----------|--------|
| Any Mac — recommended default | [`qe72_qepy_macos_accelerate_skill.md`](qe72_qepy_macos_accelerate_skill.md) |
| Apple Silicon, native arm64 Homebrew (`/opt/homebrew`, `~/homebrew`) | same |
| Apple Silicon, only `/usr/local` Homebrew (x86_64 / Rosetta) | same (works; binary is not native arm64) |
| Intel Mac with archived Intel oneAPI 2023.x + oneMKL | [`qe72_qepy_macos_mkl_skill.md`](qe72_qepy_macos_mkl_skill.md) |

On macOS, **always set Apple Accelerate explicitly** in `configure` / `make.inc`. Do not rely on automatic BLAS detection.

---

## Linux (default path — bare metal / VM with sudo)

| Situation | Skill |
|-----------|--------|
| **Ubuntu — standard** (Intel MPI + oneMKL) | [`qe72_qepy_ubuntu_intel_skill.md`](qe72_qepy_ubuntu_intel_skill.md) |
| **RHEL 9 / Rocky / Alma — standard** | [`qe72_qepy_rhel9_intel_skill.md`](qe72_qepy_rhel9_intel_skill.md) |
| Ubuntu, no Intel oneAPI / open-source only | [`qe72_qepy_ubuntu_openblas_skill.md`](qe72_qepy_ubuntu_openblas_skill.md) |
| EL9, no Intel oneAPI / open-source only | [`qe72_qepy_rhel9_openblas_skill.md`](qe72_qepy_rhel9_openblas_skill.md) |

Install the [Intel oneAPI Base Toolkit](https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit.html) (MKL + Intel MPI) before using the Intel skills on a **machine where you can run the installer**.

**Exception:** Google Colab and minimal Ubuntu VMs usually lack Intel oneAPI — use the **Ubuntu OpenBLAS** skill there unless you install oneAPI yourself.

## HPC / cluster (no sudo — modules and batch jobs only)

| Situation | Skill |
|-----------|--------|
| **Generic RHEL HPC** (no `dnf`, no installer) | [`qe72_qepy_rhel9_intel_skill.md` §16](qe72_qepy_rhel9_intel_skill.md#16-hpc-clusters-with-environment-modules-no-sudo) |
| **Amarel (Rutgers)** | [`qe72_qepy_amarel_skill.md`](qe72_qepy_amarel_skill.md) |

On HPC: use `module load`, `#SBATCH --exclusive`, and the site MPI launcher (`srun`, etc.). Do **not** run `sudo dnf` or the oneAPI `.sh` installer unless you have admin access.

---

## Pinned versions (all skills)

| Component | Value |
|-----------|--------|
| Quantum ESPRESSO | tag `qe-7.2` |
| QEpy branch | `dev` (record `git rev-parse HEAD` for reproducibility) |
| Fortran compiler | GCC/GFortran **14** (GCC 12 on older Ubuntu 22.04 if 14 unavailable) |
| Python | 3.10–3.12 (3.10 on macOS skill; 3.11+ on Linux skills) |
| QEpy build deps | `f90wrap==0.2.14`, `meson`, `ninja`, `numpy<2` |
| Virtual env name | user choice; default **`venv_qepy`** |

---

## Before you start

1. Install OS prerequisites from the chosen skill (Homebrew, `apt`, or `dnf`).
2. Pick **one** compiler/MPI/BLAS stack and use it consistently.
3. Choose a **build directory** (e.g. `~/qe_build`) with enough disk (~5–10 GB for a full QE build).
4. Tell your installer or AI assistant the **venv name** if not using `venv_qepy`.

**macOS:** run [`preflight_macos.sh`](preflight_macos.sh) before a long build to check Homebrew, compilers, and which skill to use.

**All platforms:** shared clone/build/test steps are in [`common.md`](common.md). Virtualenv checks: [`check_qepy_venv.sh`](check_qepy_venv.sh).

**Agents:** read [`../AGENTS.md`](../AGENTS.md) before executing a skill.

---

## Success criteria

After following a skill, all of these should pass (adjust paths and tools for your OS):

```bash
export QE_ROOT="$BUILD_ROOT/q-e"   # your QE clone

# QE built completely (not only pw.x)
test -f "$QE_ROOT/GWW/minpack/dpmpar.o"
find "$QE_ROOT/atomic" -name 'ld1inc.mod' | grep -q .

# Main executable runs
"$QE_ROOT/bin/pw.x" < /dev/null 2>&1 | head -3

# BLAS backend (pick one check)
otool -L "$QE_ROOT/bin/pw.x" | grep -E 'Accelerate|vecLib'   # macOS Accelerate
ldd "$QE_ROOT/bin/pw.x" | grep -E 'openblas|mkl'             # Linux

# QEpy imports from the venv, not the source tree
source "$VENV_DIR/bin/activate"
cd /tmp
python -c "import qepy; import qepy.qepylibs; print(qepy.__file__)"
```

The printed `qepy.__file__` path must lie inside your virtual environment (e.g. `.../venv_qepy/lib/python.../site-packages/`).

---

## Skill files

| File | Platform | MPI | BLAS/LAPACK | Role |
|------|----------|-----|-------------|------|
| `qe72_qepy_macos_accelerate_skill.md` | macOS | Open MPI (Homebrew) | Apple Accelerate | **macOS default** |
| `qe72_qepy_macos_mkl_skill.md` | Intel macOS | Open MPI (Homebrew) | Intel oneMKL 2023.x | macOS + oneMKL |
| `qe72_qepy_ubuntu_intel_skill.md` | Ubuntu (sudo) | Intel MPI | oneMKL | **Linux VM default** |
| `qe72_qepy_ubuntu_openblas_skill.md` | Ubuntu (sudo) | Open MPI | OpenBLAS | open-source alternative |
| `qe72_qepy_rhel9_intel_skill.md` | RHEL 9 family (sudo) | Intel MPI | oneMKL | **Linux VM default** |
| `qe72_qepy_rhel9_openblas_skill.md` | RHEL 9 family (sudo) | Open MPI | OpenBLAS | open-source alternative |
| `qe72_qepy_amarel_skill.md` | **HPC** (Amarel) | Intel MPI 2018 (`intel/18`) | MKL 18 | Rutgers; no sudo |
| [`common.md`](common.md) | all | — | shared clone / venv / QEpy steps |
| [`env_amarel.sh`](env_amarel.sh) | Amarel | — | SLURM job environment |
| [`preflight_macos.sh`](preflight_macos.sh) | macOS | — | pre-build toolchain check |
| [`check_qepy_venv.sh`](check_qepy_venv.sh) | all | — | venv compatibility function |

---

## Common mistakes

- Building only `pw.x` instead of **`make all`** (QEpy needs atomic, CPV, GWW/minpack, etc.).
- Compiling QE **without `-fPIC`** (QEpy links QE objects into shared libraries).
- Testing `import qepy` **inside the QEpy repository** (local source shadows the install).
- Mixing Homebrew prefixes on macOS (`/usr/local` vs `/opt/homebrew`).
- Mixing OpenBLAS and MKL in the same `make.inc`.
- Using GCC 15 with QE 7.2 (MBD `f_c_string` conflict — use GCC 14).

---

## Reporting issues

When opening a build issue, include:

- OS and skill file used
- `uname -m`, compiler versions, `which mpif90`
- QE commit (`git rev-parse HEAD` in `q-e`)
- QEpy commit on `dev`
- Relevant lines from `make.inc` (`BLAS_LIBS`, `LAPACK_LIBS`, `CC`, `F90`)
