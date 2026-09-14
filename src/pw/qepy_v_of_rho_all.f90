!
! Copyright (C) 2001-2020 Quantum ESPRESSO group
! This file is distributed under the terms of the
! GNU General Public License. See the file `License'
! in the root directory of the present distribution,
! or http://www.gnu.org/copyleft/gpl.txt .
!
!----------------------------------------------------------------------------
SUBROUTINE qepy_v_of_rho_all( rho, rho_core, rhog_core, tau_core, &
                     ehart, etxc, vtxc, eth, etotefield, charge, v )
  !----------------------------------------------------------------------------
  !! This routine computes the Hartree and Exchange and Correlation
  !! potential and energies which corresponds to a given charge density
  !! The XC potential is computed in real space, while the
  !! Hartree potential is computed in reciprocal space.
  !
  USE kinds,            ONLY : DP
  USE fft_base,         ONLY : dfftp
  USE gvect,            ONLY : ngm
  USE noncollin_module, ONLY : noncolin, nspin_lsda
  USE ions_base,        ONLY : nat, tau
  USE ldaU,             ONLY : lda_plus_u
  USE xc_lib,           ONLY : xclib_dft_is
  USE scf,              ONLY : scf_type
  USE cell_base,        ONLY : alat
  USE io_global,        ONLY : stdout
  USE control_flags,    ONLY : ts_vdw, mbd_vdw, sic
  USE tsvdw_module,     ONLY : tsvdw_calculate, UtsvdW
  USE libmbd_interface, ONLY : mbd_interface
  USE sic_mod,          ONLY : add_vsic
  !
  USE scf,                  ONLY : vltot, vrs, kedtau, vnew
  USE gvecs,                ONLY : doublegrid
  USE lsda_mod,             ONLY : lsda, nspin, magtot, absmag, isk
  USE plugin_variables,     ONLY : plugin_etot
  USE dfunct,               ONLY : newd
  USE paw_variables,        ONLY : okpaw, ddd_paw, total_core_energy, only_paw
  USE paw_onecenter,        ONLY : PAW_potential
  USE paw_symmetry,         ONLY : PAW_symmetrize_ddd
  USE ener,                 ONLY : epaw
  !
  USE qepy_common,      ONLY : embed
  !
  IMPLICIT NONE
  !
  TYPE(scf_type), INTENT(INOUT) :: rho
  !! the valence charge
  TYPE(scf_type), INTENT(INOUT) :: v
  !! the scf (Hxc) potential
  !=================> NB: NOTE that in F90 derived data type must be INOUT and 
  !=================> not just OUT because otherwise their allocatable or pointer
  !=================> components are NOT defined 
  REAL(DP), INTENT(IN) :: rho_core(dfftp%nnr)
  !! the core charge
  COMPLEX(DP), INTENT(IN) :: rhog_core(ngm)
  !! the core charge in reciprocal space
  REAL(DP), INTENT(IN) :: tau_core(dfftp%nnr)
  !! the kinetic energy density of the core charge
  REAL(DP), INTENT(OUT) :: vtxc
  !! the integral V_xc * rho
  REAL(DP), INTENT(OUT) :: etxc
  !! the E_xc energy
  REAL(DP), INTENT(OUT) :: ehart
  !! the hartree energy
  REAL(DP), INTENT(OUT) :: eth
  !! the hubbard energy
  REAL(DP), INTENT(OUT) :: charge
  !! the integral of the charge
  REAL(DP), INTENT(INOUT) :: etotefield
  !! electric field energy - inout due to the screwed logic of add_efield
  !
  REAL(DP) :: etot_cmp_paw(nat,2,2)
  !
  call qepy_v_of_rho( rho, rho_core, rhog_core, tau_core, &
                     ehart, etxc, vtxc, eth, etotefield, charge, v)
  IF (okpaw) THEN
     CALL PAW_potential( rho%bec, ddd_paw, epaw, etot_cmp_paw )
     CALL PAW_symmetrize_ddd( ddd_paw )
  ENDIF
!qepy --> 
  ! add extpot
  IF (ALLOCATED(embed%extpot)) v%of_r = v%of_r + embed%extpot
!qepy <-- 
     ! ... define the total local potential (external + scf)
     !
     CALL set_vrs( vrs, vltot, v%of_r, kedtau, v%kin_r, dfftp%nnr, &
                   nspin, doublegrid )
     !
     ! ... in the US case we have to recompute the self-consistent
     ! ... term in the nonlocal potential
     ! ... PAW: newd contains PAW updates of NL coefficients
     !
     CALL newd()
END SUBROUTINE qepy_v_of_rho_all
