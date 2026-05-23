%.fpp : %.f90
	$(FPP) $< > $@

%.o : %.f90
	$(LD) -c $(F2FLAGS) $< -o $@

.PHONY: clean

default: all

BUILDDIR = $(dir $(abspath $(filter %make.qepy.inc,$(MAKEFILE_LIST))))
SRC_DIR  = ./

QEDIR = $(or ${qedir}, ../../../)
qepybackend ?= meson
#
include ${QEDIR}/make.inc
PYTHON := $(or ${PYTHON}, python3)
PYTHONEXEC := $(shell ${PYTHON} -c 'import sys; print(sys.executable)')
UNAME = $(shell uname)
F2FLAGS = $(F90FLAGS) $(QEPY_INCS)

#export LDFLAGS := ${LDFLAGS}
# For the old version numpy (e.g 1.17.3)
export NPY_DISTUTILS_APPEND_FLAGS=1

ifneq ($(findstring ifort, ${F90}),)
   FCOMPILER=intelem
else ifneq ($(findstring ifx, ${F90}),)
   FCOMPILER=intelem
else
   FCOMPILER=gnu95
endif

ifneq ($(findstring -std, ${CFLAGS}), -std)
   CFLAGS += -std=c99
endif


FPP = ${F90} -E -cpp $(F2FLAGS)
F2PY = CFLAGS='$(CFLAGS)' ${PYTHON} ${BUILDDIR}/f90wrap2py.py \
				--fcompiler=$(FCOMPILER) --build-dir . \
				-c --f90exec=$(MPIF90) --f77exec=$(MPIF90) \
				--f90flags='${F2FLAGS}'

export LDFLAGS +=-Wl,-rpath,"$$ORIGIN/:$$ORIGIN/qepy"
export FC := ${MPIF90}
export CC := ${CC}
# turn off the response file of mesonbuild
export MESON_RSP_THRESHOLD := 10000000
#$(info $(LDFLAGS))
#ifeq (${UNAME}, Darwin)
   #export LDFLAGS +=-Wl,-ld_classic
#endif

MODS_BASE = -lqepy_modules \
-lqepy_upflib \
-lqepy_xclib \
-lqepy_fftxlib \
-lqepy_laxlib \
-lqepy_utilxlib \
-lqepy_mbd

MODS_PW = -lqepy_pw -lqepy_ks_solvers -lqepy_dft_d3 $(MODS_BASE)

MODS_LR = -lqepy_lr_modules $(MODS_PW)

INCS_MODS_BASE = -I${BUILDDIR}/modules \
-I${BUILDDIR}/upflib \
-I${BUILDDIR}/xclib \
-I${BUILDDIR}/fftxlib \
-I${BUILDDIR}/laxlib \
-I${BUILDDIR}/utilxlib \
-I${BUILDDIR}/mbd

INCS_MODS_PW = -I${BUILDDIR}/pw -I${BUILDDIR}/ks_solvers -I${BUILDDIR}/dft_d3 $(INCS_MODS_BASE)

INCS_MODS_LR = -I${BUILDDIR}/lr_modules $(INCS_MODS_PW)

INCS_MODS_BASE_QE = -I$(QEDIR)/upflib \
               -I$(QEDIR)/XClib \
               -I$(QEDIR)/Modules \
               -I$(QEDIR)/FFTXlib/src \
			   -I$(QEDIR)/LAXlib \
			   -I$(QEDIR)/UtilXlib \
			   -I$(QEDIR)/MBD \
			    $(FOX_MOD)

INCS_MODS_PW_QE = -I$(QEDIR)/PW/src -I$(QEDIR)/KS_Solvers -I$(QEDIR)/dft-d3 $(INCS_MODS_BASE_QE)

INCS_MODS_LR_QE = -I$(QEDIR)/LR_Modules $(INCS_MODS_PW_QE)

QEPYSRC = ${BUILDDIR}/fix/ ${BUILDDIR}/cmdx/ $(SRC_DIR) ${PLUGIN_DIR}

vpath %.f90 ${QEPYSRC} $(QEDIR)/$(QESRC_DIR)

QEPY_OBJS_NEW = ${QEPY_OBJS} ${QEPY_FIX_OBJS} ${QEPY_PROG_OBJS}
LIB_OBJS = $(addprefix $(QEDIR)/$(QESRC_DIR)/, $(filter-out ${QEPY_OBJS_NEW}, ${LIB_OBJS_TEMP}))

WRAP_OBJS = $(QE_OBJS) $(QEPY_OBJS_NEW)
WRAP_FPP_FILES = $(WRAP_OBJS:%.o=%.fpp)
F90WRAP_FILES = f90wrap_*.f90

ifeq ($(strip $(WRAP_OBJS)),)
QEPY_OBJS_NEW = qepy_fake.o
endif

MESONTMP = _build_dir
CONFIG = __config__.py
#QEPY_OBJS_MESON = $(addprefix ../, $(QEPY_OBJS_NEW))
QEPY_FIELS = $(QEPY_OBJS_NEW:%.o=%.f90)

ifneq ($(qepybackend), meson)
build : ${PNAME} $(QEPY_OBJS_NEW)
	${F2PY} -m lib${PNAME} ${F90WRAP_FILES} $(QEPY_OBJS_NEW) $(LIB_OBJS) $(QEPY_LIBS) ${QELIBS}
else
lib${PNAME}module.c : ${PNAME}
	@${PYTHON} -m f90wrap --f2py-f90wrap -m lib${PNAME} ${F90WRAP_FILES} --lower --quiet

meson.build : lib${PNAME}module.c meson.clean
	@cp ../meson.build .
	@cp ../meson_options.txt .
	meson setup --wipe ${MESONTMP} \
		-Dfortran_args='${F2FLAGS}' \
		-Dc_args='${CFLAGS}' \
		-Dc_link_args='${LDFLAGS}' \
		-Db_lundef=false \
		-Dqedir='${QEDIR}' \
		-Dpythonexec='${PYTHONEXEC}' \
		-Dlibname='lib${PNAME}' \
		-Dqepy_link='$(LIB_OBJS) $(QEPY_LIBS)' \
		-Dqe_link='${QELIBS}' \
		-Dsource='${QEPY_FIELS}' \
		-Dvpath='${QEPYSRC}'

lib$(PNAME).so : meson.build
	meson compile -C ${MESONTMP} --verbose -j 0
	@mv ${MESONTMP}/lib${PNAME}.*so lib$(PNAME).so
	@find ${MESONTMP} -name '*.mod' -exec cp {} . \;
	@if test '${PNAME}' = 'qepy_utilxlib'; then \
		cp ${MESONTMP}/${CONFIG} . ; fi
build : lib$(PNAME).so
endif

${PNAME} : ${WRAP_FPP_FILES}
	@${PYTHON} -m f90wrap --f90wrap -m ${PNAME} --f90-mod-name lib${PNAME} ${WRAP_FPP_FILES} ${CROSS_FPP_FILES} -k $(BUILDDIR)/kind_map.json -P

meson.clean:
	@-rm -f meson*
	@-rm -rf ${MESONTMP}

clean : meson.clean
	@-rm -f ${F90WRAP_FILES} ${WRAP_FPP_FILES}
	@-rm -f *.o *.mod
	@-rm -rf src.* .libs .f2py_f2cmap lib${PNAME}*
	@-rm -rf ${PNAME} ${BUILDDIR}/${PNAME} ${BUILDDIR}/lib${PNAME}.*

all : build
	${PYTHON} ${BUILDDIR}/fix_init_.py $(PNAME)/__init__.py
	@if test '${UNAME}' = 'Darwin'; then \
		install_name_tool -id '@loader_path/lib${PNAME}.so' lib${PNAME}.so; \
	fi
	cp lib$(PNAME).so ${BUILDDIR}/
	if test -d $(PNAME); then cp -r $(PNAME) ${BUILDDIR}/; fi
	if test -f ${CONFIG}; then cp ${CONFIG} ${BUILDDIR}/; fi
