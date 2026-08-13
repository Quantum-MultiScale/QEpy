!
! Copyright (C) 2001-2009 Quantum ESPRESSO group
! This file is distributed under the terms of the
! GNU General Public License. See the file `License'
! in the root directory of the present distribution,
! or http://www.gnu.org/copyleft/gpl.txt .
!
MODULE qepy_phonon_common
  !! State shared between `qepy_phonon_initial`, `qepy_phonon_run` and
  !! `qepy_stop_ph`: the work plan decided by `check_initial_status`, that
  !! `do_phonon` and the final bookkeeping need afterwards.
  IMPLICIT NONE
  SAVE
  CHARACTER(LEN=256) :: auxdyn = ' '
END MODULE qepy_phonon_common
!
!-----------------------------------------------------------------------
SUBROUTINE qepy_phonon_initial(infile, my_world_comm)
  !-----------------------------------------------------------------------
  !! Jupyter/Python-safe driver of the phonon (ph.x) code: read the
  !! `&inputph` input and decide the work plan (which q-points/irreps need
  !! doing), same as `phonon()` up to (and including) the call to
  !! `check_initial_status`. Does not run the calculation itself (see
  !! `qepy_phonon_run`) and never calls Fortran `STOP`.
  !
  !qepy --> based on PHonon/PH/phonon.f90 : SUBROUTINE phonon()
  USE check_stop,          ONLY : check_stop_init
  USE environment,         ONLY : environment_start
  USE mp_global,           ONLY : mp_startup
  USE qepy_sys,            ONLY : command_line
  USE qepy_phonon_common,  ONLY : auxdyn
  ! closes the qestdin unit `phq_readin` (unlike pw.x's `read_input_file`)
  ! never closes itself, since standalone ph.x just exits right after --
  ! left open, it corrupts the *next* `qepy_phonon_initial` call's read of a
  ! same-named input file in the same process (stale file position)
  USE open_close_input_file, ONLY : close_input_file
  !qepy <--
  !
  IMPLICIT NONE
  !
  CHARACTER(len=*) :: infile
  INTEGER, INTENT(IN), OPTIONAL :: my_world_comm
  CHARACTER (LEN=9)   :: code = 'PHONON'
  INTEGER :: ierr_close
  !
  !qepy --> fake a "-i infile" command line argument, picked up by
  ! `open_input_file`/`get_file_name` (src/cmdx/open_close_input_file.f90)
  ! through `phq_readin`, instead of dumping stdin to "input_tmp.in"
  command_line = ' -i ' // infile
  !qepy <--
  !
  IF ( PRESENT(my_world_comm)) THEN
     CALL mp_startup(my_world_comm=my_world_comm, start_images=.true., images_only=.true. )
  ELSE
     CALL mp_startup ( start_images=.true., images_only=.true. )
  ENDIF
  !
  CALL environment_start ( code )
  !
  CALL phq_readin()
  !
  !qepy --> see USE open_close_input_file above
  ierr_close = close_input_file()
  !qepy <--
  !
  CALL check_stop_init()
  !
  CALL check_initial_status(auxdyn)
  !
  !qepy --> unset command_line
  command_line = ' '
  !qepy <--
  !
END SUBROUTINE qepy_phonon_initial
!
!-----------------------------------------------------------------------
SUBROUTINE qepy_phonon_run()
  !-----------------------------------------------------------------------
  !! Run the phonon (linear-response) calculation set up by
  !! `qepy_phonon_initial`. Same as the remainder of `phonon()`, minus the
  !! terminal `STOP` (see `qepy_stop_ph` for the Jupyter/Python-safe
  !! finalization).
  !
  USE control_flags,       ONLY : use_para_diag
  USE control_ph,          ONLY : bands_computed, qplot
  USE ph_restart,          ONLY : ph_writefile
  USE YAMBO,                ONLY : elph_yambo, dvscf_yambo
  USE qepy_phonon_common,  ONLY : auxdyn
  !
  IMPLICIT NONE
  !
  INTEGER :: ierr
  !
  CALL do_phonon(auxdyn)
  !
  CALL ph_writefile('status_ph', 1, 0, ierr)
  !
  IF (.not.elph_yambo .and. .not.dvscf_yambo) THEN
     IF (qplot) CALL write_qplot_data(auxdyn)
     IF (bands_computed) CALL print_clock_pw()
  ENDIF
  !
  IF ( use_para_diag ) CALL laxlib_end()
  !
END SUBROUTINE qepy_phonon_run
!
!-----------------------------------------------------------------------
SUBROUTINE qepy_stop_ph( finalize )
  !-----------------------------------------------------------------------
  !! Jupyter/Python-safe version of `stop_ph`/`stop_smoothly_ph`
  !! (PHonon/PH/stop_ph.f90): same file/clock/environment cleanup, but
  !! never calls `mp_global_end()` or Fortran `STOP`, so the calling
  !! process (e.g. a Jupyter kernel) keeps running and can start another
  !! `Driver` afterwards.
  !
  !qepy --> based on PHonon/PH/stop_ph.f90 : SUBROUTINE stop_ph(flag) / stop_smoothly_ph(flag)
  USE ph_restart,          ONLY : destroy_status_run
  USE save_ph,             ONLY : clean_input_variables
  USE environment,         ONLY : environment_end
  USE mp_world,            ONLY : world_comm
  USE mp_bands,            ONLY : inter_bgrp_comm, intra_bgrp_comm
  USE mp_pools,            ONLY : inter_pool_comm, intra_pool_comm
  USE mp_images,           ONLY : inter_image_comm, intra_image_comm
  USE mp,                  ONLY : mp_comm_free, mp_barrier, mp_end, mp_stop
  ! q/irrep work-plan arrays set up by `check_initial_status`/`q_points`
  ! (PHonon/PH/phcom.f90): never deallocated upstream because ph.x normally
  ! exits the process right after using them once.
  USE disp,                ONLY : x_q, wq, omega_disp, lgamma_iq, done_iq, comp_iq
  USE grid_irr_iq,         ONLY : npert_irr_iq, irr_iq, nsymq_iq, comp_irr_iq, &
                                   done_irr_iq, done_elph_iq, done_bands
  !qepy <--
  !
  IMPLICIT NONE
  !
  LOGICAL, OPTIONAL, INTENT(IN) :: finalize
  INTEGER :: ierr
  !
  CALL collect_grid_files()
  !
  CALL clean_input_variables()
  !
  CALL destroy_status_run()
  !
  CALL deallocate_part()
  !
  CALL deallocate_phq()
  !
  CALL print_clock_ph()
  !
  CALL environment_end('PHONON')
  !
  !qepy --> deallocate the PW-side (ions_base, cell_base, ...) arrays that
  ! `phq_readin`/`do_phonon` (re-)allocated, so a subsequent `Driver` in the
  ! same process (e.g. a fresh 'scf' run) can allocate them again. Without
  ! this, PW/src/input.f90 aborts with "Attempting to allocate already
  ! allocated variable 'ityp'". Same call as `qepy_pwscf.f90`'s `qepy_stop_run`.
  CALL clean_pw( .TRUE. )
  !
  ! same reasoning for the q/irrep work-plan arrays (see the USE statements above)
  IF ( ALLOCATED(x_q) )          DEALLOCATE(x_q)
  IF ( ALLOCATED(wq) )           DEALLOCATE(wq)
  IF ( ALLOCATED(omega_disp) )   DEALLOCATE(omega_disp)
  IF ( ALLOCATED(lgamma_iq) )    DEALLOCATE(lgamma_iq)
  IF ( ALLOCATED(done_iq) )      DEALLOCATE(done_iq)
  IF ( ALLOCATED(comp_iq) )      DEALLOCATE(comp_iq)
  IF ( ALLOCATED(npert_irr_iq) ) DEALLOCATE(npert_irr_iq)
  IF ( ALLOCATED(irr_iq) )       DEALLOCATE(irr_iq)
  IF ( ALLOCATED(nsymq_iq) )     DEALLOCATE(nsymq_iq)
  IF ( ALLOCATED(comp_irr_iq) )  DEALLOCATE(comp_irr_iq)
  IF ( ALLOCATED(done_irr_iq) )  DEALLOCATE(done_irr_iq)
  IF ( ALLOCATED(done_elph_iq) ) DEALLOCATE(done_elph_iq)
  IF ( ALLOCATED(done_bands) )   DEALLOCATE(done_bands)
  !qepy <--
  !
  !qepy --> mp_global_end(), without tearing down world_comm, so the
  ! calling process can start another Driver afterwards
  IF ( intra_bgrp_comm  /= 0 .and. intra_bgrp_comm  /= world_comm ) THEN
     CALL mp_comm_free ( intra_bgrp_comm )
     intra_bgrp_comm = 0
  ENDIF
  IF ( inter_bgrp_comm  /= 0 .and. inter_bgrp_comm  /= world_comm ) THEN
     CALL mp_comm_free ( inter_bgrp_comm )
     inter_bgrp_comm = 0
  ENDIF
  IF ( intra_pool_comm  /= 0 .and. intra_pool_comm  /= world_comm ) THEN
     CALL mp_comm_free ( intra_pool_comm )
     intra_pool_comm = 0
  ENDIF
  IF ( inter_pool_comm  /= 0 .and. inter_pool_comm  /= world_comm ) THEN
     CALL mp_comm_free ( inter_pool_comm )
     inter_pool_comm = 0
  ENDIF
  IF ( intra_image_comm /= 0 .and. intra_image_comm /= world_comm ) THEN
     CALL mp_comm_free ( intra_image_comm )
     intra_image_comm = 0
  ENDIF
  IF ( inter_image_comm /= 0 .and. inter_image_comm /= world_comm ) THEN
     CALL mp_comm_free ( inter_image_comm )
     inter_image_comm = 0
  ENDIF
  CALL mp_barrier( world_comm )
#if defined(__MPI)
  IF ( PRESENT(finalize) ) THEN
     IF ( finalize ) THEN
        CALL mpi_finalize(ierr)
        IF (ierr/=0) CALL mp_stop( 8002 )
     ENDIF
  ENDIF
#endif
  !qepy <--
  !
END SUBROUTINE qepy_stop_ph
