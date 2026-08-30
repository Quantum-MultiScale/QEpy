QESRC_DIR = GWW/head
PNAME = qepy_gww_head
QEPY_LIBS = -L$(PYBUILDDIR) -lqepy_gww_minpack -lqepy_phonon_ph $(MODS_LR)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) -I$(PYBUILDDIR)/gww_minpack -I$(QEDIR)/GWW/minpack -I$(PYBUILDDIR)/phonon_ph -I$(QEDIR)/PHonon/PH $(INCS_MODS_LR) $(INCS_MODS_LR_QE)

QEPY_OBJS = 

QEPY_PROG_OBJS = head.o

QE_OBJS = 

LIB_OBJS_TEMP = bcast_gwl_input.o \
close_gwl.o \
gwl_readin.o \
lanczos_k.o \
openfilq_gwl.o \
solve_head.o

include ../make.qepy.inc
include ../make.depend
