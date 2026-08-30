QESRC_DIR = KS_Solvers
PNAME = qepy_ks_solvers
QEPY_LIBS = -L$(PYBUILDDIR) -lqepy_utilxlib -lqepy_laxlib -lqepy_modules -lqepy_pw
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) -I$(PYBUILDDIR)/utilxlib -I$(QEDIR)/UtilXlib -I$(PYBUILDDIR)/laxlib -I$(QEDIR)/LAXlib -I$(PYBUILDDIR)/modules -I$(QEDIR)/Modules -I$(PYBUILDDIR)/pw -I$(QEDIR)/PW/src

QEPY_OBJS = 

QEPY_PROG_OBJS = 

QE_OBJS = 

LIB_OBJS_TEMP = CG/ccgdiagg.o \
CG/rcgdiagg.o \
Davidson/cegterg.o \
Davidson/pcegterg.o \
Davidson/pregterg.o \
Davidson/regterg.o \
Davidson_RCI/david_rci.o \
DENSE/gram_schmidt_gamma.o \
DENSE/gram_schmidt_k.o \
DENSE/rotate_HSpsi_gamma.o \
DENSE/rotate_HSpsi_k.o \
DENSE/rotate_driver.o \
DENSE/rotate_wfc_gamma.o \
DENSE/rotate_wfc_k.o \
DENSE/rotate_xpsi_gamma.o \
DENSE/rotate_xpsi_k.o \
ParO/bpcg_gamma.o \
ParO/bpcg_k.o \
ParO/paro_gamma.o \
ParO/paro_gamma_new.o \
ParO/paro_k.o \
ParO/paro_k_new.o \
ParO/pcg_gamma.o \
ParO/pcg_k.o \
Direct/direct_diag_k.o \
RMM/crmmdiagg.o \
RMM/rrmmdiagg.o

include ../make.qepy.inc
include ../make.depend
