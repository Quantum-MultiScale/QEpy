import os
import types
import sys
from functools import wraps
import pkgutil
import operator
from importlib import import_module
from ctypes import util, CDLL, RTLD_LOCAL, RTLD_GLOBAL
import subprocess
from pathlib import Path
import platform

def find_library(name):
    if hasattr(util, '_findLib_ld') and hasattr(util, '_get_soname') :
        lib = util._get_soname(util._findLib_ld(name))
    else :
        lib = util.find_library(name)
    return lib

def load_library(lib=None, name=None):
    if lib and '.' not in lib: name = lib
    if name is not None: lib = find_library(name)
    if lib is None: raise AttributeError("Please provide a library name")
    try:
        cdll = CDLL(lib, RTLD_LOCAL | RTLD_GLOBAL)
    except Exception :
        cdll = None
    return cdll


class Logger(type):
    def __new__(cls, name, bases, attrs):

        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, types.FunctionType):
                attrs[attr_name] = cls.stdout2file(attr_value)

        return super().__new__(cls, name, bases, attrs)

    @staticmethod
    def stdout2file(function, fileobj = None):
        return stdout2file(function, fileobj=fileobj)

    @staticmethod
    def print2file(fileobj = None):
        return print2file(fileobj=fileobj)

def print2file(fileobj = None):
    def decorator(function):
        return stdout2file(function, fileobj=fileobj)
    return decorator

def stdout2file(function, fileobj = None):
    @wraps(function)
    def wrapper(*args, **kwargs):
        fobj = fileobj
        if not fobj :
            if len(args) > 0 and hasattr(args[0], 'fileobj'): fobj = args[0].fileobj
        stdout = None
        if fobj is not None and not fobj.closed :
            if os.fstat(1).st_ino != os.fstat(fobj.fileno()).st_ino :
                stdout = os.dup(1)
                os.dup2(fobj.fileno(), 1)
        results = function(*args, **kwargs)
        if stdout is not None :
            os.dup2(stdout, 1)
            os.close(stdout)
        return results
    return wrapper

def qepy_clean_saved(module=None):
    if module is None:
        l = [v for key, v in sys.modules.items() if key.startswith('qepy_') and '.' not in key]
        for module in l:
            qepy_clean_saved(module=module)
    mods = [name for _, name, _ in pkgutil.iter_modules(module.__path__)]
    for mod in mods :
        if hasattr(module, mod):
            for item in ['_arrays', '_objs'] :
                if hasattr(operator.attrgetter(mod)(module), item):
                    attr = mod + '.' + item
                    operator.attrgetter(attr)(module).clear()


env = {
    'LOGFILE' : None, # The screen output of QE.
    'STDOUT' : None,  # file descriptor of output
    'STDIN' : None,  # file descriptor of input
    'STDIN_SAVE' : None,  # The saved screen input of QE.
    'DRIVER' : None, # save the instance of driver class
}

qepylibs = [
    'qepy_atomic',
    'qepy_cetddft',
    'qepy_cpv',
    'qepy_dft_d3',
    'qepy_fftxlib',
    'qepy_gww_bse',
    'qepy_gww_gww',
    'qepy_gww_head',
    'qepy_gww_minpack',
    'qepy_gww_pw4gww',
    'qepy_gww_simple',
    'qepy_gww_simple_bse',
    'qepy_gww_simple_ip',
    'qepy_hp',
    'qepy_kcw',
    'qepy_kcw_pp',
    'qepy_ks_solvers',
    'qepy_laxlib',
    'qepy_lr_modules',
    'qepy_mbd',
    'qepy_modules',
    'qepy_neb',
    'qepy_phonon_gamma',
    'qepy_phonon_ph',
    'qepy_pioud',
    'qepy_pp',
    'qepy_pw',
    'qepy_pwcond',
    'qepy_tddfpt',
    'qepy_upflib',
    'qepy_utilxlib',
    'qepy_xclib',
    'qepy_xspectra',
]

class QEpyLibs(type):
    def __getattr__(cls, attr):
        if attr.startswith('qepy_'):
            # TODO: replace the package by subpackage
            p = import_module(attr)
            return p
        else :
            return object.__getattribute__(cls, attr)

class QEpyMods:
    def __init__(self, qepymod):
        self.qepymod = qepymod

    def __getattr__(self, attr):
        if attr == 'qepymod' :
            return object.__getattribute__(self, attr)
        else :
            for _, mod in self.qepymod.items() :
                if hasattr(mod, attr):
                    return getattr(mod, attr)
            else:
                raise AttributeError(f"There is no '{attr}' in {list(self.qepymod.keys())}")

    @property
    def qepymod(self):
        if isinstance(self._qepymod, str):
            self._qepymod = {self._qepymod: None}
        elif not isinstance(self._qepymod, dict):
            self._qepymod = dict.fromkeys(self._qepymod)
        for k, v in self._qepymod.items():
            if v is None :
                mod = import_module(k)
                self._qepymod[mod.__name__] = mod
        return self._qepymod

    @qepymod.setter
    def qepymod(self, value):
        self._qepymod = value

def get_dynamic_libraries(filename):
    system = platform.system()
    libraries = []
    try:
        if system == "Linux":
            # Use ldd for Linux
            result = subprocess.run(["ldd", filename], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                parts = line.split("=>")
                if len(parts) == 2:
                    library_path = parts[1].strip().split()[0]
                    libraries.append(library_path)
        elif system == "Darwin":
            # Use otool for macOS
            result = subprocess.run(["otool", "-L", filename], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines()[1:]:  # Skip the first line
                library_path = line.strip().split()[0]
                libraries.append(library_path)
    except:
        libraries = []
    return libraries

def import_mkl_lib(libraries):
    for item in libraries:
        if 'libmkl_core' in item:
            mkl_path = item[:item.rfind('/')+1]
            files = list(Path(mkl_path).glob('libmkl_rt.so*'))
            if files: load_library(lib=str(files[0]))
            break

def import_mpi_lib(libraries):
    for item in libraries:
        if 'libmpi' in item: load_library(lib=item)

def fix_external_lib():
    system = platform.system()
    if system != "Linux": return
    try:
        libqepy_pw_file = Path(__file__).resolve().parent/'qepylibs'/'libqepy_pw.so'
        libraries = get_dynamic_libraries(str(libqepy_pw_file))
        import_mkl_lib(libraries)
        import_mpi_lib(libraries)
    except:
        pass
