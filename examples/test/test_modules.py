import re
from importlib import import_module
import qepy.driver

optional=['qepy_cetddft']

def test_modules():
    file = qepy.driver.__file__
    pattern = re.compile(r'^\s*(qepy_.*?\..+?)\(')

    attrs = []
    with open(file, 'r') as fh:
        for line in fh:
            m = pattern.findall(line)
            attrs.extend(m)

    missing = []
    errors = []
    for item in attrs:
        l = item.split('.')
        try:
            mod = import_module('.'.join(l[:-1]))
        except Exception as e:
            if l[0] not in optional:
                errors.append(item)
                # raise e
            continue
        if not hasattr(mod, l[-1]):
            missing.append(item)

    if len(errors)>0:
        print('Modules are not found:\n', '\n'.join(errors))
    if len(missing)>0:
        print('Following modules are not found:\n', '\n'.join(missing))
        raise AttributeError('Some modules are not found', len(missing))


if __name__ == "__main__":
    tests = [item for item in globals() if item.startswith('test_')]
    for func in sorted(tests):
        globals()[func]()
