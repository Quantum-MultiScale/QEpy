project('qepy',
  ['c', 'fortran'],
  version : '7.2.0',
  meson_version: '>= 1.4.0',
  default_options : [
    'warning_level=1',
    'buildtype=release'
    ])


cc = meson.get_compiler('c')
##
##--> from scipy meson.build
# Adding at project level causes many spurious -lgfortran flags.
add_languages('fortran', native: false)
ff = meson.get_compiler('fortran')
if ff.has_argument('-Wno-conversion')
  add_project_arguments('-Wno-conversion', language: 'fortran')
endif

if host_machine.system() == 'darwin'
  if cc.has_link_argument('-Wl,-ld_classic')
    # New linker introduced in macOS 14 not working yet, see gh-19357 and gh-19387
    add_project_link_arguments('-Wl,-ld_classic', language : ['c', 'cpp', 'fortran'])
  endif
  if cc.has_link_argument('-Wl,-dead_strip')
    # Allow linker to strip unused symbols
    add_project_link_arguments('-Wl,-dead_strip', language : ['c', 'cpp', 'fortran'])
  endif
endif

# Intel compilers default to fast-math, so disable it if we detect Intel
# compilers. A word of warning: this may not work with the conda-forge
# compilers, because those have the annoying habit of including lots of flags
# that are gcc-specific in CFLAGS/CXXFLAGS/FFLAGS, which throws off the
# detection logic below. You have to remove the wrong flags (only `-isystem`
# is actually needed, everything else shouldn't be there).
_intel_cflags = []
_intel_fflags = []
if cc.get_id() in ['intel', 'intel-llvm']
  _intel_cflags += cc.get_supported_arguments('-fp-model=strict')
elif cc.get_id() in ['intel-cl', 'intel-llvm-cl']
  _intel_cflags += cc.get_supported_arguments('/fp:strict')
endif
if ff.get_id() in ['intel', 'intel-llvm']
  _intel_fflags = ff.get_supported_arguments('-fp-model=strict')
  minus0_arg = ['-assume', 'minus0']
  if ff.has_multi_arguments(minus0_arg)
    _intel_fflags += minus0_arg
  endif
elif ff.get_id() in ['intel-cl', 'intel-llvm-cl']
  # Intel Fortran on Windows does things differently, so deal with that
  # (also specify dynamic linking and the right name mangling)
  _intel_fflags = ff.get_supported_arguments(
    '/fp:strict', '/MD', '/names:lowercase', '/assume:underscore',
    '/assume:minus0'
  )
endif
add_project_arguments(_intel_cflags, language: ['c', 'cpp'])
add_project_arguments(_intel_fflags, language: 'fortran')
##<-- END scipy
add_project_arguments('-fPIC', language: 'fortran')
if ff.get_id() in ['intel', 'intel-llvm'] # ifort deprecation warning
  add_project_arguments('-diag-disable=10448', language: 'fortran')
endif
if cc.has_argument('-Wno-typedef-redefinition')
  add_project_arguments('-Wno-typedef-redefinition', language : ['c', 'cpp'])
endif
if cc.has_argument('-Wunused-variable')
  add_project_arguments('-Wunused-variable', language : ['c', 'cpp'])
endif

##--> update variables
qedir = get_option('qedir')
pythonexec = get_option('pythonexec')
libname = get_option('libname')
qepy_link_str = get_option('qepy_link')
qe_link_str = get_option('qe_link')
source_str = get_option('source')
vpath = get_option('vpath')
qepy_link_str = qepy_link_str + ' ' + qe_link_str
##<--
#
py3 = import('python').find_installation(pythonexec, pure: false)
py_dep = py3.dependency()


incdir_numpy = run_command(py3,
  ['-c', 'import numpy; print(numpy.get_include())'],
  check : true
).stdout().strip()

#numpy.f2py.get_include() added after v1.21.1
incdir_f2py = incdir_numpy / '..' / '..' / 'f2py' / 'src'

fortranobject_c = incdir_f2py / 'fortranobject.c'
quadmath_dep = ff.find_library('quadmath', required: false)

source = files([libname+'module.c', fortranobject_c])
source += files(run_command('sh', '-c', 'ls f90wrap_*.f90', check:true).stdout().strip().split('\n'))
link_args = []
qepy_incs_dirs = ['./', '../']

foreach a : qepy_link_str.split()
  link_args += a
endforeach

fs = import('fs')
foreach f : source_str.split()
  foreach path : vpath.split()
    if fs.is_file(path / f)
      source += path /f
    endif
  endforeach
endforeach

qepy_incs_np = include_directories(incdir_numpy, incdir_f2py, qepy_incs_dirs)

# additional_flags

build_target(libname,
  source,
  include_directories: qepy_incs_np,
  dependencies : [py_dep, quadmath_dep],
  link_args : link_args,
  install : true,
  gnu_symbol_visibility : 'default',
  link_language : 'fortran',
  name_prefix : '',
  name_suffix : 'so',
  target_type : 'shared_library',
  )

### write config file
use_pythran = false
dependency_map = {}

compilers = {
  'C': cc,
  #'CPP': cpp,
  #'CYTHON': meson.get_compiler('cython'),
  'FORTRAN': meson.get_compiler('fortran')
}

machines = {
  'HOST': host_machine,
  'BUILD': build_machine,
}

conf_data = configuration_data()

# Set compiler information
foreach name, compiler : compilers
  conf_data.set(name + '_COMP', compiler.get_id())
  conf_data.set(name + '_COMP_LINKER_ID', compiler.get_linker_id())
  conf_data.set(name + '_COMP_VERSION', compiler.version())
  conf_data.set(name + '_COMP_CMD_ARRAY', ', '.join(compiler.cmd_array()))
  conf_data.set(name + '_COMP_ARGS', ', '.join(
      get_option(name.to_lower() + '_args')
    )
  )
  conf_data.set(name + '_COMP_LINK_ARGS', ', '.join(
      get_option(name.to_lower() + '_link_args')
    )
  )
endforeach
# Add `pythran` information if present
if use_pythran
  conf_data.set('PYTHRAN_VERSION', pythran.version())
  conf_data.set('PYTHRAN_INCDIR', incdir_pythran)
endif

# Machines CPU and system information
foreach name, machine : machines
  conf_data.set(name + '_CPU', machine.cpu())
  conf_data.set(name + '_CPU_FAMILY', machine.cpu_family())
  conf_data.set(name + '_CPU_ENDIAN', machine.endian())
  conf_data.set(name + '_CPU_SYSTEM', machine.system())
endforeach

conf_data.set('CROSS_COMPILED', meson.is_cross_build())

# Python information
conf_data.set('PYTHON_PATH', py3.full_path())
conf_data.set('PYTHON_VERSION', py3.language_version())

# Dependencies information
foreach name, dep : dependency_map
  conf_data.set(name + '_NAME', dep.name())
  conf_data.set(name + '_FOUND', dep.found())
  if dep.found()
    conf_data.set(name + '_VERSION', dep.version())
    conf_data.set(name + '_TYPE_NAME', dep.type_name())
    conf_data.set(name + '_INCLUDEDIR', dep.get_variable('includedir', default_value: 'unknown'))
    conf_data.set(name + '_LIBDIR', dep.get_variable('libdir', default_value: 'unknown'))
    conf_data.set(name + '_OPENBLAS_CONFIG', dep.get_variable('openblas_config', default_value: 'unknown'))
    conf_data.set(name + '_PCFILEDIR', dep.get_variable('pcfiledir', default_value: 'unknown'))
  endif
endforeach

if libname == 'libqepy_utilxlib'
# QE information
  qe_conf_log = qedir / 'install' / 'config.log'
  if fs.is_file(qe_conf_log)
    qe_conf = run_command('awk',
      '/\$/{ $1=$2=""; sub(/^ */, ""); print $0; exit}',
      qe_conf_log,
      check: true).stdout().strip()
  else
    qe_conf = 'CFLAGS=-fPIC FFLAGS=-fPIC'
  endif

  conf_data.set('QE_PATH', qedir)
  conf_data.set('QE_LINK', ', '.join(qe_link_str.split()))
  conf_data.set('QE_CONF', ', '.join(qe_conf.split()))

  config_py = '__config__.py'
  configure_file(
    input: config_py + '.in',
    output: config_py,
    configuration : conf_data,
    #install_dir: meson.project_source_root(),
    #install_tag: 'python-runtime',
    )
endif
