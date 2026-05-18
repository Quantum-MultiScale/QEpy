MODULE qepy_mod
   USE kinds,                   ONLY : DP
   USE scatter_mod,             ONLY : gather_grid, scatter_grid
   USE qepy_common,             ONLY : embed
   USE fft_base,                ONLY : dfftp
   !
   IMPLICIT NONE
   PUBLIC
   !
   INTERFACE mp_gather
      MODULE PROCEDURE mp_gather_real, mp_gather_complex
   END INTERFACE
   !
   INTERFACE mp_scatter
      MODULE PROCEDURE mp_scatter_real, mp_scatter_complex
   END INTERFACE
   !
   INTERFACE mp_bcast_group
      MODULE PROCEDURE mp_bcast_group_real_1, mp_bcast_group_real_2
   END INTERFACE
   !
   INTERFACE qepy_get_value
      MODULE PROCEDURE qepy_get_value_real_1, qepy_get_value_real_2
   END INTERFACE
   !
CONTAINS

   SUBROUTINE mp_gather_real(fin, fout)
      USE kinds,                ONLY : DP
      USE fft_base,             ONLY : dfftp
      !
      IMPLICIT NONE
      REAL(DP), INTENT(IN) :: fin(:)
      REAL(DP), INTENT(OUT) :: fout(:)
      !
      IF (dfftp%nproc > 1) THEN
         CALL gather_grid(dfftp, fin, fout)
      ELSE
         fout(:) = fin(:)
      ENDIF
   END SUBROUTINE

   SUBROUTINE mp_scatter_real(fin, fout)
      USE kinds,                ONLY : DP
      USE fft_base,             ONLY : dfftp
      !
      IMPLICIT NONE
      REAL(DP), INTENT(IN) :: fin(:)
      REAL(DP), INTENT(OUT) :: fout(:)
      !
      IF (dfftp%nproc > 1) THEN
         CALL scatter_grid(dfftp, fin, fout)
      ELSE
         fout(:) = fin(:)
      ENDIF
   END SUBROUTINE

   SUBROUTINE mp_gather_complex(fin, fout)
      USE kinds,                ONLY : DP
      USE fft_base,             ONLY : dfftp
      !
      IMPLICIT NONE
      COMPLEX(DP), INTENT(IN) :: fin(:)
      COMPLEX(DP), INTENT(OUT) :: fout(:)
      !
      IF (dfftp%nproc > 1) THEN
         CALL gather_grid(dfftp, fin, fout)
      ELSE
         fout(:) = fin(:)
      ENDIF
   END SUBROUTINE

   SUBROUTINE mp_gather_complex_s(fin, fout)
      USE kinds,                ONLY : DP
      USE fft_base,             ONLY : dffts
      !
      IMPLICIT NONE
      COMPLEX(DP), INTENT(IN) :: fin(:)
      COMPLEX(DP), INTENT(OUT) :: fout(:)
      !
      IF (dffts%nproc > 1) THEN
         CALL gather_grid(dffts, fin, fout)
      ELSE
         fout(:) = fin(:)
      ENDIF
   END SUBROUTINE

   SUBROUTINE mp_scatter_complex(fin, fout)
      USE kinds,                ONLY : DP
      USE fft_base,             ONLY : dfftp
      !
      IMPLICIT NONE
      COMPLEX(DP), INTENT(IN) :: fin(:)
      COMPLEX(DP), INTENT(OUT) :: fout(:)
      !
      IF (dfftp%nproc > 1) THEN
         CALL scatter_grid(dfftp, fin, fout)
      ELSE
         fout(:) = fin(:)
      ENDIF
   END SUBROUTINE

   SUBROUTINE mp_bcast_group_real_1(data)
      USE kinds,                ONLY : DP
      USE fft_base,             ONLY : dfftp
      USE mp,                   ONLY : mp_bcast
      USE mp_bands,             ONLY : inter_bgrp_comm, me_bgrp, root_bgrp, root_bgrp_id, nbgrp
      USE mp_pools,             ONLY : inter_pool_comm, me_pool, root_pool, npool
      !
      IMPLICIT NONE
      REAL(DP), INTENT(INOUT)        :: data(:)
      !
      IF (me_pool == root_pool .and. npool>1 ) CALL mp_bcast(data, root_pool, inter_pool_comm)
      IF (me_bgrp == root_bgrp .and. nbgrp>1 ) CALL mp_bcast(data, root_bgrp_id, inter_bgrp_comm)
   END SUBROUTINE

   SUBROUTINE mp_bcast_group_real_2(data)
      USE kinds,                ONLY : DP
      !
      IMPLICIT NONE
      REAL(DP), INTENT(INOUT)        :: data(:,:)
      INTEGER                        :: i, n2
      !
      n2 = size(data, 2)
      DO i = 1, n2
         CALL mp_bcast_group_real_1(data(:,i))
      END DO
   END SUBROUTINE

   SUBROUTINE qepy_get_value_real_1(fin, fout, gather, scatter)
      USE kinds,                ONLY : DP
      USE fft_base,             ONLY : dfftp
      !
      IMPLICIT NONE
      real(DP), INTENT(IN)        :: fin(:)
      real(DP), INTENT(OUT)       :: fout(:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      LOGICAL,INTENT(in),OPTIONAL :: scatter
      !
      INTEGER                     :: nnr
      LOGICAL                     :: gather_
      LOGICAL                     :: scatter_
      !
      gather_ = .FALSE.
      scatter_ = .FALSE.
      !
      IF ( present(gather) ) gather_ = gather
      IF ( present(scatter) ) scatter_ = scatter
      !
      IF ( gather_ ) THEN
         CALL mp_gather(fin, fout)
      ELSE IF ( scatter_ ) THEN
         CALL mp_scatter(fin, fout)
      ELSE
         !nnr = dfftp%nr1x* dfftp%my_nr2p* dfftp%my_nr3p
         nnr = size(fin)
         fout(1:nnr) = fin
         fout(nnr:size(fout)) = 0.0_DP
      ENDIF
      !
   END SUBROUTINE

   SUBROUTINE qepy_get_value_real_2(fin, fout, gather, scatter)
      USE kinds,                ONLY : DP
      !
      IMPLICIT NONE
      real(DP), INTENT(IN)        :: fin(:,:)
      real(DP), INTENT(OUT)       :: fout(:,:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      LOGICAL,INTENT(in),OPTIONAL :: scatter
      !
      INTEGER                     :: ispin, nspin
      LOGICAL                     :: gather_
      LOGICAL                     :: scatter_
      !
      gather_ = .FALSE.
      scatter_ = .FALSE.
      !
      IF ( present(gather) ) gather_ = gather
      IF ( present(scatter) ) scatter_ = scatter
      !
      nspin = size(fin, 2)
      DO ispin = 1, nspin
         call qepy_get_value_real_1(fin(:, ispin), fout(:, ispin), gather_, scatter_)
      END DO
      !
   END SUBROUTINE

   SUBROUTINE qepy_get_rho(rhor, gather)
      USE kinds,                ONLY : DP
      use scf,                  ONLY : rho, rhoz_or_updw
      USE fft_base,             ONLY : dfftp, dffts
      USE lsda_mod,             ONLY : lsda, nspin, current_spin, isk
      !
      IMPLICIT NONE
      REAL(DP), INTENT(OUT) :: rhor(:,:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      !
      LOGICAL :: gather_
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      IF (nspin > 1) CALL rhoz_or_updw( rho, 'only_r', '->updw' )
      !
      call qepy_get_value(rho%of_r, rhor, gather = gather_)
      !
      IF (nspin > 1) CALL rhoz_or_updw( rho, 'only_r', '->rhoz' )
   END SUBROUTINE

   SUBROUTINE qepy_set_rho(rhor, gather)
      USE kinds,                ONLY : DP
      USE fft_rho,              ONLY : rho_g2r, rho_r2g
      USE fft_base,             ONLY : dfftp, dffts
      use scf,                  ONLY : rho, rhoz_or_updw
      USE lsda_mod,             ONLY : lsda, nspin, current_spin, isk
      !
      IMPLICIT NONE
      REAL(DP), INTENT(IN) :: rhor(:,:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      !
      LOGICAL :: gather_
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      IF (nspin > 1) CALL rhoz_or_updw( rho, 'only_r', '->updw' )
      !
      call qepy_get_value(rhor, rho%of_r, scatter = gather_)
      !
      IF (nspin > 1) CALL rhoz_or_updw( rho, 'only_r', '->rhoz' )
      CALL rho_r2g(dfftp, rho%of_r, rho%of_g )
   END SUBROUTINE

   SUBROUTINE qepy_get_rho_core(rhoc, gather)
      USE kinds,                ONLY : DP
      use scf,                  ONLY : rho_core !! the core charge in real space
      USE fft_base,             ONLY : dfftp, dffts
      IMPLICIT NONE
      REAL(DP), INTENT(OUT) :: rhoc(:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      !
      LOGICAL :: gather_
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      call qepy_get_value(rho_core, rhoc, gather = gather_)
      !
   END SUBROUTINE

   SUBROUTINE qepy_set_rho_core(rhoc, gather)
      USE kinds,                ONLY : DP
      use scf,                  ONLY : rho_core, rhog_core
      USE fft_base,             ONLY : dfftp, dffts
      USE fft_rho,              ONLY : rho_r2g
      IMPLICIT NONE
      REAL(DP), INTENT(IN) :: rhoc(:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      !
      LOGICAL :: gather_
      COMPLEX(DP)                 :: rhogc(size(rhog_core),1)
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      call qepy_get_value(rhoc, rho_core, scatter = gather_)
      !
      CALL rho_r2g(dfftp, rho_core, rhogc)
      rhog_core(:) = rhogc(:,1)
   END SUBROUTINE

   SUBROUTINE qepy_set_extpot(vin, gather)
      USE kinds,                ONLY : DP
      USE fft_rho,              ONLY : rho_g2r, rho_r2g
      USE fft_base,             ONLY : dfftp, dffts
      USE lsda_mod,             ONLY : lsda, nspin, current_spin, isk
      USE mp,                   ONLY : mp_bcast
      !
      IMPLICIT NONE
      REAL(DP), INTENT(IN) :: vin(:,:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      !
      INTEGER :: ispin, ns
      LOGICAL :: gather_
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      call embed%allocate_extpot()
      !
      ns = size(vin,2)
      CALL mp_bcast(ns, dfftp%root, dfftp%comm)
      !
      call qepy_get_value(vin(:,1:ns), embed%extpot(:,1:ns), scatter = gather_)
      !
      DO ispin = ns+1, nspin
         embed%extpot(:,ispin) = embed%extpot(:,1)
      END DO
      !
   END SUBROUTINE

   FUNCTION qepy_get_grid(nr, gather) RESULT( nrw )
      USE kinds,                ONLY : DP
      USE fft_base,             ONLY : dfftp
      !
      IMPLICIT NONE
      INTEGER,INTENT(OUT),OPTIONAL :: nr(3)
      LOGICAL,INTENT(in),OPTIONAL  :: gather
      !
      INTEGER                      :: nrw(3)
      !
      IF ( present(gather) ) THEN
         nrw = qepy_get_grid_shape(dfftp, gather)
      ELSE
         nrw = qepy_get_grid_shape(dfftp)
      ENDIF
      !
      IF ( present(nr) ) nr = nrw
   END FUNCTION

   FUNCTION qepy_get_grid_shape(dfft, gather) RESULT( nrw )
      USE kinds,                ONLY : DP
      USE fft_types,            ONLY : fft_type_descriptor
      !
      IMPLICIT NONE
      TYPE(fft_type_descriptor),INTENT(IN) :: dfft
      LOGICAL,INTENT(in),OPTIONAL          :: gather
      !
      LOGICAL                              :: gather_
      INTEGER                              :: nrw(3)
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      IF ( gather_ ) THEN
         nrw =(/dfft%nr1, dfft%nr2, dfft%nr3/)
      ELSE
         nrw =(/dfft%nr1x, dfft%my_nr2p, dfft%my_nr3p/)
      ENDIF
      !
   END FUNCTION

   FUNCTION qepy_get_grid_smooth(nr, gather) RESULT(nrw)
      USE kinds,                ONLY : DP
      USE fft_base,             ONLY : dffts
      !
      IMPLICIT NONE
      INTEGER,INTENT(OUT),OPTIONAL :: nr(3)
      LOGICAL,INTENT(in),OPTIONAL  :: gather
      !
      INTEGER                      :: nrw(3)
      !
      IF ( present(gather) ) THEN
         nrw = qepy_get_grid_shape(dffts, gather)
      ELSE
         nrw = qepy_get_grid_shape(dffts)
      ENDIF
      !
      IF ( present(nr) ) nr = nrw
   END FUNCTION

   SUBROUTINE qepy_set_stdout(fname, uni, append)
      USE io_global,            ONLY : stdout, ionode
      !
      INTEGER                  :: ierr
      CHARACTER(LEN=*),INTENT(IN),OPTIONAL  :: fname
      INTEGER,INTENT(in),OPTIONAL :: uni
      LOGICAL,INTENT(in),OPTIONAL :: append
      !
      LOGICAL :: exst
      !
      IF ( .NOT. present(fname) ) return
      IF ( present(uni) ) THEN
         stdout = uni
      ELSE
         stdout = 666
      ENDIF
      !
      exst = .false.
      IF ( present(append)) THEN
         IF (append) INQUIRE (file = TRIM(fname), exist = exst)
      ENDIF
      !
      IF (exst) THEN
         OPEN (UNIT = stdout, FILE = TRIM(fname), FORM = 'formatted', POSITION = 'append', iostat = ierr )
      ELSE
         OPEN (UNIT = stdout, FILE = TRIM(fname), FORM = 'formatted', STATUS = 'unknown', iostat = ierr )
      ENDIF
   END SUBROUTINE

   SUBROUTINE qepy_write_stdout(fstr)
      USE io_global,            ONLY : stdout, ionode
      !
      INTEGER                  :: ierr
      CHARACTER(LEN=*),INTENT(IN)  :: fstr
      !
      IF(ionode) WRITE(stdout,'(A)') fstr
   END SUBROUTINE

   SUBROUTINE qepy_close_stdout(fname)
      USE io_global,            ONLY : stdout, ionode
      !
      INTEGER                  :: ierr
      CHARACTER(LEN=*),INTENT(IN)  :: fname
      !
      IF(ionode) close(stdout)
   END SUBROUTINE

   SUBROUTINE qepy_get_evc(ik, wfc)
      USE kinds,                ONLY : DP
      USE io_files,             ONLY : iunwfc, nwordwfc
      USE buffers,              ONLY : get_buffer
      USE wavefunctions,        ONLY : evc
      USE klist,                ONLY : nks
      !
      IMPLICIT NONE
      INTEGER,INTENT(IN) :: ik
      COMPLEX(DP), INTENT(OUT),OPTIONAL :: wfc(:,:)
      !
      IF ( nks > 1 ) CALL get_buffer ( evc, nwordwfc, iunwfc, ik )
      IF ( present(wfc) ) THEN
         wfc = evc
      ENDIF
   END SUBROUTINE

   SUBROUTINE qepy_get_wf(ik, ibnd, wf, gather)
      USE kinds,                ONLY : DP
      USE io_files,             ONLY : iunwfc, nwordwfc
      USE buffers,              ONLY : get_buffer
      USE wavefunctions,        ONLY : evc, psic
      USE klist,                ONLY : nks, igk_k, ngk
      USE fft_base,             ONLY : dfftp, dffts
      USE fft_interfaces,       ONLY : invfft
      USE control_flags,        ONLY : diago_full_acc, gamma_only, lxdm, tqr
      USE bp,                   ONLY : lelfield
      !
      IMPLICIT NONE
      INTEGER,INTENT(IN) :: ik, ibnd
      COMPLEX(DP), INTENT(OUT) :: wf(:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      !
      INTEGER :: j, nnr, npw
      LOGICAL :: gather_
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      IF ( dffts%has_task_groups ) THEN
         call errore('qepy_get_wf', 'Sorry this one not support task-group version', 1)
      ENDIF
      !
      IF ( nks > 1 .OR. lelfield ) CALL get_buffer ( evc, nwordwfc, iunwfc, ik )
      psic(:) = (0.0_DP, 0.0_DP)
      npw = ngk(ik)
      IF ( gamma_only ) THEN
         psic(dffts%nl (1:npw))  = evc(1:npw,ibnd)
         psic(dffts%nlm(1:npw)) = CONJG( evc(1:npw,ibnd) )
      ELSE
         !$omp parallel
         !$omp do
         DO j = 1, npw
            psic(dffts%nl(igk_k(j,ik))) = evc(j,ibnd)
         ENDDO
         !$omp end do nowait
         !$omp end parallel
      END IF
      CALL invfft ('Wave', psic, dffts)
      !
      IF ( gather_ ) THEN
         CALL mp_gather_complex_s(psic(1:dffts%nnr), wf)
      ELSE
         nnr = min(size(wf), dffts%nnr)
         wf(1:nnr) = psic(1:nnr)
         wf(nnr:size(wf)) = (0.0_DP, 0.0_DP)
      ENDIF
   END SUBROUTINE

   SUBROUTINE qepy_get_vkb(ik, vk, gather)
      USE kinds,                ONLY : DP
      USE io_files,             ONLY : iunwfc, nwordwfc
      USE buffers,              ONLY : get_buffer
      USE wavefunctions,        ONLY : evc, psic
      USE klist,                ONLY : nks, igk_k, ngk, xk
      USE uspp,                 ONLY : vkb, nkb
      USE fft_base,             ONLY : dfftp, dffts
      USE fft_interfaces,       ONLY : invfft
      USE control_flags,        ONLY : diago_full_acc, gamma_only, lxdm, tqr
      USE uspp_init,            ONLY : init_us_2
      !
      IMPLICIT NONE
      INTEGER,INTENT(IN) :: ik
      COMPLEX(DP), INTENT(OUT) :: vk(:,:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      !
      INTEGER :: i, j, nnr, npw
      LOGICAL :: gather_
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      IF ( dffts%has_task_groups ) THEN
         call errore('qepy_get_vkb', 'Sorry this one not support task-group version', 1)
      ENDIF
      !
      IF ( nkb > 0 ) CALL init_us_2( ngk(ik), igk_k(1,ik), xk(1,ik), vkb )
      !
      vk(:,:) = (0.0_DP, 0.0_DP)
      DO i = 1, nkb
         psic(:) = (0.0_DP, 0.0_DP)
         npw = ngk(ik)
         IF ( gamma_only ) THEN
            psic(dffts%nl (1:npw))  = vkb(1:npw,i)
            psic(dffts%nlm(1:npw)) = CONJG( vkb(1:npw,i) )
         ELSE
            !$omp parallel
            !$omp do
            DO j = 1, npw
               psic(dffts%nl(igk_k(j,ik))) = vkb(j,i)
            ENDDO
            !$omp end do nowait
            !$omp end parallel
         END IF
         CALL invfft ('Wave', psic, dffts)
         !
         IF ( gather_ ) THEN
            CALL mp_gather_complex_s(psic(1:dffts%nnr), vk(:, i))
         ELSE
            nnr = min(size(vk, 1), dffts%nnr)
            vk(1:nnr, i) = psic(1:nnr)
         ENDIF
      ENDDO
   END SUBROUTINE

   SUBROUTINE qepy_set_extforces(forces)
      USE kinds,                ONLY : DP
      USE ions_base,            ONLY : nat, ntyp => nsp
      !
      IMPLICIT NONE
      REAL(DP), INTENT(IN) :: forces(:,:)
      !
      call embed%allocate_extforces()
      embed%extforces(:,:) = forces(:,1:nat)
      !
   END SUBROUTINE

   SUBROUTINE qepy_calc_effective_potential(potential, gather)
      USE kinds,                ONLY : DP
      USE ions_base,            ONLY : nat, ntyp => nsp
      USE scf,                  ONLY : rho, rho_core, rhog_core, v, vltot, vrs
      USE ener,                 ONLY : etot, hwf_energy, eband, deband, ehart, &
                                       vtxc, etxc, etxcc, ewld, demet, epaw, &
                                       elondon, edftd3, ef_up, ef_dw
      USE ldaU,                 ONLY : eth
      USE extfield,             ONLY : tefield, etotefield
      USE lsda_mod,             ONLY : nspin
      !
      IMPLICIT NONE
      REAL(DP), INTENT(OUT),OPTIONAL  :: potential(:,:)
      LOGICAL,INTENT(in),OPTIONAL     :: gather
      !
      REAL(DP) :: charge
      !
      LOGICAL :: gather_
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      CALL qepy_v_of_rho_all( rho, rho_core, rhog_core, &
         ehart, etxc, vtxc, eth, etotefield, charge, v)
      !
      IF ( present(potential) ) THEN
         call qepy_get_value(vrs, potential, gather = gather_)
      ENDIF
      !
   END SUBROUTINE

   SUBROUTINE qepy_set_effective_potential(potential, gather)
      USE kinds,                ONLY : DP
      USE scf,                  ONLY : kedtau, v, vltot, vrs
      USE lsda_mod,             ONLY : nspin
      USE gvecs,                ONLY : doublegrid
      !
      IMPLICIT NONE
      REAL(DP),INTENT(IN)             :: potential(:,:)
      LOGICAL,INTENT(in),OPTIONAL     :: gather
      !
      LOGICAL :: gather_
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      call qepy_get_value(potential, vrs, gather = gather_)
      !
      CALL interpolate_vrs( dfftp%nnr, nspin, doublegrid, kedtau, v%kin_r, vrs )
      !
   END SUBROUTINE

   SUBROUTINE qepy_calc_density(rhor, gather)
      USE kinds,                ONLY : DP
      USE wvfct,                ONLY : nbnd, et
      USE klist,                ONLY : nks, nkstot
      !
      IMPLICIT NONE
      REAL(DP), INTENT(OUT),OPTIONAL :: rhor(:,:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      !
      CALL poolrecover( et, nbnd, nkstot, nks )
      CALL sum_band()
      !
      IF ( present(rhor) ) THEN
         IF ( present(gather) ) THEN
            call qepy_get_rho(rhor, gather)
         ELSE
            call qepy_get_rho(rhor)
         ENDIF
      ENDIF
   END SUBROUTINE

   SUBROUTINE qepy_diagonalize(iter, threshold)
      USE klist,                ONLY : nks, nkstot
      USE bp,                   ONLY : lelfield
      USE control_flags,        ONLY : ethr
      !
      IMPLICIT NONE
      INTEGER,INTENT(in),OPTIONAL :: iter
      REAL(DP),INTENT(in),OPTIONAL :: threshold
      !
      INTEGER                     :: it = 1
      !
      IF ( present(iter) ) it = iter
      IF ( present(threshold) ) ethr = threshold
      !
      IF ( lelfield ) THEN
         CALL c_bands_efield( it )
      ELSE
         CALL c_bands( it )
      ENDIF
   END SUBROUTINE

   SUBROUTINE qepy_update_ions(pos, ikind, lattice)
      !-----------------------------------------------------------------------
      ! This is function Combined 'run_pwscf' and 'move_ions'.
      !***********************************************************************
      ! pos:
      !   ionic positions in bohr
      ! ikind:
      !   ikind = 0  all
      !   ikind = 1  atomic configuration dependent information
      ! lattice:
      !   lattice parameter in bohr
      !***********************************************************************
      !-----------------------------------------------------------------------
      USE mp_images,            ONLY : intra_image_comm
      USE extrapolation,        ONLY : update_file, update_pot
      USE io_global,            ONLY : ionode_id, ionode
      USE ions_base,            ONLY : nat, ityp, tau
      USE symm_base,            ONLY : checkallsym
      USE mp,                   ONLY : mp_bcast
      USE control_flags,        ONLY : treinit_gvecs
      USE cell_base,            ONLY : alat, at, bg, omega, cell_force, &
                                     fix_volume, fix_area, ibrav, enforce_ibrav
      USE cellmd,               ONLY : omega_old, at_old, lmovecell, calc, cell_factor
      !
      !
      INTEGER                  :: ierr
      REAL(DP), INTENT(IN) :: pos(:,:)
      INTEGER,INTENT(IN),OPTIONAL  :: ikind
      REAL(DP), INTENT(IN), OPTIONAL  :: lattice(3,3)
      !
      INTEGER   :: iflag
      LOGICAL :: lmovecell_
      !
      IF ( present(ikind) ) THEN
         iflag = ikind
      ELSE
         iflag = 0
      ENDIF
      !
      IF ( present(lattice) ) THEN
         IF (.not. lmovecell) THEN
            call errore("qepy_update_ions","lattice update only works for calculation= 'vc-relax' and 'vc-md'.",1)
            ! This is due to the `gshells` function in the initialization will set `ngl`, which is one of the shape of `vloc`.
         ENDIF
         lmovecell_ = .TRUE.
      ELSE
         lmovecell_ = .FALSE.
      ENDIF

      CALL update_file()

      IF ( ionode ) THEN
         tau(:,:)=pos(:,:) / alat
         IF ( lmovecell_ ) THEN
            !
            IF (ALLOCATED(embed%extpot)) DEALLOCATE(embed%extpot)
            !
            at_old = at
            omega_old = omega
            IF (fix_volume) CALL impose_deviatoric_strain( alat*at, lattice )
            IF (fix_area)   CALL impose_deviatoric_strain_2d( alat*at, lattice )
            at = lattice / alat
            IF(enforce_ibrav) CALL remake_cell( ibrav, alat, at(1,1),at(1,2),at(1,3) )
            CALL recips( at(1,1),at(1,2),at(1,3), bg(1,1),bg(1,2),bg(1,3) )
            CALL volume( alat, at(1,1),at(1,2),at(1,3), omega )
            !
         ENDIF
         CALL checkallsym( nat, tau, ityp)
      ENDIF
      !
      CALL mp_bcast( tau, ionode_id, intra_image_comm )
      !
      IF ( lmovecell_ ) THEN
         !
         CALL mp_bcast( at,        ionode_id, intra_image_comm )
         CALL mp_bcast( at_old,    ionode_id, intra_image_comm )
         CALL mp_bcast( omega,     ionode_id, intra_image_comm )
         CALL mp_bcast( omega_old, ionode_id, intra_image_comm )
         CALL mp_bcast( bg,        ionode_id, intra_image_comm )
         !
      ENDIF
      IF (iflag == 0 ) THEN
         CALL punch( 'config-nowf' )
         IF ( treinit_gvecs ) THEN
            CALL reset_gvectors()
         ELSE
            CALL update_pot()
            CALL hinit1()
         END IF
      ELSE IF (iflag == 1 ) THEN
         CALL set_rhoc()
         CALL hinit1()
      END IF
   END SUBROUTINE

   SUBROUTINE qepy_restart_from_xml()
      USE symm_base,            ONLY : irt
      USE force_mod,            ONLY : force
      USE ions_base,            ONLY : extfor
      USE extfield,             ONLY : forcefield, forcegate
      USE pw_restart_new,       ONLY : read_xml_file
      !
      LOGICAL              :: wfc_is_collected
      !
      IF (ALLOCATED(irt)) DEALLOCATE(irt)
      IF (ALLOCATED(force)) DEALLOCATE(force)
      IF (ALLOCATED(extfor)) DEALLOCATE(extfor)
      IF (ALLOCATED(forcefield)) DEALLOCATE(forcefield)
      IF (ALLOCATED(forcegate)) DEALLOCATE(forcegate)
      !
      CALL read_xml_file(wfc_is_collected)
      !
   END SUBROUTINE

   SUBROUTINE qepy_sum_band(occupations)
      USE fixed_occ,            ONLY : tfixed_occ, f_inp
      USE lsda_mod,             ONLY : isk
      !
      REAL(DP),INTENT(in),OPTIONAL :: occupations(:,:)
      INTEGER :: isk_saved(size(isk))
      INTEGER :: i
      !
      IF ( present(occupations) ) THEN
         isk_saved = isk
         IF (ALLOCATED(f_inp)) DEALLOCATE(f_inp)
         ALLOCATE(f_inp(size(occupations,1), size(occupations,2)))
         f_inp(:,:) = occupations(:,:)
         tfixed_occ = .TRUE.
         DO i = 1, size(isk)
            isk(i) = i
         ENDDO
      ELSE
         tfixed_occ = .FALSE.
         IF (ALLOCATED(f_inp)) DEALLOCATE(f_inp)
      ENDIF
      !
      CALL sum_band()
      !
      IF ( present(occupations) ) isk = isk_saved
   END SUBROUTINE

   SUBROUTINE qepy_get_tau(tau, gather)
      USE kinds,                ONLY : DP
      use scf,                  ONLY : rho
      USE wavefunctions,        ONLY : psic
      USE fft_base,                ONLY : dfftp
      USE lsda_mod,             ONLY : nspin
      USE fft_interfaces,       ONLY : invfft
      USE control_flags,        ONLY : diago_full_acc, gamma_only, lxdm, tqr
      !
      IMPLICIT NONE
      REAL(DP), INTENT(OUT) :: tau(:,:)
      LOGICAL,INTENT(in),OPTIONAL :: gather
      !
      LOGICAL :: gather_
      INTEGER :: is
      !
      gather_ = .true.
      IF ( present(gather) ) gather_ = gather
      !
      !DO is = 1, nspin
         !psic(:) = ( 0.D0, 0.D0 )
         !psic(dfftp%nl(:)) = rho%kin_g(:,is)
         !IF ( gamma_only ) psic(dfftp%nlm(:)) = CONJG( rho%kin_g(:,is) )
         !CALL invfft ('Rho', psic, dfftp)
         !rho%kin_r(:,is) = psic(:)
      !END DO
      !
      call qepy_get_value(rho%kin_r, tau, gather = gather_)
   END SUBROUTINE

   SUBROUTINE qepy_open_files(io_level)
      USE kinds,                ONLY : DP
      USE io_files,             ONLY : nwordwfc, iunwfc
      USE control_flags,        ONLY : io_level_ => io_level
      USE buffers,              ONLY : open_buffer
      !
      IMPLICIT NONE
      INTEGER,INTENT(in),OPTIONAL :: io_level
      !
      INTEGER                     :: level
      LOGICAL :: exst_mem, exst_file, opnd
      !
      IF ( present(io_level) ) THEN
         level = io_level
      ELSE
         level = io_level_
      ENDIF
      !
      INQUIRE( UNIT = iunwfc, OPENED = opnd )
      IF ( .not. opnd ) CALL open_buffer( iunwfc, 'wfc', nwordwfc, level, exst_mem, exst_file )
      !
   END SUBROUTINE

   SUBROUTINE qepy_set_dft(dft)
      USE kinds,                ONLY : DP
      USE funct,                ONLY : enforce_input_dft
      USE xc_lib,               ONLY : xclib_dft_is
      USE fft_base,             ONLY : dffts
      USE lsda_mod,             ONLY : nspin
      USE gvect,                ONLY : ngm
      USE scf,                  ONLY : rho, vnew, v, kedtau
      !
      IMPLICIT NONE
      CHARACTER(LEN=*),INTENT(IN),OPTIONAL  :: dft
      !
      LOGICAL :: is_meta
      !
      is_meta = xclib_dft_is('meta')
      IF ( present(dft) ) THEN
         call enforce_input_dft(dft)
      ELSE
         call enforce_input_dft('M06L')
      ENDIF
      !
      IF ( xclib_dft_is('meta') .and. (.not. is_meta) ) THEN
         IF (ALLOCATED(kedtau)) DEALLOCATE(kedtau)
         ALLOCATE( kedtau(dffts%nnr,nspin) )
         !
         IF (ALLOCATED(rho%kin_r)) DEALLOCATE(rho%kin_r)
         IF (ALLOCATED(rho%kin_g)) DEALLOCATE(rho%kin_g)
         ALLOCATE( rho%kin_r(dfftp%nnr,nspin) )
         ALLOCATE( rho%kin_g(ngm,nspin) )
         !
         IF (ALLOCATED(v%kin_r)) DEALLOCATE(v%kin_r)
         IF (ALLOCATED(v%kin_g)) DEALLOCATE(v%kin_g)
         ALLOCATE( v%kin_r(dfftp%nnr,nspin) )
         ALLOCATE( v%kin_g(ngm,nspin) )
         !
         IF (ALLOCATED(vnew%kin_r)) DEALLOCATE(vnew%kin_r)
         IF (ALLOCATED(vnew%kin_g)) DEALLOCATE(vnew%kin_g)
         ALLOCATE( vnew%kin_r(dfftp%nnr,nspin) )
         ALLOCATE( vnew%kin_g(ngm,nspin) )
      ENDIF
      !
   END SUBROUTINE

   SUBROUTINE qepy_calc_kinetic_density(tau)
      USE kinds,                ONLY : DP
      USE control_flags,        ONLY : gamma_only
      USE wavefunctions,        ONLY : evc, psic
      USE wavefunctions_gpum,   ONLY : using_evc
      USE wvfct_gpum,           ONLY : using_et
      USE gvect,                ONLY : g, ngm
      USE klist,                ONLY : nks, igk_k, ngk, xk
      USE lsda_mod,             ONLY : lsda,  nspin
      USE fft_base,             ONLY : dffts, dfftp
      USE mp_pools,             ONLY : inter_pool_comm
      USE mp_bands,             ONLY : inter_bgrp_comm, intra_bgrp_comm
      use scf,                  ONLY : rho
      USE symme,                ONLY : sym_rho
      USE fft_rho,              ONLY : rho_g2r, rho_r2g
      USE mp,                   ONLY : mp_sum
      USE io_files,             ONLY : nwordwfc,  iunwfc
      USE cell_base,            ONLY : tpiba, omega
      USE wvfct,                ONLY : npwx, nbnd, wg, et
      USE buffers,              ONLY : get_buffer
      USE fft_wave,             ONLY : wave_g2r
      !
      IMPLICIT NONE
      REAL(DP), INTENT(OUT) :: tau(:,:)
      INTEGER :: npw, ibnd, j, ik, ikk, ispin, nk, i, ir
      REAL(dp), ALLOCATABLE :: g2kin(:)
      REAL(dp) :: kplusgi, w1
      COMPLEX(DP), ALLOCATABLE :: kplusg_evc(:,:), kin_g(:,:)
      !
      IF( lsda )THEN
         nk = nks/2
      ELSE
         nk = nks
      ENDIF
      !
      tau(:,:) = 0.0_DP
      ALLOCATE (kplusg_evc(npwx,1))
      ALLOCATE (kin_g(ngm,nspin))
      DO ispin = 1, nspin
         CALL using_evc(0); CALL using_et(0)
         DO ik = 1, nk
            ikk = ik + nk*(ispin-1)
            npw = ngk(ikk)
            IF( nks > 1 ) CALL get_buffer (evc, nwordwfc, iunwfc, ikk )
            IF( nks > 1 ) CALL using_evc(2)
            DO ibnd = 1, nbnd
               w1 = wg(ibnd,ikk)
               DO j = 1, 3
                  DO i = 1, npw
                     kplusgi = (xk(j,ik)+g(j,igk_k(i,ik))) * tpiba
                     kplusg_evc(i,1) = CMPLX(0.D0,kplusgi,kind=DP) * evc(i,ibnd)
                  ENDDO
                  IF (gamma_only) THEN
                     CALL wave_g2r( kplusg_evc(1:npw,1:1), psic, dffts)
                  ELSE
                     CALL wave_g2r( kplusg_evc(1:npw,1:1), psic, dffts, igk=igk_k(:,ik) )
                  ENDIF
                  !$omp parallel do
                  DO ir = 1, dffts%nnr
                     tau(ir, ispin) = tau(ir, ispin) + w1 * ( DBLE( psic(ir) )**2 + &
                        AIMAG( psic(ir) )**2 )
                  END DO
                  !$omp end parallel do
               ENDDO
            ENDDO
         ENDDO
      ENDDO
      tau = tau / omega
      ! symmetrize
      CALL mp_sum( tau, inter_pool_comm )
      CALL mp_sum( tau, inter_bgrp_comm )
      !
      CALL rho_r2g( dffts, tau, kin_g )
      !
      IF (.NOT. gamma_only) CALL sym_rho( nspin, kin_g )
      !
      CALL rho_g2r( dfftp, kin_g, tau )
      !
      DEALLOCATE (kplusg_evc, kin_g)
   END SUBROUTINE

   SUBROUTINE qepy_calc_kinetic_density_normal(tau)
      USE kinds,                ONLY : DP
      USE control_flags,        ONLY : gamma_only
      USE wavefunctions,        ONLY : evc, psic
      USE wavefunctions_gpum,   ONLY : using_evc
      USE wvfct_gpum,           ONLY : using_et
      USE gvect,                ONLY : g, ngm
      USE klist,                ONLY : nks, igk_k, ngk, xk
      USE lsda_mod,             ONLY : lsda,  nspin
      USE fft_base,             ONLY : dffts, dfftp
      USE mp_pools,             ONLY : inter_pool_comm
      USE mp_bands,             ONLY : inter_bgrp_comm, intra_bgrp_comm
      use scf,                  ONLY : rho
      USE symme,                ONLY : sym_rho
      USE fft_rho,              ONLY : rho_g2r, rho_r2g
      USE mp,                   ONLY : mp_sum
      USE io_files,             ONLY : nwordwfc,  iunwfc
      USE cell_base,            ONLY : tpiba2, omega
      USE wvfct,                ONLY : npwx, nbnd, wg, et
      USE buffers,              ONLY : get_buffer
      USE fft_wave,             ONLY : wave_g2r
      !
      IMPLICIT NONE
      REAL(DP), INTENT(OUT) :: tau(:,:)
      INTEGER :: npw, ibnd, j, ik, ikk, ispin, nk
      REAL(dp), ALLOCATABLE :: g2kin(:)
      REAL(dp) :: atmp
      COMPLEX(DP), ALLOCATABLE :: psicg(:)
      COMPLEX(DP), ALLOCATABLE :: evcg(:,:), kin_g(:,:)
      !
      IF( lsda )THEN
         nk = nks/2
      ELSE
         nk = nks
      ENDIF
      !
      tau(:,:) = 0.0_DP
      ALLOCATE ( g2kin(npwx), evcg(npwx,1), psicg(size(psic)))
      ALLOCATE (kin_g(ngm,nspin))
      DO ispin = 1, nspin
         CALL using_evc(0); CALL using_et(0)
         DO ik = 1, nk
            ikk = ik + nk*(ispin-1)
            npw = ngk(ikk)
            IF( nks > 1 ) CALL get_buffer (evc, nwordwfc, iunwfc, ikk )
            IF( nks > 1 ) CALL using_evc(2)
            g2kin(1:npw) = ( ( xk(1,ikk) + g(1,igk_k(1:npw,ikk)) )**2 + &
                             ( xk(2,ikk) + g(2,igk_k(1:npw,ikk)) )**2 + &
                             ( xk(3,ikk) + g(3,igk_k(1:npw,ikk)) )**2 ) * tpiba2
            DO ibnd = 1, nbnd
               evcg(1:npw,1) = evc(1:npw,ibnd) * g2kin(1:npw)
               IF (gamma_only) THEN
                  CALL wave_g2r(evc(1:npw,ibnd:ibnd), psic, dffts )
                  CALL wave_g2r(evcg(1:npw, 1:1), psicg, dffts)
               ELSE
                  CALL wave_g2r(evc(1:npw,ibnd:ibnd), psic, dffts, igk=igk_k(:,ikk) )
                  CALL wave_g2r(evcg(1:npw, 1:1), psicg, dffts, igk=igk_k(:,ikk) )
               ENDIF
               DO j = 1, dffts%nnr
                  atmp = DBLE(conjg(psic(j))*psicg(j)) * wg(ibnd,ikk)
                  tau(j,ispin) = tau(j,ispin) + atmp
               ENDDO
            ENDDO
         ENDDO
      ENDDO
      tau = tau / omega
      ! symmetrize
      CALL mp_sum( tau, inter_pool_comm )
      CALL mp_sum( tau, inter_bgrp_comm )
      !
      CALL rho_r2g( dffts, tau, kin_g )
      !
      IF (.NOT. gamma_only) CALL sym_rho( nspin, kin_g )
      !
      CALL rho_g2r( dfftp, kin_g, tau )
      !
      DEALLOCATE ( g2kin, evcg, psicg )
      DEALLOCATE ( kin_g )
   END SUBROUTINE

END MODULE qepy_mod
