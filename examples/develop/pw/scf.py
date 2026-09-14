import qepy
from qepy.driver import Driver

try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    comm = comm.py2f()
except Exception:
    comm = None

fname = 'qe_in.in'

driver = Driver(fname, comm, iterative=True)

for i in range(60):
    driver.diagonalize()
    driver.mix(mix_coef = 0.7)
    if driver.check_convergence(): break

energy = driver.get_energy()
forces = driver.get_forces()
stress = driver.get_stress()
driver.stop()

# print('energy', energy)
# print('forces', forces)
# print('stress', stress)
