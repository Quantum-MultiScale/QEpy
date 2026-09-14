PLUGIN_DIR = $(PYBUILDDIR)/ce-tddft/src
PNAME = qepy_cetddft
QEPY_LIBS = -L$(PYBUILDDIR) $(MODS_LR)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) $(INCS_MODS_LR) $(INCS_MODS_LR_QE)

SKIPTYPES = 

QEPY_OBJS = qepy_molecule_optical_absorption.o \
qepy_tddft_common.o \
qepy_tddft_main.o \
qepy_tddft_mod.o \
qepy_tddft_routines.o \
qepy_tddft_setup.o \
qepy_update_ham.o

QEPY_PROG_OBJS = tddft_main.o

QEPY_FIX_OBJS = tddft_version.o tddft_module.o tddft_routines.o \
	     tddft_setup.o tddft_ch_psi_all.o tddft_cgsolver.o \
	     update_ham.o apply_efield.o molecule_optical_absorption.o \
	     molecule_operators.o stop_code.o trajectory.o wavepacket.o

QE_OBJS = 

LIB_OBJS_TEMP =

include ../make.qepy.inc
include ../make.depend
