QESRC_DIR = GWW/gww
PNAME = qepy_gww_gww
QEPY_LIBS = -L$(PYBUILDDIR) -lqepy_gww_minpack $(MODS_BASE)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) -I$(PYBUILDDIR)/gww_minpack -I$(QEDIR)/GWW/minpack $(INCS_MODS_BASE) $(INCS_MODS_BASE_QE)

SKIPTYPES = 

QEPY_OBJS = 

QEPY_PROG_OBJS = gww.o \
gww_fit.o

QE_OBJS = 

LIB_OBJS_TEMP = basic_structures.o \
compact_product.o \
contour.o \
create_hf.o \
create_quasi_particle.o \
create_quasi_particle_off.o \
do_contour.o \
do_polarization_lanczos.o \
do_self_lanczos.o \
do_self_lanczos_full.o \
do_self_lanczos_time.o \
energies_gww.o \
expansion.o \
fft_gw.o \
fit_multipole.o \
fit_polynomial.o \
go_dressed_w.o \
go_exchange.o \
go_fft.o \
go_green.o \
go_polarization.o \
green_function.o \
gv_time.o \
input_gw.o \
lanczos_polarization.o \
para_gww.o \
polarization.o \
read_data_pw.o \
self_energy.o \
self_energy_storage.o \
start_end.o \
times_gw.o \
vcprim.o

include ../make.qepy.inc
include ../make.depend
