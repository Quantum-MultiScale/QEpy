QESRC_DIR = GWW/minpack
PNAME = qepy_gww_minpack
QEPY_LIBS = -L$(PYBUILDDIR) $(MODS_BASE)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) $(INCS_MODS_BASE) $(INCS_MODS_BASE_QE)

QEPY_OBJS = 

QEPY_PROG_OBJS = 

QE_OBJS = 

LIB_OBJS_TEMP = dpmpar.o \
enorm.o \
fdjac2.o \
lmder.o \
lmder1.o \
lmdif.o \
lmdif1.o \
lmpar.o \
mlagzo.o \
mlegzo.o \
qrfac.o \
qrsolv.o

include ../make.qepy.inc
include ../make.depend
