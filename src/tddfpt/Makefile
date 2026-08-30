QESRC_DIR = TDDFPT/src
PNAME = qepy_tddfpt
QEPY_LIBS = -L$(PYBUILDDIR) $(MODS_LR)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) $(INCS_MODS_LR) $(INCS_MODS_LR_QE)

QEPY_OBJS = 

QEPY_PROG_OBJS = lr_dav_main.o \
lr_eels_main.o \
lr_magnons_main.o \
lr_main.o \
turbo_spectrum.o

QE_OBJS = 

LIB_OBJS_TEMP = bcast_lr_input.o \
dveqpsi_us.o \
dveqpsi_us_only.o \
environ_td_module.o \
linear_solvers.o \
lr_Opsi_magnons.o \
lr_addus_dvpsi.o \
lr_alloc_init.o \
lr_apply_liouvillian.o \
lr_apply_liouvillian_eels.o \
lr_apply_liouvillian_magnons.o \
lr_calc_dens.o \
lr_calc_dens_eels.o \
lr_calc_dens_eels_nc.o \
lr_calc_dens_magnons.o \
lr_charg_resp.o \
lr_compute_intq.o \
lr_dav_routines.o \
lr_dav_variables.o \
lr_dealloc.o \
lr_dv_setup.o \
lr_dvpsi_e.o \
lr_dvpsi_eels.o \
lr_dvpsi_magnons.o \
lr_exx_kernel.o \
lr_init_nfo.o \
lr_lanczos.o \
lr_magnons_routines.o \
lr_mix_pot.o \
lr_normalise.o \
lr_ortho.o \
lr_psym_eels.o \
lr_read_d0psi.o \
lr_read_wf.o \
lr_readin.o \
lr_restart.o \
lr_run_nscf.o \
lr_set_boxes_density.o \
lr_set_intq_nc.o \
lr_setup_nscf.o \
lr_smallgq.o \
lr_solve_e.o \
lr_sternheimer.o \
lr_summary.o \
lr_sym_eels.o \
lr_test_restart.o \
lr_transform_intq_nc.o \
lr_transform_intq_so.o \
lr_us.o \
lr_variables.o \
lr_write_restart.o \
paw_add_symmetry.o \
plugin_tddfpt_potential.o \
print_clock_lr.o \
sd0psi.o \
stop_lr.o

include ../make.qepy.inc
include ../make.depend
