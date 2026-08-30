QESRC_DIR = PIOUD/src
PNAME = qepy_pioud
QEPY_LIBS = -L$(PYBUILDDIR) $(MODS_PW)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) $(INCS_MODS_PW) $(INCS_MODS_PW_QE)

QEPY_OBJS = 

QEPY_PROG_OBJS = pioud.o

QE_OBJS = 

LIB_OBJS_TEMP = compute_scf_pioud.o \
engine_to_trpmd_nat_alat.o \
engine_to_trpmd_pos.o \
fcp_opt_routines.o \
fcp_variables.o \
pimd_subrout.o \
pimd_utils.o \
pimd_variables.o \
pw_gen_inputs.o \
ring_formats.o \
ring_input_parameters_module.o \
ring_io_units_module.o \
ring_variables.o \
set_defaults.o \
stop_run_path.o \
trpmd_base.o \
trpmd_io_routines.o

include ../make.qepy.inc
include ../make.depend
