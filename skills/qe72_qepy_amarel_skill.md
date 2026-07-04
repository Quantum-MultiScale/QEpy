# Skill: Build Quantum ESPRESSO 7.2 and QEpy on Amarel (Rutgers HPC)

**Environment type:** HPC cluster — **no `sudo`**, only pre-loaded modules (`module load intel/18.0.5`), SLURM batch jobs, and user-space builds under `$HOME`.

## Which skill to use

| Goal | Skill file |
|------|------------|
| **Amarel / HPC cluster (no sudo)** | `qe72_qepy_amarel_skill.md` (this file) |
| **RHEL 9 VM with sudo + oneAPI installer** | `qe72_qepy_rhel9_intel_skill.md` |
| Generic RHEL 9 HPC (no sudo) | `qe72_qepy_rhel9_intel_skill.md` §16 + this file as a worked example |

**Do not** use the generic RHEL 9 Intel skill on Amarel without reading this file. Amarel has site-specific modules, SLURM layout, and known toolchain quirks.

**Agent instruction:** SSH to **`amarel-new.hpc.rutgers.edu`** (RHEL 9.6 head node). Do **not** build or run on the legacy CentOS 7 login node (`amarel.rutgers.edu`). Submit all builds and tests to **`main-redhat`** compute nodes via SLURM. Use **`--exclusive`** when possible; check `sinfo` and avoid **`mix`** nodes if not using exclusive.

---

## Purpose

Reproducible build of:

- Quantum ESPRESSO tag `qe-7.2`
- QEpy from the `dev` branch
- **Intel Parallel Studio 18** (`module load intel/18.0.5`): `ifort`, `mpiifort`, MKL 18
- **gcc** for C code (not `icc` — too old for RHEL 9 glibc headers)
- System **Python 3.9** venv with **`--copies`** (never conda/miniforge for QEpy)
- Local FFTW build (no system FFTW on compute nodes)

Validated on Amarel July 2026: `pw.x` Gaussian smearing + QEpy pytest (`test_pwscf.py`, `test_readfile.py`) **4/4 passed**.

---

## Amarel-specific facts

| Topic | Detail |
|-------|--------|
| Head node | `amarel-new.hpc.rutgers.edu` — RHEL 9.6, has `python3-devel` |
| Legacy login | `amarel.rutgers.edu` — CentOS 7, **cannot run** modern binaries |
| Compute partition | `main-redhat` — RHEL 9.6 |
| Intel stack | `module load intel/18.0.5` (includes MKL + Intel MPI 2018). **Do not** also load `intel_mkl` — it conflicts |
| C compiler | `gcc` / `g++` from OS; set `I_MPI_CC=gcc`, `I_MPI_CXX=g++` |
| Fortran | `ifort`, `mpiifort` from `intel/18.0.5` |
| Launch MPI jobs | **`srun --mpi=pmi2 -n N`** for multi-rank; **`srun -n 1`** for serial. **`mpirun`/`mpiexec` segfault** on RHEL 9. Plain **`srun -n 2` without `--mpi=pmi2`** fails at `PMI_KVS_Get` because SLURM `MpiDefault=none` |
| Python | `/usr/bin/python3.9` only on compute; **no conda** for QEpy |
| Python headers | **Not installed on compute nodes** — copy from head node to `~/qe_build/python39/` |
| `git` | Not on compute — use a `fakebin/git` stub for `./configure` |
| Home NFS cache | Compute nodes may see **stale venv symlinks** — use `python3.9 -m venv --copies` in a **new directory** (`venv_py39`) |
| SLURM | Prefer `#SBATCH --exclusive`; `#SBATCH --mem=0` uses full node RAM |

---

# 1. SSH and layout

```bash
ssh USER@amarel-new.hpc.rutgers.edu
export BUILD_ROOT=$HOME/qe_build
mkdir -p "$BUILD_ROOT"
```

Recommended layout:

```text
~/qe_build/
  q-e/              QE 7.2 (tag qe-7.2)
  QEpy/             dev branch
  fftw-nomp/        local FFTW 3.3.10 (no OpenMP)
  venv_py39/        Python 3.9 venv (--copies, system python)
  python39/         copied include + pkgconfig for compute QEpy builds
  fakebin/git       stub for configure
  env_amarel.sh     environment (source inside batch jobs)
  full_rebuild_qepy.sh   end-to-end SLURM script (optional)
```

---

# 2. Load modules (batch script or interactive on compute)

```bash
source /etc/profile.d/modules.sh
module load intel/18.0.5

export CC=gcc CXX=g++ FC=ifort F90=ifort
export I_MPI_CC=gcc I_MPI_CXX=g++ I_MPI_FC=ifort I_MPI_F77=ifort
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
ulimit -s unlimited
```

Verify:

```bash
which gcc ifort mpiifort
ifort --version | head -1
echo "MKLROOT=$MKLROOT"
```

---

# 3. Fake `git` (compute nodes lack git)

```bash
mkdir -p "$BUILD_ROOT/fakebin"
cat > "$BUILD_ROOT/fakebin/git" <<'EOF'
#!/bin/bash
case "$1" in
  rev-parse) echo HEAD; exit 0 ;;
  describe) echo qe-7.2; exit 0 ;;
  submodule) exit 0 ;;
esac
exit 0
EOF
chmod +x "$BUILD_ROOT/fakebin/git"
export PATH="$BUILD_ROOT/fakebin:$PATH"
```

---

# 4. Build FFTW (on head node or compute)

```bash
FFTW_ROOT="$BUILD_ROOT/fftw-nomp"
cd "$BUILD_ROOT"
curl -LO https://www.fftw.org/fftw-3.3.10.tar.gz
tar xzf fftw-3.3.10.tar.gz && mv fftw-3.3.10 fftw-build && cd fftw-build
./configure --prefix="$FFTW_ROOT" --enable-shared --disable-fortran --enable-threads=no
make -j$(nproc) && make install
test -f "$FFTW_ROOT/include/fftw3.f03" || test -f "$FFTW_ROOT/include/fftw3.h"
```

---

# 5. Clone QE and QEpy

On the **head node** (has git):

```bash
cd "$BUILD_ROOT"
git clone https://gitlab.com/QEF/q-e.git q-e
cd q-e && git checkout qe-7.2 && git submodule update --init --recursive

cd "$BUILD_ROOT"
git clone https://github.com/Quantum-MultiScale/QEpy.git
cd QEpy && git checkout dev
```

---

# 6. Python venv (system Python, NOT conda)

**On the head node** (`amarel-new`), where `python3-devel` exists:

```bash
/usr/bin/python3.9 -m venv --copies "$BUILD_ROOT/venv_py39"
source "$BUILD_ROOT/venv_py39/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install "numpy<2" "f90wrap==0.2.14" meson ninja packaging pytest pytest-mpi ase
deactivate
```

Copy Python headers for **compute-node QEpy builds**:

```bash
mkdir -p "$BUILD_ROOT/python39/include" "$BUILD_ROOT/python39/lib/pkgconfig"
cp -r /usr/include/python3.9 "$BUILD_ROOT/python39/include/"
cp /usr/lib64/pkgconfig/python-3.9.pc "$BUILD_ROOT/python39/lib/pkgconfig/"
sed -i "s|prefix=/usr|prefix=$BUILD_ROOT/python39|" "$BUILD_ROOT/python39/lib/pkgconfig/python-3.9.pc"
sed -i 's|includedir=.*|includedir=${prefix}/include/python3.9|' "$BUILD_ROOT/python39/lib/pkgconfig/python-3.9.pc"
```

Verify on a compute node:

```bash
srun --partition=main-redhat --exclusive -n1 --time=00:02:00 \
  "$BUILD_ROOT/venv_py39/bin/python" -c "import sys; print(sys.version); assert 'conda' not in sys.version.lower()"
```

---

# 7. Configure and build QE (submit to SLURM)

Create `~/qe_build/full_rebuild_qepy.sh` or use the script on the cluster. Key points:

1. **W90 symlink** before any w90 target: `ln -sf wannier90-3.1.0 W90`
2. **Configure** with `mpiifort`, `mkl_intel_lp64`, external FFTW
3. **Fix `make.inc`** — critical on Amarel:

```bash
mi="$BUILD_ROOT/q-e/make.inc"
MKLLIB="$MKLROOT/lib/intel64"
FFTW_ROOT="$BUILD_ROOT/fftw-nomp"

sed -i "s|^DFLAGS.*|DFLAGS         = -D__MPI -D__FFTW3 -D__INTEL -D__PARA|" "$mi"
sed -i "s|^FFLAGS.*|FFLAGS = -fPIC -O1 -assume byterecl -fpp|" "$mi"
sed -i "s|^CFLAGS.*|CFLAGS = -O2 -fPIC \$(DFLAGS) \$(IFLAGS)|" "$mi"
sed -i "s|^IFLAGS.*|IFLAGS = -I. -I\$(TOPDIR)/include -I$FFTW_ROOT/include -I$MKLROOT/include|" "$mi"
sed -i "s|^FFT_LIBS.*|FFT_LIBS = -L$FFTW_ROOT/lib -lfftw3|" "$mi"
sed -i "s|^LDFLAGS.*|LDFLAGS = -L$FFTW_ROOT/lib -Wl,-rpath,$FFTW_ROOT/lib -L$MKLLIB -Wl,-rpath,$MKLLIB|" "$mi"
sed -i "s|^BLAS_LIBS.*|BLAS_LIBS = -L$MKLLIB -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lpthread -lm|" "$mi"
sed -i "s|^LAPACK_LIBS.*|LAPACK_LIBS =|" "$mi"
```

4. **Build order** (avoids W90 race and header races):

```bash
cd "$BUILD_ROOT/q-e"
rm -f install/configure-w90 install/make-w90
make -j1 w90
make -j1 mods
make -j8 all
```

SLURM header example:

```bash
#SBATCH --job-name=qe-qepy
#SBATCH --partition=main-redhat
#SBATCH --exclusive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=0
#SBATCH --time=03:00:00
```

---

# 8. Test `pw.x`

Amarel SLURM has **`MpiDefault=none`**: multi-rank jobs must use **`srun --mpi=pmi2`**, not plain `srun -n N` and not `mpirun`/`mpiexec` (those segfault on RHEL 9).

```bash
mkdir -p "$BUILD_ROOT/test_run/DATA"
cp "$BUILD_ROOT/QEpy/examples/test/DATA/"* "$BUILD_ROOT/test_run/DATA/"
cd "$BUILD_ROOT/test_run"

# serial (1 rank)
srun -n 1 "$BUILD_ROOT/q-e/bin/pw.x" -i DATA/qe_in.in </dev/null | tail -5

# parallel (2 ranks) — note --mpi=pmi2
srun --mpi=pmi2 -n 2 "$BUILD_ROOT/q-e/bin/pw.x" -i DATA/qe_in.in </dev/null | tail -5
# expect: JOB DONE
```

---

# 9. Build and test QEpy

Inside the same SLURM job (compute node):

```bash
export qedir="$BUILD_ROOT/q-e"
export C_INCLUDE_PATH="$BUILD_ROOT/python39/include/python3.9"
export PKG_CONFIG_PATH="$BUILD_ROOT/python39/lib/pkgconfig:$BUILD_ROOT/venv_py39/lib/pkgconfig"
export PATH="$BUILD_ROOT/venv_py39/bin:$PATH"
unset MAKEFLAGS

PY="$BUILD_ROOT/venv_py39/bin/python"
cd "$BUILD_ROOT/QEpy" && rm -rf build qepy.egg-info
MAX_JOBS=4 qedir="$BUILD_ROOT/q-e" "$PY" -m pip install --no-build-isolation .

cd "$BUILD_ROOT/QEpy/examples/test"

# Serial
srun -n 1 "$PY" -m pytest -v --tb=line test_pwscf.py test_readfile.py

# Parallel (2 MPI ranks) — must use --mpi=pmi2 on Amarel; do NOT use mpirun here
srun --mpi=pmi2 -n 2 --export=ALL "$PY" -m pytest --with-mpi -v --tb=line test_pwscf.py test_readfile.py
```

Validated job **57845416** (exclusive): 4/4 parallel tests passed in **2.14 s** vs **~8 s** serial.

---

# 10. Environment script (`env_amarel.sh`)

Source inside batch jobs on compute nodes:

```bash
source /etc/profile.d/modules.sh
module load intel/18.0.5

export BUILD_ROOT="${BUILD_ROOT:-$HOME/qe_build}"
export PATH="$BUILD_ROOT/fakebin:$BUILD_ROOT/venv_py39/bin:$PATH"

export CC=gcc CXX=g++ FC=ifort F90=ifort
export I_MPI_CC=gcc I_MPI_CXX=g++ I_MPI_FC=ifort I_MPI_F77=ifort
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
ulimit -s unlimited

export qedir="$BUILD_ROOT/q-e"
export C_INCLUDE_PATH="$BUILD_ROOT/python39/include/python3.9"
export PKG_CONFIG_PATH="$BUILD_ROOT/python39/lib/pkgconfig:${PKG_CONFIG_PATH:-}"

# Launch QE with srun (mpirun from Intel MPI 2018 is broken on RHEL 9)
alias pw.x='srun -n 1 "$BUILD_ROOT/q-e/bin/pw.x"'
```

---

# 11. Verification checklist

```bash
# After QE build (on compute via srun or batch)
test -x "$BUILD_ROOT/q-e/bin/pw.x"
grep -q '\-fPIC' "$BUILD_ROOT/q-e/make.inc"

# pw.x smoke (Gaussian smearing input from QEpy tests)
cd "$BUILD_ROOT/test_run"
srun -n 1 "$BUILD_ROOT/q-e/bin/pw.x" -i DATA/qe_in.in </dev/null | grep -q "JOB DONE"

# QEpy (from /tmp to avoid shadowing source tree)
source "$BUILD_ROOT/venv_py39/bin/activate"
cd /tmp && python -c "import qepy; print(qepy.__file__)"
# path must be under venv_py39/site-packages, not QEpy source

# pytest
cd "$BUILD_ROOT/QEpy/examples/test"
python -m pytest -v test_pwscf.py test_readfile.py
```

---

# 12. Common failures on Amarel

| Symptom | Cause | Fix |
|---------|-------|-----|
| `mpirun` / `mpiexec` segfault at `MPI_Init` | Intel MPI 2018 Hydra on RHEL 9 | Use **`srun --mpi=pmi2 -n N`**, not mpirun |
| `PMI_KVS_Get returned -1` with `srun -n 2` | SLURM `MpiDefault=none` — no PMI unless requested | Add **`--mpi=pmi2`** to srun |
| `icc` / `floatn-common.h` errors | icc 18 vs RHEL 9 headers | Use **`gcc`** for C |
| `qe_cdefs.h` not found during build | CFLAGS missing `$(IFLAGS)` | Fix `make.inc` §7 |
| `recompile with -fPIC` during QEpy | FFLAGS without `-fPIC` | Add `-fPIC` to FFLAGS, rebuild mods/pw |
| `Python dependency not found` (Meson) | No Python.h on compute | Copy headers to `~/qe_build/python39/` |
| `meson: command not found` | venv not on PATH | `export PATH=$BUILD_ROOT/venv_py39/bin:$PATH` |
| venv shows conda on compute | Stale NFS cache of old venv | New venv with **`--copies`** in `venv_py39` |
| W90 / `configure-w90` errors | Missing symlink | `ln -sf wannier90-3.1.0 W90` before `make w90` |
| QEpy + conda | Meson/compiler flag conflicts | **Never** use miniforge/conda for QEpy |
| Slow/hung jobs on shared nodes | Noisy neighbors | `#SBATCH --exclusive`; avoid `mix` in `sinfo` |
| `srun -n 2` / `PMI_KVS_Get -1` / rc=15 | SLURM `MpiDefault=none` without PMI | Add **`--mpi=pmi2`** to srun |
| Duplicate `collecting ...` lines under parallel | Both ranks run pytest collector | Expected with `--with-mpi`; use `if driver.is_root` for QE output |

---

# 13. Testing on Amarel

Run inside an **exclusive** SLURM job on `main-redhat` after sourcing `env_amarel.sh`.

**Serial:**

```bash
cd "$BUILD_ROOT/QEpy/examples/test"
srun -n 1 --export=ALL python -m pytest -v --tb=line test_pwscf.py test_readfile.py
```

**Parallel (2 MPI ranks):**

```bash
srun --mpi=pmi2 -n 2 --export=ALL python -m pytest --with-mpi -v --tb=line test_pwscf.py test_readfile.py
```

Do **not** use plain `srun -n 2` (no PMI) or `mpirun`/`mpiexec` on this cluster.

Optional: install `mpi4py` in the venv to silence pytest-mpi warnings (tests pass without it).

---

# 14. Agent notes

- Default venv name on Amarel: **`venv_py39`** (not `venv_qepy`) to avoid stale conda venv cache.
- Community oneAPI modules under `/projects/community/modulefiles` work on some nodes but the **validated stack uses `intel/18.0.5`** from `/opt/sw/modulefiles/Core`.
- Do not run `make distclean` casually — it removes `make.inc` and breaks incremental rebuilds.
- For pytest on Amarel: serial **`srun -n 1`**, parallel **`srun --mpi=pmi2 -n 2 … pytest --with-mpi`** (job 57845416: 4/4 passed in 2.14 s).
