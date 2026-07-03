# QEpy - Quantum ESPRESSO in Python
   `QEpy` turns Quantum ESPRESSO (QE) into a Python DFT engine for nonstandard workflows.

## Contributors and funding
 - [The Quantum-Multiscale collaboration](http://www.quantum-multiscale.org/)
 - Main author: [Xuecheng Shao](mailto:xuecheng.shao@rutgers.edu) (Rutgers)
 - Oliviero Andreussi (UNT), Davide Ceresoli (CNR, Italy), Matthew Truscott (UNT), Andrew Baczewski (Sandia), Quinn Campbell (Sandia), Michele Pavanello (Rutgers)


## Thanks to ...
 - The Quantum ESPRESSO developers for the QE codebase
 - NSF for funding the Quantum-Multiscale collaboration

## Requirements
 - [Quantum ESPRESSO ](https://gitlab.com/QEF/q-e/-/releases/qe-7.2) (==7.2)
 - [Python](https://www.python.org/) (>=3.8)
 - [NumPy](https://docs.scipy.org/doc/numpy/reference/)
 - [f90wrap](https://github.com/jameskermode/f90wrap)
 - Compiler ([GNU](https://gcc.gnu.org/fortran/)(Recommended) or [Intel](https://software.intel.com/content/www/us/en/develop/tools/oneapi/components/fortran-compiler.html))

## Installation
### Pip
   Using pip can easy install the release version (serial) of QEpy from [PyPI](https://pypi.org/project/qepy).

```shell
python -m pip install qepy
```

### Source (with local Quantum ESPRESSO 7.2)

For a full **fresh QE 7.2 + QEpy** build, use the step-by-step skills in [`skills/README.md`](skills/README.md):

| Platform | Default skill |
|----------|----------------|
| **macOS** | [`skills/qe72_qepy_macos_accelerate_skill.md`](skills/qe72_qepy_macos_accelerate_skill.md) |
| **Ubuntu / Debian** | [`skills/qe72_qepy_ubuntu_intel_skill.md`](skills/qe72_qepy_ubuntu_intel_skill.md) |
| **RHEL 9 / Rocky / Alma 9** | [`skills/qe72_qepy_rhel9_intel_skill.md`](skills/qe72_qepy_rhel9_intel_skill.md) |
| **Colab / no Intel oneAPI** | [`skills/qe72_qepy_ubuntu_openblas_skill.md`](skills/qe72_qepy_ubuntu_openblas_skill.md) |

AI assistants should read [`AGENTS.md`](AGENTS.md) before running a skill. On macOS, run `skills/preflight_macos.sh` first. On Linux, install the [Intel oneAPI Base Toolkit](https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit.html) (MKL + Intel MPI) for the default Ubuntu/RHEL skills.

Minimal manual outline (see skills for `make.inc`, compilers, and BLAS/LAPACK):

 - **QE** — clone tag `qe-7.2`, configure with `-fPIC`, **`make all`**, then `export qedir=$(pwd)`.

     ```shell
     git clone --branch qe-7.2 --single-branch https://gitlab.com/QEF/q-e.git q-e
     cd q-e && git submodule update --init --recursive
     ./configure CFLAGS=-fPIC FFLAGS="-fPIC -fallow-argument-mismatch"
     make all
     export qedir="$(pwd)"
     ```

 - **QEpy** — use a dedicated venv and link to the QE tree above:

     ```shell
     git clone -b dev https://github.com/Quantum-MultiScale/QEpy.git
     cd qepy
     python3 -m venv venv_qepy && source venv_qepy/bin/activate
     python -m pip install "numpy<2" "f90wrap==0.2.14" meson ninja packaging
     qedir="$qedir" python -m pip install --no-build-isolation -U .
     ```

## Manual and Tutorials
  See [QEpy's website](https://qepy.rutgers.edu) for details.
