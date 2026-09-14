QESRC_DIR = KCW/src
PNAME = qepy_kcw
QEPY_LIBS = -L$(PYBUILDDIR) $(MODS_LR)
QEPY_INCS = -I. -I$(QEDIR)/$(QESRC_DIR) $(INCS_MODS_LR) $(INCS_MODS_LR_QE)

SKIPTYPES = 

QEPY_OBJS = 

QEPY_PROG_OBJS = kcw.o

QE_OBJS = 

LIB_OBJS_TEMP = alpha_corr.o \
apply_u_matrix.o \
bare_pot.o \
bcast_kcw_input.o \
bcast_wfc.o \
calculate_phase.o \
clean_pw_kcw.o \
close_kcw.o \
compute_map_ikq_single.o \
convert_kpts_names.o \
coulomb.o \
find_IBZ_q.o \
full_ham.o \
group_orbitals.o \
ham_R0_2nd.o \
input_summary.o \
interpolation.o \
kcw_R_points.o \
kcw_allocate_q.o \
kcw_comm.o \
kcw_deallocate_q.o \
kcw_deallocate_symmetry_arrays.o \
kcw_ham.o \
kcw_init_q.o \
kcw_initialize_ph.o \
kcw_io_new.o \
kcw_kpoint_grid.o \
kcw_openfilq.o \
kcw_prepare_q.o \
kcw_q_setup.o \
kcw_read_sym.o \
kcw_readin.o \
kcw_run_nscf.o \
kcw_screen.o \
kcw_setup.o \
kcw_setup_ham.o \
kcw_setup_screen.o \
kcw_write_sym.o \
koopmans_ham.o \
ks_hamiltonian.o \
print_clock_kcw.o \
read_alpha.o \
read_qlist_ibz.o \
read_wannier.o \
rho_of_q.o \
rotate_ks.o \
screen_coeff.o \
self_hartree.o \
setup_coulomb_exx.o \
solve_linter_koop_mod.o \
structure_factor.o \
wann2kcw.o \
write_hr_to_file.o \
write_qlist_ibz.o

include ../make.qepy.inc
include ../make.depend
