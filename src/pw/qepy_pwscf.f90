!
! Copyright (C) 2001-2013 Quantum ESPRESSO group
! This file is distributed under the terms of the
! GNU General Public License. See the file `License'
! in the root directory of the present distribution,
! or http://www.gnu.org/copyleft/gpl.txt .
!
!----------------------------------------------------------------------------
!qepy -->
SUBROUTINE qepy_pwscf(infile, my_world_comm, embed)
!qepy <--
  !! Author: Paolo Giannozzi
  !
  !! Version: v6.1
  !
  !! License: GNU
  !
  !! Summary: Main program calling one or more instances of Plane Wave Self-Consistent Field code
  !
  !! This is the main program for executable "pw.x".  |
  !! * If called as "pw.x -ipi server-address" or "pw.x --ipi server-address",
  !! works in "server" mode, calls [[run_driver]].
  !! * If called as "manypw.x" via a link, works in "manypw" mode, runs many
  !! instances (images) of pw.x (see [[run_manypw]])
  !! * If called as "dist.x" via a link, works in "dry run" mode, computes
  !! distances, angles, neighbors, writes to file "dist.out" and stops. 
  !! Otherwise: see [[run_pwscf]]
  !!
  !! @Note
  !! 10/01/17 Samuel Ponce: Add Ford documentation
  !! @endnote
  !!
  !! @warning
  !! Example of Warning
  !!
  !! @todo
  !! Have automatic parallelisation. 
  !!
  !! @bug
  !! No bug.
  !!
  USE environment,          ONLY : environment_start
  USE mp_global,            ONLY : mp_startup
  USE read_input,           ONLY : read_input_file
  USE command_line_options, ONLY : input_file_, command_line, nimage_
  USE upf_utils,            ONLY : matches
  !
!qepy -->
  USE qepy_common,          ONLY : embed_base, set_embed, messenger, p_embed => embed
!qepy <--
  IMPLICIT NONE
  !
  CHARACTER(len=256) :: srvaddress
  !! Get the address of the server 
  CHARACTER(len=256) :: get_server_address
  !! Get the address of the server 
  INTEGER :: exit_status
  !! Status at exit
  LOGICAL :: use_images
  !! true if running "manypw.x"
  !
!qepy -->
  CHARACTER(len=*) :: infile
  INTEGER, INTENT(IN), OPTIONAL :: my_world_comm
  type(embed_base), intent(inout), optional :: embed
  !
  if (present(embed)) call set_embed(embed)
  if (.not. associated(p_embed)) call set_embed(messenger)
  !
  IF ( PRESENT(my_world_comm)) THEN
  CALL mp_startup(my_world_comm=my_world_comm, start_images=.TRUE., images_only=.TRUE. )
  ELSE
!qepy <--
  CALL mp_startup( start_images=.TRUE., images_only=.TRUE. )
!qepy -->
  ENDIF
!qepy <--
  !
  !
  CALL environment_start( 'PWSCF' )
!qepy -->
  input_file_=trim(infile)
  CALL read_input_file( 'PW', input_file_ )
  CALL qepy_run_pwscf(exit_status)
END SUBROUTINE qepy_pwscf

SUBROUTINE qepy_pwscf_finalise()
   IMPLICIT NONE
   INTEGER :: exit_status

  CALL laxlib_end()
  CALL qepy_stop_run( exit_status )
  !CALL do_stop( exit_status )
END SUBROUTINE qepy_pwscf_finalise

SUBROUTINE qepy_initial(input, embed)
  USE io_global,   ONLY : ionode
  USE mp_global,   ONLY : mp_startup
  USE environment, ONLY : environment_start, environment_end
  USE qepy_common, ONLY : input_base
  USE io_files,    ONLY : tmp_dir, prefix
  USE check_stop,  ONLY : check_stop_init
  USE qepy_common, ONLY : embed_base, set_embed, messenger, p_embed => embed
  IMPLICIT NONE
  TYPE(input_base), OPTIONAL :: input
  type(embed_base), intent(inout), optional :: embed
  LOGICAL            :: start_images = .false.
  LOGICAL            :: images_only = .false.
  if (present(embed)) call set_embed(embed)
  if (.not. associated(p_embed)) call set_embed(messenger)
  IF (PRESENT(input)) THEN
     start_images = input%start_images
     images_only = input%start_images
  ENDIF
  IF ( PRESENT(input)) THEN
     IF (input%my_world_comm /= 0 ) THEN
        CALL mp_startup(my_world_comm=input%my_world_comm, start_images=start_images, images_only=images_only )
     ELSE
        CALL mp_startup(start_images=start_images, images_only=images_only )
     ENDIF
  ELSE
     CALL mp_startup(start_images=start_images )
  ENDIF
  IF (PRESENT(input)) THEN
     prefix = input%prefix
     tmp_dir = input%tmp_dir
     CALL environment_start ( input%code )
  ENDIF
  CALL check_stop_init()
END SUBROUTINE qepy_initial

SUBROUTINE qepy_finalise_end(input)
  !
  USE environment, ONLY : environment_start, environment_end
  USE qepy_common, ONLY : input_base
  USE mp_global,   ONLY : mp_global_end
  !
  IMPLICIT NONE
  !
  TYPE(input_base), OPTIONAL :: input
  !
  IF (PRESENT(input)) THEN
     CALL environment_end ( input%code )
  ENDIF
  CALL mp_global_end()
END SUBROUTINE qepy_finalise_end
!qepy <--
