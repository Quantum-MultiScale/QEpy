.. QEpy documentation master file

=================================
QEpy - Quantum ESPRESSO in Python
=================================

QEpy_ turns `Quantum ESPRESSO (QE) <https://www.quantum-espresso.org/>`_ into a Python DFT engine for nonstandard workflows. QEpy_ allows the user to include external potentials, use custom xc functionals, and much much more.

Contributors and funding
========================

 - Main author: `Xuecheng Shao  <https://www.shaoxc.com/>`_ (former PRG_ member, now at Jilin University)
 - Aniket Mandal (Rutgers), Oliviero Andreussi (Boise State), Davide Ceresoli (CNR, Italy), Andrew Baczewski (Sandia), Quinn Campbell (Sandia), `Michele Pavanello <https://sasn.rutgers.edu/about-us/faculty-staff/michele-pavanello>`_ (Rutgers).
 - `The Quantum MultiScale collaboration <http://www.quantum-multiscale.org/>`_.


Thanks to ...
=============
 - The Quantum ESPRESSO developers for the QE codebase
 - NSF for funding the Quantum MultiScale collaboration

What's in this code?
====================
Minor modifications to QE routines (e.g., electrons.f90) and a compilation with Python wrappers. QEpy_ is kept up to date with the latest QE stable release.


If you like QEpy_ then ...
==========================

...you likely also would like to play around with DFTpy_

Contents
========

.. toctree::
   :maxdepth: 2

   contact
   install
   tutorials/tutorials
   qepy/qepy
   faq

.. _QEpy: https://github.com/Quantum-MultiScale/QEpy
.. _Python: https://www.python.org
.. _DFTpy: http://dftpy.rutgers.edu
.. _PRG: https://sites.rutgers.edu/prg
