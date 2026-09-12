QESRC_DIR = GWW/simple_bse
PNAME = qepy_gww_simple_bse
QEPY_LIBS = -L$(PYBUILDDIR) -lqepy_gww_gww $(MODS_BASE)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) -I$(PYBUILDDIR)/gww_gww -I$(QEDIR)/GWW/gww $(INCS_MODS_BASE) $(INCS_MODS_BASE_QE)

SKIPTYPES = 

QEPY_OBJS = 

QEPY_PROG_OBJS = simple_bse.o

QE_OBJS = 

LIB_OBJS_TEMP = build_eemat.o \
derived_object.o \
diago_exc_cg.o \
diago_exc_sd.o \
hamiltonian.o \
input_simple_exc.o \
lanczos.o \
simple_eigen.o \
simple_object.o \
spectrum.o \
start_end.o

include ../make.qepy.inc
include ../make.depend
