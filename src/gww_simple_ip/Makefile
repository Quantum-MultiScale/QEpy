QESRC_DIR = GWW/simple_ip
PNAME = qepy_gww_simple_ip
QEPY_LIBS = -L$(PYBUILDDIR) -lqepy_gww_pw4gww $(MODS_PW)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) -I$(PYBUILDDIR)/gww_pw4gww -I$(QEDIR)/GWW/pw4gww $(INCS_MODS_PW) $(INCS_MODS_PW_QE)

QEPY_OBJS = 

QEPY_PROG_OBJS = simple_ip.o

QE_OBJS = 

LIB_OBJS_TEMP = diagonalization.o \
dielectric.o \
input_simple_ip.o \
interpolation.o \
simple_ip_objects.o \
start_end.o \
tetra_mod1.o

include ../make.qepy.inc
include ../make.depend
