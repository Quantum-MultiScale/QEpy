QESRC_DIR = NEB/src
PNAME = qepy_neb
QEPY_LIBS = -L$(PYBUILDDIR) $(MODS_PW)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) $(INCS_MODS_PW) $(INCS_MODS_PW_QE)

SKIPTYPES = 

QEPY_OBJS = 

QEPY_PROG_OBJS = neb.o \
path_interpolation.o \
path_io_tools.o

QE_OBJS = 

LIB_OBJS_TEMP = bcast_file.o \
compute_scf.o \
engine_to_path_alat.o \
engine_to_path_fix_atom_pos.o \
engine_to_path_nat.o \
engine_to_path_pos.o \
engine_to_path_tot_charge.o \
fcp_opt_routines.o \
fcp_variables.o \
gcscf_variables.o \
neb_input.o \
path_base.o \
path_formats.o \
path_gen_inputs.o \
path_input_parameters_module.o \
path_io_routines.o \
path_io_tools.o \
path_io_units_module.o \
path_opt_routines.o \
path_read_cards_module.o \
path_read_namelists_module.o \
path_reparametrisation.o \
path_to_engine_fix_atom_pos.o \
path_variables.o \
set_defaults.o \
stop_run_path.o

include ../make.qepy.inc
include ../make.depend
