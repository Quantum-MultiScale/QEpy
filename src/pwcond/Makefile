QESRC_DIR = PWCOND/src
PNAME = qepy_pwcond
QEPY_LIBS = -L$(PYBUILDDIR) $(MODS_PW)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) $(INCS_MODS_PW) $(INCS_MODS_PW_QE)

SKIPTYPES = 

QEPY_OBJS = 

QEPY_PROG_OBJS = condmain.o

QE_OBJS = 

LIB_OBJS_TEMP = allocate_cond.o \
bessj.o \
compbs.o \
compbs_2.o \
cond_out.o \
cond_restart.o \
condcom.o \
do_cond.o \
eigenchnl.o \
form_zk.o \
four.o \
free_mem.o \
gep_x.o \
gramsh.o \
hev_ab.o \
init_cond.o \
init_gper.o \
init_orbitals.o \
integrals.o \
jbloch.o \
kbloch.o \
local.o \
local_set.o \
openfil_cond.o \
plus_u_setup.o \
poten.o \
print_clock_pwcond.o \
realus_scatt.o \
rotproc.o \
save_cond.o \
scat_states_plot.o \
scatter_forw.o \
summary_band.o \
summary_tran.o \
sunitary.o \
transmit.o

include ../make.qepy.inc
include ../make.depend
