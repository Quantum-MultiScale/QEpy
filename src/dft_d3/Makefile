QESRC_DIR = dft-d3
PNAME = qepy_dft_d3
QEPY_LIBS = -L$(PYBUILDDIR) -lqepy_modules -lqepy_utilxlib -lqepy_laxlib
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) -I$(PYBUILDDIR)/modules -I$(QEDIR)/Modules -I$(PYBUILDDIR)/utilxlib -I$(QEDIR)/UtilXlib -I$(PYBUILDDIR)/laxlib -I$(QEDIR)/LAXlib

QEPY_OBJS = 

QEPY_PROG_OBJS = 

QE_OBJS = 

LIB_OBJS_TEMP = api.o \
common.o \
core.o \
dftd3_qe.o \
pars.o \
sizes.o

include ../make.qepy.inc
include ../make.depend
