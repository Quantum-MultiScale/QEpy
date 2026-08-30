QESRC_DIR = KCW/PP
PNAME = qepy_kcw_pp
QEPY_LIBS = -L$(PYBUILDDIR) -lqepy_kcw $(MODS_LR)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) -I$(PYBUILDDIR)/kcw -I$(QEDIR)/KCW/src $(INCS_MODS_LR) $(INCS_MODS_LR_QE)

QEPY_OBJS = 

QEPY_PROG_OBJS = compute_self_hartree.o \
interp_r_to_k.o \
merge_wann.o

QE_OBJS = 

LIB_OBJS_TEMP = bcast_kcw_pp_input.o \
input_pp_summary.o \
kcw_bands.o \
kcw_pp_readin.o \
read_hr.o \
sh_setup.o

include ../make.qepy.inc
include ../make.depend
