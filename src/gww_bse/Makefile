QESRC_DIR = GWW/bse
PNAME = qepy_gww_bse
QEPY_LIBS = -L$(PYBUILDDIR) -lqepy_gww_gww -lqepy_gww_minpack $(MODS_PW)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) -I$(PYBUILDDIR)/gww_gww -I$(QEDIR)/GWW/gww -I$(PYBUILDDIR)/gww_minpack -I$(QEDIR)/GWW/minpack $(INCS_MODS_PW) $(INCS_MODS_PW_QE) -I$(PYBUILDDIR)/gww_pw4gww -I$(QEDIR)/GWW/pw4gww

QEPY_OBJS = 

QEPY_PROG_OBJS = bse_main.o

QE_OBJS = 

LIB_OBJS_TEMP = absorption.o \
bse_basic_structure.o \
bse_wannier.o \
cgsolve.o \
check_basis.o \
conj_grad_stuff.o \
conjgrad.o \
contract_w_exc.o \
diago_exc.o \
direct_v_exc.o \
direct_w_exc.o \
direct_www.o \
dvpsi_bse.o \
exc_h_a.o \
exchange_exc.o \
exciton.o \
find_eig.o \
h_h.o \
lanczos.o \
openfil_bse.o \
plot_excwfn.o \
print_bse.o \
print_spectrum.o \
qpcorrections.o \
qpe_exc.o \
read_export.o \
rotate_wannier.o \
sdescent.o \
spectrum.o \
start_bse.o \
transitions.o \
tspace.o \
write_wannier_matrix.o \
../pw4gww/fft_custom.o \
../pw4gww/stop_pp.o \
../pw4gww/mp_wave_parallel.o

include ../make.qepy.inc
include ../make.depend
