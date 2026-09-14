QESRC_DIR = PHonon/Gamma
PNAME = qepy_phonon_gamma
QEPY_LIBS = -L$(PYBUILDDIR) $(MODS_LR)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) $(INCS_MODS_LR) $(INCS_MODS_LR_QE)

SKIPTYPES = 

QEPY_OBJS = 

QEPY_PROG_OBJS = phcg.o

QE_OBJS = 

LIB_OBJS_TEMP = a_h.o \
cg_readin.o \
cg_setup.o \
cgcom.o \
cgsolve.o \
d2ion.o \
dgradcorr.o \
dielec.o \
drhodv.o \
dvb_cc.o \
dvpsi_e.o \
dvpsi_kb.o \
dyndiar.o \
dynmat_init.o \
dynmatcc.o \
find_equiv_sites.o \
generate_dynamical_matrix.o \
generate_effective_charges.o \
h_h.o \
macro.o \
rhod2vkb.o \
solve_e.o \
solve_ph.o \
writedyn.o

include ../make.qepy.inc
include ../make.depend
