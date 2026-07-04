#!/bin/bash
# Strict QEpy timing benchmark for Amarel (HPC).
# - One exclusive allocation, one node for all runs
# - Execution time only: /usr/bin/time around srun (not queue, not $SECONDS)
# - Per-test: one srun step per repeat (unavoidable for isolated tests)
# - Suite: one srun per mode per repeat (full file set)
# - 3 repeats → median written to TSV
#
# Submit: sbatch pytest_timing_strict.sh

#SBATCH --job-name=pytest-strict
#SBATCH --partition=main-redhat
#SBATCH --exclusive
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=0
#SBATCH --time=00:30:00
#SBATCH --output=pytest-strict-%j.log

set -o pipefail
BUILD="${BUILD_ROOT:-$HOME/qe_build}"
REPEATS=3
TSV="$BUILD/pytest-timing-strict.tsv"
LOG="$BUILD/pytest-timing-strict.log"
: > "$LOG"
exec > >(tee -a "$LOG") 2>&1

echo "=== strict timing $(date -Is) job=$SLURM_JOB_ID node=$(hostname -s) repeats=$REPEATS ==="

source /etc/profile.d/modules.sh
module load intel/18.0.5
export PATH="$BUILD/fakebin:$BUILD/venv_py39/bin:$PATH"
export LD_LIBRARY_PATH="/usr/lib64:${LD_LIBRARY_PATH:-}"
export I_MPI_CC=gcc I_MPI_FC=ifort I_MPI_FABRICS=shm I_MPI_PIN=0
export qedir="$BUILD/q-e" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
ulimit -s unlimited

PY="$BUILD/venv_py39/bin/python"
TESTDIR="$BUILD/QEpy/examples/test"
cd "$TESTDIR"

median() {
  printf '%s\n' "$@" | sort -g | awk '{
    a[NR]=$1
  } END {
    n=NR
    if (n==0) { print "NA"; exit }
    if (n%2) print a[(n+1)/2]; else print (a[n/2]+a[n/2+1])/2
  }'
}

echo -e "scope\tmode\ttest_id\texec_sec_median\tpytest_sec_median\trepeats\tnode\tnotes" > "$TSV"

# Returns: EXEC PYTEST RC on stdout
run_once() {
  local mode=$1 launcher=$2 spec=$3
  local rc=0 out mpi_flag=""
  [ "$mode" = "parallel" ] && mpi_flag="--with-mpi"
  out=$( { /usr/bin/time -f "__EXEC__ %e" $launcher "$PY" -m pytest -v --tb=line $mpi_flag $spec 2>&1; } ) || rc=$?
  local exec_sec pytest_sec
  exec_sec=$(echo "$out" | grep "__EXEC__" | tail -1 | awk '{print $2}')
  pytest_sec=$(echo "$out" | grep -oP "passed in \K[0-9.]+(?=s)" | tail -1)
  [ -z "$exec_sec" ] && exec_sec="NA"
  [ -z "$pytest_sec" ] && pytest_sec="NA"
  echo "$exec_sec $pytest_sec $rc"
}

run_pertest() {
  local mode=$1 launcher=$2 tid=$3 spec=$4
  local -a execs pytests
  local r rc
  echo ""
  echo "--- per-test $mode $tid ($REPEATS repeats) ---"
  for r in $(seq 1 "$REPEATS"); do
    read -r es ps rc <<< "$(run_once "$mode" "$launcher" "$spec")"
    echo "  repeat $r: exec=${es}s pytest=${ps}s rc=$rc"
    [ "$es" != "NA" ] && execs+=("$es")
    [ "$ps" != "NA" ] && pytests+=("$ps")
    [ "$rc" -ne 0 ] && echo "  WARN rc=$rc on repeat $r"
  done
  local med_exec med_py
  med_exec=$(median "${execs[@]}")
  med_py=$(median "${pytests[@]}")
  echo "  MEDIAN exec=$med_exec pytest=$med_py"
  echo -e "per-test\t${mode}\t${tid}\t${med_exec}\t${med_py}\t${REPEATS}\t$(hostname -s)\t${launcher}" >> "$TSV"
}

run_suite() {
  local mode=$1 launcher=$2
  local -a execs pytests
  local r rc
  echo ""
  echo "--- suite $mode ($REPEATS repeats, one srun each) ---"
  for r in $(seq 1 "$REPEATS"); do
    read -r es ps rc <<< "$(run_once "$mode" "$launcher" "test_pwscf.py test_readfile.py")"
    echo "  repeat $r: exec=${es}s pytest=${ps}s rc=$rc"
    [ "$es" != "NA" ] && execs+=("$es")
    [ "$ps" != "NA" ] && pytests+=("$ps")
  done
  local med_exec med_py
  med_exec=$(median "${execs[@]}")
  med_py=$(median "${pytests[@]}")
  echo "  MEDIAN exec=$med_exec pytest=$med_py"
  echo -e "suite\t${mode}\tall_4_tests\t${med_exec}\t${med_py}\t${REPEATS}\t$(hostname -s)\t${launcher}" >> "$TSV"
}

SERIAL="srun -n 1 --export=ALL"
PARALLEL="srun --mpi=pmi2 -n 2 --export=ALL"

run_pertest serial "$SERIAL" test_scf "test_pwscf.py::test_scf"
run_pertest parallel "$PARALLEL" test_scf "test_pwscf.py::test_scf"
run_pertest serial "$SERIAL" test_0_scf "test_readfile.py::test_0_scf"
run_pertest parallel "$PARALLEL" test_0_scf "test_readfile.py::test_0_scf"
run_pertest serial "$SERIAL" test_1_read "test_readfile.py::test_1_read"
run_pertest parallel "$PARALLEL" test_1_read "test_readfile.py::test_1_read"
run_pertest serial "$SERIAL" test_2_read_pw "test_readfile.py::test_2_read_pw"
run_pertest parallel "$PARALLEL" test_2_read_pw "test_readfile.py::test_2_read_pw"

run_suite serial "$SERIAL"
run_suite parallel "$PARALLEL"

echo ""
echo "=== SUMMARY $(hostname -s) ==="
column -t "$TSV" 2>/dev/null || cat "$TSV"
echo "=== STRICT_DONE $(date -Is) ==="
