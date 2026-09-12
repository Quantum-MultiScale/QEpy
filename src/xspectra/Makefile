QESRC_DIR = XSpectra/src
PNAME = qepy_xspectra
QEPY_LIBS = -L$(PYBUILDDIR) $(MODS_PW)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) $(INCS_MODS_PW) $(INCS_MODS_PW_QE)

SKIPTYPES = 

QEPY_OBJS = 

QEPY_PROG_OBJS = molecularnexafs.o \
spectra_correction.o \
xspectra.o \
read_input_and_bcast.o

QE_OBJS = 

LIB_OBJS_TEMP = assign_paw_radii_to_species.o \
banner_xspectra.o \
check_orthogonality_k_epsilon.o \
gaunt_mod.o \
init_gipaw_1.o \
init_gipaw_2.o \
io_routines.o \
ipoolscatter.o \
lanczos.o \
lr_sm1_psi.o \
mygetK.o \
paw_gipaw.o \
plot_xanes_cross_sections.o \
radin_mod.o \
read_input_and_bcast.o \
read_k_points.o \
reset_k_points_and_reinit.o \
select_nl_init.o \
set_xspectra_namelists_defaults.o \
stdout_routines.o \
xanes_dipole.o \
xanes_dipole_general_edge.o \
xanes_quadrupole.o \
xspectra_mod.o \
xspectra_utils.o

include ../make.qepy.inc
include ../make.depend
