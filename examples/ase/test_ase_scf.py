#!/usr/bin/env python3
import qepy
import time

try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
except Exception:
    comm = None

from qepy.calculator import QEpyCalculator

inputfile = 'qe_in.in'

calc = QEpyCalculator(comm = comm, inputfile = inputfile)

get_potential_energy      = calc.get_potential_energy()
get_forces                = calc.get_forces()
get_stress                = calc.get_stress()
get_density               = calc.get_density()
get_bz_k_points           = calc.get_bz_k_points()
get_eigenvalues           = calc.get_eigenvalues()
get_fermi_level           = calc.get_fermi_level()
get_ibz_k_points          = calc.get_ibz_k_points()
get_k_point_weights       = calc.get_k_point_weights()
get_magnetic_moment       = calc.get_magnetic_moment()
get_number_of_bands       = calc.get_number_of_bands()
get_number_of_grid_points = calc.get_number_of_grid_points()
get_number_of_spins       = calc.get_number_of_spins()
get_occupation_numbers    = calc.get_occupation_numbers()
get_pseudo_density        = calc.get_pseudo_density()
get_pseudo_wave_function  = calc.get_pseudo_wave_function()
get_spin_polarized        = calc.get_spin_polarized()
get_xc_functional         = calc.get_xc_functional()

time.sleep(0.1)

if calc.is_root :
    print('ncharge:', get_density.sum()*calc.atoms.get_volume()/get_density.shape[0] , flush = True)
    print("calc.get_potential_energy()           =" , get_potential_energy           , flush = True)
    print("calc.get_forces()[0]                  =" , get_forces[0]                  , flush = True)
    print("calc.get_stress()[0]                  =" , get_stress[0]                  , flush = True)
    print("calc.get_density()[0]                 =" , get_density[0]                 , flush = True)
    print("calc.get_bz_k_points()[:, 0]          =" , get_bz_k_points[:, 0]          , flush = True)
    print("calc.get_eigenvalues()[0]             =" , get_eigenvalues[0]             , flush = True)
    print("calc.get_fermi_level()                =" , get_fermi_level                , flush = True)
    print("calc.get_ibz_k_points()[:, 0]         =" , get_ibz_k_points[:, 0]         , flush = True)
    print("calc.get_k_point_weights()[0]         =" , get_k_point_weights[0]         , flush = True)
    print("calc.get_magnetic_moment()            =" , get_magnetic_moment            , flush = True)
    print("calc.get_number_of_bands()            =" , get_number_of_bands            , flush = True)
    print("calc.get_number_of_grid_points()      =" , get_number_of_grid_points      , flush = True)
    print("calc.get_number_of_spins()            =" , get_number_of_spins            , flush = True)
    print("calc.get_occupation_numbers()[0]      =" , get_occupation_numbers[0]      , flush = True)
    print("calc.get_pseudo_density()[0]          =" , get_pseudo_density[0]          , flush = True)
    print("calc.get_pseudo_wave_function()[0, 0] =" , get_pseudo_wave_function[0, 0] , flush = True)
    print("calc.get_spin_polarized()             =" , get_spin_polarized             , flush = True)
    print("calc.get_xc_functional()              =" , get_xc_functional              , flush = True)

time.sleep(0.1)
