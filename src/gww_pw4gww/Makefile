QESRC_DIR = GWW/pw4gww
PNAME = qepy_gww_pw4gww
QEPY_LIBS = -L$(PYBUILDDIR) -lqepy_phonon_gamma $(MODS_LR)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) -I$(PYBUILDDIR)/phonon_gamma -I$(QEDIR)/PHonon/Gamma $(INCS_MODS_LR) $(INCS_MODS_LR_QE)

QEPY_OBJS = 

QEPY_PROG_OBJS = pw4gww.o

QE_OBJS = 

LIB_OBJS_TEMP = allocate_wannier.o \
calculate_wing.o \
cgsolve_all_gamma.o \
contour_terms.o \
convergence.o \
dft_exchange.o \
diago_cg.o \
diago_cg_g.o \
easy_gw.o \
energies_xc.o \
exchange_custom.o \
fake_conduction.o \
fft_custom.o \
full.o \
gww_realus.o \
hpsi_pw4gww.o \
lanczos_chains.o \
matrix_wannier_gamma.o \
mp_wave_parallel.o \
o_1psi.o \
o_bands.o \
o_rinitcgg.o \
openfil_pw4gww.o \
operator_1_vp.o \
operator_debug.o \
optimal.o \
pola_lanczos.o \
pola_partial.o \
produce_wannier_gamma.o \
rotate_wannier.o \
self_lanczos.o \
semicore.o \
semicore_read.o \
start_pw4gww.o \
stop_pp.o \
v_basis.o \
wannier.o \
wannier_bse.o \
wannier_uterms.o \
wfc_real.o \
write_vpot_matrix.o \
write_wannier_matrix.o

include ../make.qepy.inc
include ../make.depend
