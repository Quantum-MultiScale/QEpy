__version__ = "7.2.1rc0"
import sys
from pathlib import Path
from importlib import import_module
from importlib.metadata import version # python >= 3.8
from .__config__ import CONFIG, show as show_config
from .core import QEpyMods, fix_external_lib

__all__ = ["show_config"]

# fix the mkl and mpi in linux
fix_external_lib()

path = Path(__file__).resolve().parent/'qepylibs'
sys.path.insert(0, str(path))
__path__.append(str(path))

try:
    __version__ = version("qepy")
except Exception :
    pass

# compatible with older versions API
constants = QEpyMods('qepy_modules.constants')
qepy_common = QEpyMods('qepy_pw.qepy_common')

# TODO: replace the package by subpackage
def __getattr__(pname):
    if pname.startswith('qepy_'):
        p = import_module(pname)
        return p
