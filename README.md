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

### Source

 - **QE**

	All source codes should be compiled with the `-fPIC` compuiler option. Add `-fPIC` to the configuration options. E.g.,

     ```shell
	 ./configure CFLAGS=-fPIC FFLAGS=-fPIC try_foxflags=-fPIC
	  make all
	  export qedir=`pwd`
     ```

 - **QEpy**

     ```shell
	 git clone --recurse-submodules https://gitlab.com/shaoxc/qepy.git
     python -m pip install -U ./qepy
	 ```

## Manual and Tutorials
  See [QEpy's website](https://qepy.rutgers.edu) for details.
