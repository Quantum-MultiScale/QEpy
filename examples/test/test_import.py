from pathlib import Path
from importlib import import_module
import qepy

def test_import_qepylibs():
    a = Path(qepy.__file__).parent / 'qepylibs'
    so = a.glob('*.so')
    for b in so:
        f = b.name.split('.')[0]
        try:
            p = import_module(f)
        except Exception as e:
            print(f)
            raise e

if __name__ == "__main__":
    tests = [item for item in globals() if item.startswith('test_')]
    for func in sorted(tests):
        globals()[func]()
