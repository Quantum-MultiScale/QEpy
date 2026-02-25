import os
import sys
import subprocess
from pathlib import Path
import shutil

from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext

name = 'qepy'
qe_branch = 'qe-7.2'

class MakeBuild(build_ext):
    def run(self):
        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        print('build_extension: ', ext, flush=True)
        topdir = Path('.')
        build_args = ' '
        env = os.environ
        self.build_name = Path(self.build_lib) / name
        self.build_path = Path(self.build_temp)
        env['PYTHON'] = sys.executable

        try:
            import multiprocessing as mp
            nprocs = max(mp.cpu_count()//2, 2)
        except ImportError:
            nprocs = 4
        build_args += ' -j ' + str(nprocs)

        if env.get('qepydev', 'no').lower() == 'yes' :
            print("Keep the previous compiled files", flush = True)
        else :
            if self.build_path.is_dir(): shutil.rmtree(self.build_temp)
            shutil.copytree(topdir / 'src', self.build_temp)

        # install the QE
        qedir = env.get('qedir', '')
        if not qedir :
            qedir = self.build_temp + '/q-e'
            qe_download = "git clone -b " + qe_branch + " --depth=1 https://gitlab.com/QEF/q-e.git "+ qedir
            subprocess.check_call(qe_download, env = env, shell=True, text=True)
            if '-fPIC' not in env.get('CFLAGS', ''):
                env['CFLAGS'] = '-fPIC ' + env.get('CFLAGS', '')
            if '-fPIC' not in env.get('FFLAGS', ''):
                env['FFLAGS'] = '-fPIC ' + env.get('FFLAGS', '')
            if '-fPIC' not in env.get('try_foxflags', ''):
                env['try_foxflags'] = '-fPIC ' + env.get('try_foxflags', '')
            # blas and lapack
            if 'BLAS_LIBS' not in env : env['BLAS_LIBS'] = '-lblas'
            if 'LAPACK_LIBS' not in env : env['LAPACK_LIBS'] = '-llapack'
            qe_install_flags = env.get('QE_INSTALL_FLAGS', '')
            print('env', env, flush=True)
            print('build_args', build_args, flush=True)
            res = subprocess.run("./configure " + qe_install_flags, cwd=qedir, env = env, shell=True, capture_output=True, text=True)
            if res.returncode > 0 :
                print('Some errors happened in configure...', flush=True)
                print(res.stderr, flush=True)
                subprocess.run("cat install/config.log", cwd=qedir, env = env, shell=True)
                raise RuntimeError('QE configure failed.')

            res = subprocess.run("make all " + build_args, cwd=qedir, env = env, shell=True, capture_output=True, text=True)
            if res.returncode > 0 :
                print(res.stderr[-100:], flush=True)
                print("'make w90' sometimes will failed at first time, so try again", flush=True)
                res = subprocess.run("make all " + build_args, cwd=qedir, env = env, shell=True, capture_output=True, text=True)
                if res.returncode > 0 :
                    print(res.stderr, flush=True)
                    raise RuntimeError('QE installation failed.')

            env['qedir'] = os.path.abspath(qedir)

        res = subprocess.run('make all ' + build_args, cwd=self.build_temp, env = env, shell=True, capture_output=True, text=True)
        if res.returncode > 0 :
            print("stdout:", res.stdout, flush=True)
            print("stderr:", res.stderr, flush=True)
            raise RuntimeError('QEpy installation failed.')

        if env.get('tddft', 'no').lower() == 'yes' :
            res = subprocess.run('make qepy_cetddft' + build_args, cwd=self.build_temp, env = env, shell=True, capture_output=True, text=True)
            if res.returncode > 0 :
                print("stderr:", res.stderr, flush=True)
                raise RuntimeError('QEpy[cetddft] installation failed.')

        qepylibs = self.build_name / 'qepylibs'
        for f in self.build_path.glob('*.so'):
            shutil.copy2(f, qepylibs)
        for f in self.build_path.glob('qepy_*'):
            if f.is_file():
                shutil.copy2(f, self.build_name)
            else :
                target = qepylibs / f.name
                if target.is_dir(): shutil.rmtree(target)
                shutil.copytree(f, target)
        #
        shutil.copy2(self.build_path / '__config__.py', self.build_name)

def get_version(release=None):
    if release is None:
        with open('pyproject.toml', 'r') as fh:
            for line in fh:
                if line.startswith('version'):
                    release = True
                    break
                elif line.startswith('#version'):
                    release = False
                    break
    if release :
        VERSION = {'version' : None}
    else :
        VERSION = {
                'use_scm_version': {'version_scheme': 'post-release'},
                'setup_requires': ['setuptools_scm']
                }
    return VERSION
VERSION = get_version()


setup(**VERSION,
      packages=find_packages('./'),
      ext_modules = [Extension("qepy._qepy", sources = [])],
      cmdclass={"build_ext" : MakeBuild},
      )
