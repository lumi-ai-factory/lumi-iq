# --- Imports ---
import os
import sys
import warnings
warnings.filterwarnings("ignore", message=".*IProgress not found.*")

try:
    from qaas.client import QProvider, QBackend, QJob
    if QJob is not None:
        if not hasattr(QJob, "is_final_state"):
            def _qjob_is_final_state(self):
                try:
                    st = str(self.status()).upper()
                    return any(term in st for term in ["DONE", "COMPLETED", "ERROR", "CANCEL", "FAIL"])
                except Exception:
                    return False
            QJob.is_final_state = _qjob_is_final_state
        if not hasattr(QJob, "in_final_state"):
            QJob.in_final_state = QJob.is_final_state
except ImportError:
    QProvider, QBackend, QJob = None, None, None

import argparse
import numpy as np
from typing import Literal
from qiskit.providers import Backend
from qiskit.circuit.instruction import Instruction
from qiskit.circuit.library import HGate, IGate, UnitaryGate, SGate
from qiskit.quantum_info import Operator

from hamiltonian import run_hf, select_active_space, active_space_hamiltonian, qubit_hamiltonian
from vqe import (general_ansatz, run_vqe, get_ground_state_circuit, estimate_energy,
                 build_measurement_groups, replay_trajectory, save_trajectory,
                 load_trajectory)
from classical_shadow import calculate_snapshots, create_pauli_shadow

# --- Functions ---

def get_backend(name: str) -> Backend:
    '''
    Initializes the chosen backend.

    Args:
        name: The name of the backend that should be used. Options are "VLQ" and "SIM".
    Returns:
        backend: The chosen backend
    '''

    if name == 'VLQ':
        try:
            from config import LEXIS_PROJECT, LEXIS_RESOURCE, get_lexis_token, save_lexis_token
        except ImportError:
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
            from config import LEXIS_PROJECT, LEXIS_RESOURCE, get_lexis_token, save_lexis_token

        token = get_lexis_token()
        if token:
            print(f"Using saved token from ~/.lumi-iq/token for LEXIS project '{LEXIS_PROJECT}'")
            provider = QProvider(lexis_project=LEXIS_PROJECT, token=token)
        else:
            print(f"No saved token found. Prompting OAuth Device Flow for project '{LEXIS_PROJECT}'...")
            provider = QProvider(lexis_project=LEXIS_PROJECT)
            if getattr(provider, "_token", None):
                save_lexis_token(provider._token)

        backend: QBackend = provider.get_backend(LEXIS_RESOURCE)
        print(f"Backend '{backend.name}' successfully initialized (target: {LEXIS_RESOURCE}).")
    elif name == 'SIM':
        from qiskit_aer import AerSimulator
        backend = AerSimulator()
    else:
        raise ValueError(f"Backend not supported. Supported backends are VLQ and SIM. Got {name}.")

    return backend
    

def build_y_gate() -> UnitaryGate:
    '''
    Builds the Y basis measurement rotation gate (Sdg followed by H).
    Returns:
        y_gate: The Y basis measurement rotation gate
    '''
    Y_measurement_rotation = Operator(HGate()).data @ Operator(SGate().inverse()).data
    return UnitaryGate(Y_measurement_rotation)
    

def run_workflow(
        atom: str,
        basis: str,
        spin: int,
        ao_labels: list[str],
        backend: Backend | str | None = None,
        optimization_level: Literal[0, 1, 2, 3] = 1,
        shots: int = 256,
        N: int = 100,
        K: int = 10,
        threshold: float = 0.2,
        learning_rate: float | None = None,
        perturbation: float | None = None,
        report_per_job_progress: bool = False,
        trajectory_file: str | None = 'vqe_trajectory.csv',
        replay_shots: int = 10000,
        max_circuits_per_job: int = 1000,
        max_iters: int = 40,
        run_vqe_stage: bool = True,
        optimal_params: np.ndarray | None = None,
        is_simulation: bool | None = None,
        backend_name: str | None = None,
        **kwargs
        ) -> float:
    '''
    Runs the full hybrid quantum-classical workflow to estimate the ground state
    energy of a molecule using VQE combined with classical shadows.
    Args:
        atom: Atomic geometry string
        basis: Basis set name
        spin: Number of unpaired electrons. Zero for closed-shell, positive integer for open-shell
        ao_labels: List of atomic orbital labels for AVAS active space selection
        backend: The backend to run the quantum circuits on (Backend instance or string 'VLQ' / 'SIM')
        optimization_level: The transpilation optimization level, options are 0-3 (default: 1)
        shots: The number of shots for each circuit evaluation
        N: The number of classical shadow snapshots to collect
        K: The number of groups for the median-of-means estimator
        threshold: AVAS threshold for active space selection. Default is 0.2.
        learning_rate: The SPSA learning rate. Must be given together with perturbation.
            If both are left as None, SPSA calibrates them automatically. Default is None.
        perturbation: The SPSA perturbation. Must be given together with learning_rate.
            Default is None.
        report_per_job_progress: If True, prints the id of every job that is submitted
        trajectory_file: The csv file to save the VQE convergence data into. Set to None
            to skip the replay entirely. Default is 'vqe_trajectory.csv'.
        replay_shots: The number of shots to use when re-measuring the trajectory.
            Default is 100000.
        max_circuits_per_job: The largest number of circuits to put into a single job
            when re-measuring the trajectory. Default is 1000.
        run_vqe_stage: If True, runs VQE and the trajectory replay to find the ground
            state parameters. If False, both are skipped and the parameters given in
            optimal_params are used instead, so that only the classical shadow part is
            run on the quantum backend. Default is True.
        optimal_params: The ansatz parameters to build the ground state circuit from.
            Required when run_vqe_stage is False, ignored otherwise. Default is None.
        is_simulation: If True, jobs are not polled for their status.
        backend_name: Alternative alias for backend (supports 'VLQ' or 'SIM').
    Returns:
        energy_estimate: The estimated ground state energy in Hartree units
    '''
    # Resolve backend string or alias
    if backend is None and backend_name is not None:
        backend = backend_name
    if isinstance(backend, str):
        backend_name_str = backend
        backend = get_backend(backend_name_str)
        if is_simulation is None:
            is_simulation = (backend_name_str == 'SIM')
    elif is_simulation is None:
        is_simulation = False

    # Validate inputs
    if optimization_level not in range(4):
        raise ValueError('optimization_level must be 0, 1, 2, or 3')
    if N % K != 0:
        raise ValueError(f'N must be divisible by K. Got N={N}, K={K}.')
    if not run_vqe_stage and optimal_params is None:
        raise ValueError(
            'optimal_params must be given when run_vqe_stage is False, because the '
            'ground state circuit cannot be built without them.'
        )

    # Build U_list for classical shadow measurements
    U_list = [HGate(), build_y_gate(), IGate()]

    # --- Classical HPC part ---
    print('Running Hartree-Fock calculation...')
    mf = run_hf(atom, basis, spin)
    print(f'RHF energy: {mf.e_tot:.6f} Hartree')
    print(f'Converged: {mf.converged}')

    print('Selecting active space using AVAS...')
    n_orbitals, n_alpha, n_beta = select_active_space(mf, ao_labels, threshold)
    print(f'Active space: {n_orbitals} orbitals, {n_alpha} alpha electrons, {n_beta} beta electrons')

    print('Building active space Hamiltonian...')
    fermionic_hamiltonian = active_space_hamiltonian(mf, n_alpha, n_beta, n_orbitals)
    hamiltonian_matrix, pauli_hamiltonian = qubit_hamiltonian(fermionic_hamiltonian)
    n_qubits = pauli_hamiltonian.num_qubits
    print(f'Hamiltonian built with {n_qubits} qubits and {len(pauli_hamiltonian)} Pauli terms')

    # --- Quantum part ---
    ansatz = general_ansatz(n_qubits)

    if run_vqe_stage:
        print('Running VQE...')
        optimal_params, vqe_energy, trajectory = run_vqe(
            ansatz, pauli_hamiltonian, backend, optimization_level, shots,
            report_per_job_progress=report_per_job_progress,
            learning_rate=learning_rate,
            perturbation=perturbation,
            max_iters=max_iters,
            is_simulation=is_simulation
        )
        print(f'VQE converged with energy: {vqe_energy:.6f} Hartree')
        print(f'Optimal parameters: {np.array2string(optimal_params, precision=6)}')

        # The trajectory records the points that a gradient was measured around, so its
        # last row is the point of the final iteration and not the point that the final
        # update step led to. That last point is the actual result of the optimization,
        # so it is appended as one more iteration and re-measured with all the others.
        if trajectory:
            trajectory = trajectory + [(optimal_params, vqe_energy)]

        # Re-measure the whole convergence curve with more shots
        # Every iterate is known by now, so they all fit into very few jobs
        if trajectory_file is not None and trajectory:
            print(f'Re-measuring {len(trajectory)} iterates with {replay_shots} shots...')
            groups, const = build_measurement_groups(
                ansatz, pauli_hamiltonian, backend, optimization_level
            )
            replay_energies = replay_trajectory(
                trajectory, groups, const, backend, replay_shots,
                max_circuits_per_job=max_circuits_per_job,
                report_per_job_progress=report_per_job_progress,
                is_simulation=is_simulation
            )
            save_trajectory(trajectory_file, trajectory, replay_energies)
            print(f'Convergence data saved to {trajectory_file}')
    else:
        # The optimization was already run earlier, so its parameters are used as they are
        optimal_params = np.asarray(optimal_params, dtype=float)
        if len(optimal_params) != ansatz.num_parameters:
            raise ValueError(
                f'The ansatz needs {ansatz.num_parameters} parameters but '
                f'{len(optimal_params)} were given. They are probably from a run with a '
                f'different molecule or active space.'
            )
        print(f'Skipping VQE, using the {len(optimal_params)} parameters that were given')

    ground_state_circuit = get_ground_state_circuit(ansatz, optimal_params)

    # --- Classical shadow part ---
    print('Collecting classical shadow snapshots...')
    snapshots = calculate_snapshots(
        N, backend, optimization_level, n_qubits,
        ground_state_circuit, U_list, batch_size=max_circuits_per_job,
        report_per_job_progress=report_per_job_progress, is_simulation=is_simulation
    )

    print('Building classical shadow...')
    classical_shadow = create_pauli_shadow(snapshots)

    print('Estimating ground state energy from classical shadow...')
    energy_estimate = estimate_energy(classical_shadow, pauli_hamiltonian, K)
    print(f'Final energy estimate: {energy_estimate:.6f} Hartree')

    return energy_estimate


def parse_args() -> argparse.Namespace:
    '''
    Parses the command line arguments for the workflow.

    Returns:
        args: The parsed command line arguments
    '''
    parser = argparse.ArgumentParser(
        description='Estimate a molecular ground state energy with VQE and classical shadows.'
    )
    parser.add_argument('--backend', default='SIM', choices=['VLQ', 'SIM'],
                        help='The backend to run the quantum circuits on. Default is VLQ.')
    parser.add_argument('--atom', default='H 0 0 0; H 0 0 0.74',
                        help='Atomic geometry string. Default is the H2 molecule.')
    parser.add_argument('--basis', default='sto-3g',
                        help='Basis set name. Default is sto-3g.')
    parser.add_argument('--spin', type=int, default=0,
                        help='Number of unpaired electrons. Default is 0.')
    parser.add_argument('--ao-labels', nargs='+', default=['H 1s'],
                        help='Atomic orbital labels for AVAS active space selection.')
    parser.add_argument('--optimization-level', type=int, default=1, choices=[0, 1, 2, 3],
                        help='The transpilation optimization level. Default is 1.')
    parser.add_argument('--shots', type=int, default=2**10,
                        help='The number of shots for each circuit evaluation. Default is 10000.')
    parser.add_argument('-N', type=int, default=5000,
                        help='The number of classical shadow snapshots. Default is 10000.')
    parser.add_argument('-K', type=int, default=10,
                        help='The number of groups for the median-of-means estimator. Default is 10.')
    parser.add_argument('--threshold', type=float, default=0.2,
                        help='AVAS threshold for active space selection. Default is 0.2.')
    parser.add_argument('--learning-rate', type=float, default=None,
                        help='The SPSA learning rate. Must be given together with --perturbation. '
                             'If neither is given, SPSA calibrates both automatically, which costs '
                             '50 extra energy evaluations before the first iteration.')
    parser.add_argument('--perturbation', type=float, default=None,
                        help='The SPSA perturbation. Must be given together with --learning-rate.')
    parser.add_argument('--trajectory-file', default='vqe_trajectory.csv',
                        help='The csv file to save the VQE convergence data into. '
                             'Pass an empty string to skip the replay. '
                             "Default is 'vqe_trajectory.csv'.")
    parser.add_argument('--replay-shots', type=int, default=2**12,
                        help='The number of shots used to re-measure the VQE trajectory '
                             'for plotting. Default is 10000.')
    parser.add_argument('--max-circuits-per-job', type=int, default=1000,
                        help='The largest number of circuits to put into a single job when '
                             're-measuring the VQE trajectory. Default is 1000.')
    parser.add_argument('--report-per-job-progress', action='store_true',
                        help='If set, reports progress for each job submitted to the backend.')
    parser.add_argument('--max-iters', type=int, default=40, help='The maximum number of VQE iterations. Default is 40.')
    parser.add_argument('--shadow-only', action='store_true',
                        help='If set, skips VQE and the trajectory replay and runs only the '
                             'classical shadow part, using the parameters read from '
                             '--parameters-file.')
    parser.add_argument('--parameters-file', default=None,
                        help='The trajectory csv file to read the ansatz parameters from when '
                             '--shadow-only is set. Defaults to the value of --trajectory-file.')
    parser.add_argument('--parameters-row', type=int, default=-1,
                        help='Which row of the parameters file to use with --shadow-only, given '
                             'as an iteration number. Default is -1, the last row, which holds '
                             'the parameters the optimization finished on.')
    return parser.parse_args()


# --- Main ---
if __name__ == '__main__':
    # --- Parameters ---
    args = parse_args()

    # --- Load the ansatz parameters when VQE is skipped ---
    optimal_params = None
    if args.shadow_only:
        parameters_file = args.parameters_file or args.trajectory_file
        if not parameters_file:
            raise ValueError(
                '--shadow-only needs a file to read the ansatz parameters from. '
                'Give one with --parameters-file.'
            )
        saved_trajectory = load_trajectory(parameters_file)
        # A row is picked by iteration number, so row 1 is the first iterate and -1 the last
        row = args.parameters_row
        index = row - 1 if row > 0 else len(saved_trajectory) + row
        if not 0 <= index < len(saved_trajectory):
            raise ValueError(
                f'{parameters_file} has {len(saved_trajectory)} iterations, so row {row} '
                f'does not exist.'
            )
        optimal_params = saved_trajectory[index][0]
        print(f'Read {len(optimal_params)} parameters from row {index + 1} of {parameters_file}')

    # --- Run workflow ---
    energy = run_workflow(
        atom=args.atom,
        basis=args.basis,
        spin=args.spin,
        ao_labels=args.ao_labels,
        backend=get_backend(args.backend),
        optimization_level=args.optimization_level,
        shots=args.shots,
        N=args.N,
        K=args.K,
        threshold=args.threshold,
        learning_rate=args.learning_rate,
        perturbation=args.perturbation,
        report_per_job_progress=args.report_per_job_progress,
        trajectory_file=args.trajectory_file or None,
        replay_shots=args.replay_shots,
        max_circuits_per_job=args.max_circuits_per_job,
        max_iters=args.max_iters,
        run_vqe_stage=not args.shadow_only,
        optimal_params=optimal_params,
        is_simulation=(args.backend == 'SIM')
    )
    print(f'Final ground state energy: {energy:.6f} Hartree')
