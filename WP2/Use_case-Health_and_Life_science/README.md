# VQE and classical shadows

Estimates the ground state energy of a small molecule with a hybrid workflow. A classical
Hartree-Fock and active space calculation builds a qubit Hamiltonian, VQE finds the ground
state parameters on a quantum backend, and a classical shadow of the resulting state gives
the final energy estimate.

## Layout

| File | What it does |
| --- | --- |
| [code/main.py](code/main.py) | Command line entry point and the full workflow |
| [code/hamiltonian.py](code/hamiltonian.py) | Hartree-Fock, AVAS active space selection, and the Jordan-Wigner qubit Hamiltonian |
| [code/vqe.py](code/vqe.py) | Ansatz, measurement grouping, SPSA optimization, trajectory replay |
| [code/classical_shadow.py](code/classical_shadow.py) | Snapshot circuits, shadow construction, median of means estimator |
| [code/fetch_replay.py](code/fetch_replay.py) | Decodes an already submitted replay job into a csv |

## Setup

The project uses uv and pins Python 3.12.

```bash
uv sync
```

Backends are chosen with `--backend`. `VLQ` runs on the IQM hardware through LEXIS and opens
a browser login on first use. `SIM` uses a local Aer simulator, whose jobs finish before
their results are asked for and are therefore not polled for status.

## Running the workflow

```bash
uv run code/main.py --backend VLQ --report-per-job-progress
```

The defaults describe an H2 molecule in the sto-3g basis, which gives 4 qubits and 15 Pauli
terms in 5 measurement groups. Other molecules are set with `--atom`, `--basis`, `--spin`,
`--ao-labels`, and `--threshold`. The geometry format is the one PySCF expects, as shown by
the default value of `--atom` in [code/main.py](code/main.py).

The run has three stages:

1. **Classical.** Hartree-Fock, active space selection, and the qubit Hamiltonian. Runs
   locally and takes a few seconds.
2. **VQE.** SPSA optimization of an EfficientSU2 ansatz. Commuting Pauli terms are grouped
   so that one job covers all terms, and both gradient probes of an iteration go into a
   single job. Set `--max-iters` and `--shots` to control the cost.
3. **Classical shadow.** `-N` single shot snapshots of the optimized state, batched into
   jobs of `--max-circuits-per-job` circuits, then a median of means estimate over `-K`
   groups. `-N` must be divisible by `-K`.

Between stages 2 and 3 the whole optimization trajectory is re-measured with
`--replay-shots` shots, so the convergence curve can be plotted without the shot noise that
the optimizer itself tolerates. Every iterate is known by then, so they all fit into very
few jobs. The result goes into `--trajectory-file`, which defaults to `vqe_trajectory.csv`.
Pass an empty string to skip the replay entirely.

## Running only the classical shadow part

To reuse parameters from an earlier run and go
straight to the shadow:

```bash
uv run code/main.py --shadow-only --parameters-file vqe_trajectory.csv
```

The parameters are read from the `parameter_*` columns of a trajectory csv. `--parameters-row`
picks which iterate to use, given as an iteration number. The default is `-1`, the last row.
The parameter count is checked against the ansatz, so a file from a different molecule or
active space fails immediately rather than producing a meaningless estimate.

The last row of a trajectory file holds the parameters that the optimization finished on,
so the default picks up the actual result of the VQE run.

## Fetching a job that was already submitted

If a run is interrupted after the replay job reaches the backend, the counts are still
waiting there. `fetch_replay.py` retrieves them by job id and writes the energies out.

```bash
uv run code/fetch_replay.py 78624 --output vqe-replay.csv
```

The counts of a job carry no record of which Pauli terms they encode, so the script reruns
the classical stage and rebuilds the measurement grouping. Both steps are deterministic, so
the groups come back in the exact order in which the circuits were submitted. **The molecule
arguments must match the run that submitted the job.** They take the same names and defaults
as in `main.py`.

The output is `iteration,replay_energy` by default. The parameters of a trajectory live only
in the memory of the process that ran the optimization, so they cannot be recovered from the
job. If the trajectory csv of that same run survived, pass `--trajectory-file` to merge its
live energies and parameters into the output and get the same column layout that a normal
run writes. Do not point it at a trajectory from a different run, because the parameters
belong to a different random initialization and the merged file would look correct without
being correct.

## Output files

`vqe_trajectory.csv` holds one row per SPSA iteration, with the noisy energy recorded during
the optimization, the re-measured energy, and the parameters of that iterate. Files written
by `fetch_replay.py` hold the re-measured energies alone unless a trajectory was merged in.

A run with `--max-iters 40` writes 41 rows. SPSA records each iterate as the midpoint of the
two points it probes a gradient around, so rows 1 to 40 are the points it measured at, and
the final update step it takes afterwards lands on the point in row 41. That last point is
the result of the optimization, and it is replayed along with the rest, so its row is filled
in like any other.

Energies are in Hartree and come from the active space electronic Hamiltonian, so the
nuclear repulsion is not included. For H2 at the default geometry the exact electronic
energy is about -1.852 Hartree, which is the `E(CI)` value that PySCF prints during the
classical stage.