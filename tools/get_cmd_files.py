#!/usr/bin/env python
# coding: utf-8

from pathlib import Path
import re
import os
import sys
import configparser

def get_cmd_from_file(filename, path=None, ignore=r'.*test.*', cmds=None):
    pattern = re.compile(r'^\s*(\w+\.x)\s*:')
    pattern_o = re.compile(r'^\s*(\w+\.x)\s*:.*?(\w+)\.o')
    pattern_f = re.compile(r'^\s*(\w+\.x)\s*:.*?(\w+\.f90)')
    ignore = re.compile(ignore)
    if cmds is None:
        given = False
        cmds = {}
    else:
        given = True
        if isinstance(cmds, list): cmds = dict.fromkeys(cmds)
    if path:
        path = Path(path)
    else:
        path = Path(filename).parent
    with open(filename, 'r') as fh:
        for line in fh:
            match = pattern.match(line)
            if match:
                main = match.group(1)
                if ignore.match(main) : continue
                file = None
                m1 = pattern_o.match(line)
                if m1 :
                    file = m1.group(2)+'.f90'
                else:
                    m2 = pattern_f.match(line)
                    if m2 : file = m2.group(2)
                if given:
                    if main not in cmds: continue
                if file:
                    file = path / file
                else:
                    tmpf = (path / main).with_suffix(".f90")
                    if tmpf.is_file(): file = tmpf
                cmds[main] = file
    return cmds


if len(sys.argv) > 1 :
    path = Path(sys.argv[1])
else :
    path = Path(os.environ.get('qedir', '.'))

ignore_folder=['GUI', 'S3DE', 'Doc', 'test-suite', 'external', 'W90']

cmds = dict.fromkeys([item.name for item in (path/'bin').glob('*.x')])

for mf in path.rglob('Makefile'):
    for f in ignore_folder:
        if f in mf.relative_to(path).as_posix():
            break
    else:
        cs = get_cmd_from_file(mf, cmds=cmds)

update_cmds = {
    'pw.x' : 'PW/src/pwscf.f90',
    'manypw.x' : 'PW/src/pwscf.f90',
    'dist.x' : 'PW/src/pwscf.f90',
    'neb.x' : 'NEB/src/neb.f90',
    'pwcond.x' : 'PWCOND/src/condmain.f90',
}
ignore_cmds = ['iotk.x', 'iotk_print_kinds.x']
for k, v in update_cmds.items():
    cmds[k] = path / v
for k in ignore_cmds:
    cmds.pop(k, None)

not_found = [k for k,v in cmds.items() if v is None]
if not_found:
    print(f'!WARN: {len(not_found)} files not found: "{" ".join(not_found)}"')

# remove path
for k in list(cmds.keys()):
    v = cmds[k]
    if v is None:
        print(f'!WARN: {k} not found')
        cmds.pop(k)
        continue
    cmds[k] = v.relative_to(path)

config = configparser.ConfigParser()
config['CMD'] = dict(sorted(cmds.items(), key=lambda x:x[1]))
with open('qepy_qex.ini', 'w') as fh:
    config.write(fh)
