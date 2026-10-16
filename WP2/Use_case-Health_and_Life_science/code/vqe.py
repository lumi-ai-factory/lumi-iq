# --- Imports ---
from time import sleep

import numpy as np
from typing import Literal
from qiskit import QuantumCircuit, transpile
from qiskit_algorithms.optimizers import SPSA
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp
from qiskit.providers import Backend
from classical_shadow import calculate_expectation_value

# --- Functions ---
def wait_for_user(
        message: str = 'Press Enter to continue...'
        ) -> None:
    '''
    Pauses execution until the user allows the run to continue.

    Args:
        message: The prompt that is shown to the user
    '''
    try:
        input(message)
    except EOFError:
        # No interactive stdin available, so continue without waiting
        print(f'{message} (stdin not interactive, continuing)')


def general_ansatz(
        num_qubits: int
        ) -> QuantumCircuit:
    '''
    Creates a general ansatz circuit for VQE using EfficientSU2.

    Args:
        num_qubits: Number of qubits needed for the ansatz circuit

    Returns:
        ansatz: The ansatz circuit
    '''
    # Create the ansatz circuit using EfficientSU2
    ansatz = EfficientSU2(num_qubits, reps=1)
    
    # Returns the ansatz circuit
    return ansatz

def pauli_measurement_layout(
        pauli_hamiltonian: SparsePauliOp
        ) -> tuple[list[tuple[list[str], list[tuple[int, float]]]], float]:
    '''
    Works out which measurement basis each group of commuting Pauli terms needs and
    which terms are read out of that measurement.

    This is the part of the measurement grouping that does not involve any circuit, so
    it can be redone later without a backend, for example when the counts of an already
    finished job are decoded. The grouping is deterministic for a given Hamiltonian, so
    repeating this call gives the groups back in the same order.

    Args:
        pauli_hamiltonian: The Hamiltonian expressed as a sum of Pauli operators
    Returns:
        layout: A list of tuples, where each tuple contains the measurement basis of one group as a list of Pauli letters and a list of tuples with the mask and coefficient for each Pauli term in that group
        const: The constant term in the Hamiltonian that does not require any circuit to be run
    '''
    layout, const = [], 0.0
    for group in pauli_hamiltonian.group_commuting(qubit_wise=True):
        n = group.num_qubits
        basis = ['I'] * n
        terms = []
        for pauli, coeff in zip(group.paulis, group.coeffs):
            mask = 0
            for q in range(n):
                letter = str(pauli[q])        # pauli[q] IS qubit q
                if letter == 'I':
                    continue
                basis[q] = letter             # qubit-wise commuting => no conflict here
                mask |= 1 << q
            if mask == 0:
                const += complex(coeff).real  # identity: needs no circuit at all
            else:
                terms.append((mask, complex(coeff).real))
        if not terms:
            continue
        layout.append((basis, terms))
    return layout, const


def build_measurement_groups(
        ansatz: QuantumCircuit,
        pauli_hamiltonian: SparsePauliOp,
        backend: Backend,
        optimization_level: Literal[0, 1, 2, 3]
        ) -> tuple[list[tuple[QuantumCircuit, list[tuple[int, float]]]], float]:
    '''
    Builds measurement groups for the Pauli operators in the Hamiltonian.
    Condenses the number of circuits that need to be run by grouping commuting Pauli operators together
    and measuring them in the same basis. Hence one does not need to run a separate circuit for each Pauli term
    but one circuit for each group of commuting Pauli terms.

    Args:
        ansatz: The ansatz circuit that is used in the VQE
        pauli_hamiltonian: The Hamiltonian expressed as a sum of Pauli operators
        backend: The backend that should be used to run the ansatz circuit
        optimization_level: The optimization level that should be used. Options are 0-3.
    Returns:
        groups: A list of tuples, where each tuple contains a transpiled circuit and a list of tuples with the mask and coefficient for each Pauli term in that group
        const: The constant term in the Hamiltonian that does not require any circuit to be run
    '''
    layout, const = pauli_measurement_layout(pauli_hamiltonian)

    groups = []
    for basis, terms in layout:
        circuit = ansatz.copy()               # still parameterized
        for q, letter in enumerate(basis):
            if letter == 'X':
                circuit.h(q)
            elif letter == 'Y':
                circuit.sdg(q)
                circuit.h(q)
        circuit.measure_all()
        groups.append((transpile(circuit, backend, optimization_level=optimization_level), terms))
    return groups, const


def energies_from_counts(
        counts_list: list[dict[str, int]] | dict[str, int],
        terms_per_group: list[list[tuple[int, float]]],
        const: float,
        shots: int | None = None
        ) -> list[float]:
    '''
    Decodes the counts of a finished job into one energy per parameter set.

    The circuits of one parameter set form a contiguous block of one circuit per
    measurement group, so the counts are read one block at a time.

    Args:
        counts_list: The counts of every circuit of the job, in submission order
        terms_per_group: A list of the term lists of the measurement groups, in the same order as the circuits were submitted
        const: The constant term in the Hamiltonian that does not require any circuit to be run
        shots: The number of shots each circuit was run with. If None, the number is
            taken from the counts themselves. Default is None.
    Returns:
        energies: The energy of each parameter set in Hartree units, in submission order
    '''
    # get_counts returns a bare dict instead of a list when only one circuit was run
    if isinstance(counts_list, dict):
        counts_list = [counts_list]

    num_groups = len(terms_per_group)
    if num_groups == 0:
        raise ValueError('There are no measurement groups to decode the counts with.')
    if len(counts_list) % num_groups != 0:
        raise ValueError(
            f'Got counts for {len(counts_list)} circuits, which is not a whole number of '
            f'parameter sets of {num_groups} circuits each.'
        )

    energies = []
    for index in range(len(counts_list) // num_groups):
        counts_block = counts_list[index * num_groups:(index + 1) * num_groups]
        energy = const
        for terms, counts in zip(terms_per_group, counts_block):
            total = shots if shots is not None else sum(counts.values())
            for mask, coeff in terms:
                acc = 0
                for bit_string, n in counts.items():
                    bits = int(bit_string.replace(' ', ''), 2)
                    acc += n if (bits & mask).bit_count() % 2 == 0 else -n
                energy += coeff * acc / total
        energies.append(energy)
    return energies


def is_job_done(job) -> bool:
    """Helper to check if a quantum job reached terminal state across Qiskit and QaaS backends."""
    if hasattr(job, "in_final_state"):
        try:
            return bool(job.in_final_state())
        except Exception:
            pass
    if hasattr(job, "is_final_state"):
        try:
            return bool(job.is_final_state())
        except Exception:
            pass
    if hasattr(job, "status"):
        try:
            st = str(job.status()).upper()
            return any(term in st for term in ["DONE", "COMPLETED", "ERROR", "CANCEL", "FAIL"])
        except Exception:
            pass
    return False


def evaluate_energy(
        parameters: np.ndarray, 
        groups: list[tuple[QuantumCircuit, list[tuple[int, float]]]],
        const: float,
        backend: Backend, 
        shots: int,
        report_per_job_progress: bool = False,
        is_simulation: bool = False
        ) -> float | np.ndarray:
    '''
    Evaluates the energy of the ansatz circuit with given parameters.

    A batch of parameter sets can be given as a 2D array of shape (number of parameter
    sets, number of parameters). All of the circuits are then submitted as a single job
    and an array of energies is returned, one energy per parameter set. This lets the
    optimizer evaluate several points with one job instead of one job per point.

    Args:
        parameters: The parameters that are used in the ansatz circuit, either a single
            parameter set as a 1D array or a batch of parameter sets as a 2D array
        groups: A list of tuples, where each tuple contains a transpiled circuit and a list of tuples with the mask and coefficient for each Pauli term in that group
        const: The constant term in the Hamiltonian that does not require any circuit to be run
        backend: The backend that should be used to run the ansatz circuit
        shots: The number of times the quantum circuit is executed
        report_per_job_progress: If True, prints the id of every job that is submitted
        is_simulation: If True, the job is not polled for its status, because a local
            simulator has finished by the time its result is asked for and its jobs do
            not have the polling interface that remote backend jobs have. Default is False.
    Returns:
        energy: The energy of the ansatz circuit with the given parameters in Hartree units.
            A float for a single parameter set, an array of floats for a batch.
    '''
    # Treat a single parameter set as a batch of one so that both cases share one code path
    points = np.atleast_2d(parameters)

    # Bind every parameter set to every group circuit and submit them all as one job
    bound = [circuit.assign_parameters(point) for point in points for circuit, _ in groups]
    job = backend.run(bound, shots=shots)
    if report_per_job_progress:
        print(f'Job {job.job_id()} submitted to backend {backend.name}')

    time_taken = 0
    if not is_simulation:
        while not is_job_done(job):
            sleep(2)
            time_taken += 2
            if time_taken % 30 == 0:
                status_str = job.status() if hasattr(job, "status") else "RUNNING"
                print(f'Job {job.job_id()} is still running after {time_taken} seconds... (status: {status_str})')
            if time_taken > 1800:
                print(f'Warning: Job {job.job_id()} exceeded timeout (30m). Calling result().')
                break

    # Decode the counts of each parameter set separately
    counts_list = job.result().get_counts()
    energies = energies_from_counts(
        counts_list, [terms for _, terms in groups], const, shots
    )

    # Return an array for a batch and a single float for a single parameter set
    if np.ndim(parameters) == 2:
        return np.array(energies)
    return energies[0]


def run_vqe(
        ansatz: QuantumCircuit, 
        pauli_hamiltonian: SparsePauliOp, 
        backend: Backend, 
        optimization_level: Literal[0, 1, 2, 3],
        shots: int,
        report_per_job_progress: bool = False,
        learning_rate: float | None = None,
        perturbation: float | None = None,
        max_iters: int = 40,
        is_simulation: bool = False
        ) -> tuple[np.ndarray, float, list[tuple[np.ndarray, float]]]:
    '''
    Runs the VQE algorithm.

    Args:
        ansatz: The ansatz circuit that should be used in the VQE
        pauli_hamiltonian: The Hamiltonian expressed as a sum of Pauli operators
        backend: The backend to run the circuit on
        optimization_level: The optimization level that should be used. Options are 0-3.
        shots: The number of shots for each circuit evaluation
        report_per_job_progress: If True, prints the id of every job that is submitted
        is_simulation: If True, jobs are not polled for their status. Set it for a local
            simulator backend. Default is False.
        learning_rate: The SPSA learning rate. Must be given together with perturbation.
            If both are left as None, SPSA calibrates them automatically, which costs
            50 extra energy evaluations before the first iteration. Default is None.
        perturbation: The SPSA perturbation. Must be given together with learning_rate.
            Default is None.
    Returns:
        optimal_params: The optimal parameters for the ansatz circuit
        ground_state_energy: The estimated ground state energy in Hartree units
        trajectory: A list of (parameters, energy) pairs, one per SPSA iteration. The
            parameters are the exact iterate and the energy is the mean of the two
            gradient probe energies, which estimates the energy at that iterate.
    '''
    # SPSA calibrates the learning rate and the perturbation itself only when it is given
    # neither of them, so giving just one of the two is not allowed
    if (learning_rate is None) != (perturbation is None):
        raise ValueError(
            'learning_rate and perturbation must either both be given or both be left unset. '
            f'Got learning_rate={learning_rate}, perturbation={perturbation}.'
        )

    # Get the number of parameters needed from the ansatz circuit
    num_params = ansatz.num_parameters
    
    # Create the initial parameters
    # Each value is randomly chosen from the interval [0, 2*pi)
    initial_parameters = np.random.uniform(0, 2*np.pi, num_params) 

    # Build the measurement group circuits once, they do not depend on the parameters
    groups, const = build_measurement_groups(ansatz, pauli_hamiltonian, backend, optimization_level)

    # For recording how the energy values are progressing
    trajectory = []
    # Calibration evaluates the objective at the initial point only, so its evaluations
    # are counted and reported separately from the actual optimization iterations
    calibration_steps = [0]
    recording_iterations = [False]

    # Define the objective for minimize
    # The objective should be to find the minimum energy
    def objective_function(parameters):
        parameters = np.asarray(parameters)
        energy = evaluate_energy(parameters, groups, const, backend, shots, report_per_job_progress, is_simulation)
        # SPSA probes symmetrically at x + c*delta and x - c*delta, so the midpoint of a
        # pair of probe points is exactly the current iterate and the mean of their two
        # energies estimates the energy at that iterate. Recording them here means no
        # extra job has to be run just to follow the progress of the optimization.
        if parameters.ndim == 2 and len(parameters) == 2:
            estimate = float(np.mean(energy))
            if recording_iterations[0]:
                trajectory.append((parameters.mean(axis=0), estimate))
                print(f"Iteration {len(trajectory)}: energy = {estimate}")
            else:
                calibration_steps[0] += 1
                print(f"Calibration step {calibration_steps[0]}: energy = {estimate}")
        return energy

    
    if learning_rate is None and perturbation is None:
        print('Calibrating the SPSA learning rate and perturbation...')
        learning_rate, perturbation = SPSA.calibrate(
            objective_function, initial_parameters, max_evals_grouped=2
        )
        print(f'Calibration done after {calibration_steps[0]} steps')
        initial_learning_rate = next(learning_rate())
        initial_perturbation = next(perturbation())
        print(
            f'Calibrated learning rate: {initial_learning_rate}, '
            f'perturbation: {initial_perturbation}'
        )

    # Every evaluation from here on belongs to an optimization iteration
    recording_iterations[0] = True

    # Find the minimized result
    # No callback is used because SPSA evaluates the objective one extra time per
    # iteration to produce the energy value that it passes to a callback
    spsa = SPSA(
        maxiter=max_iters,
        learning_rate=learning_rate,
        perturbation=perturbation
    )
    # Let SPSA hand both gradient evaluations of an iteration to the objective at once
    # so that they are submitted as a single job instead of two
    spsa.set_max_evals_grouped(2)
    result = spsa.minimize(objective_function, initial_parameters)
    optimal_params = result.x
    ground_state_energy = float(result.fun)

    # Get the optimal parameters and the corresponding ground state energy
    optimal_params = result.x
    ground_state_energy = float(result.fun)

    # Return the optimal parameters, the ground state energy and the trajectory
    return optimal_params, ground_state_energy, trajectory


def replay_trajectory(
        trajectory: list[tuple[np.ndarray, float]],
        groups: list[tuple[QuantumCircuit, list[tuple[int, float]]]],
        const: float,
        backend: Backend,
        shots: int,
        max_circuits_per_job: int = 1000,
        report_per_job_progress: bool = False,
        is_simulation: bool = False
        ) -> np.ndarray:
    '''
    Re-measures the energy of every parameter set along an optimization trajectory.

    The energies that are recorded while the optimizer runs are noisy, because a low
    number of shots is enough to point the optimizer in the right direction. This
    function measures the same parameter sets again with a higher number of shots so
    that the convergence can be plotted. Every parameter set is known by the time the
    optimization has finished, so they can be measured together: as many of them as fit
    within max_circuits_per_job circuits are submitted as a single job. This keeps the
    number of jobs low, which is what costs time on a queued backend.

    Args:
        trajectory: A list of (parameters, energy) pairs as returned by run_vqe
        groups: A list of tuples, where each tuple contains a transpiled circuit and a list of tuples with the mask and coefficient for each Pauli term in that group
        const: The constant term in the Hamiltonian that does not require any circuit to be run
        backend: The backend to run the circuits on
        shots: The number of shots to use for each circuit
        max_circuits_per_job: The largest number of circuits to put into a single job.
            Default is 1000.
        report_per_job_progress: If True, prints the id of every job that is submitted
        is_simulation: If True, jobs are not polled for their status. Set it for a local
            simulator backend. Default is False.
    Returns:
        energies: The re-measured energy of each parameter set, in trajectory order
    '''
    # Each parameter set needs one circuit per measurement group
    circuits_per_point = len(groups)
    if circuits_per_point > max_circuits_per_job:
        raise ValueError(
            f'A single parameter set needs {circuits_per_point} circuits, which does not fit '
            f'into a job of at most {max_circuits_per_job} circuits.'
        )
    if not trajectory:
        return np.array([])

    # Work out how many parameter sets fit into one job
    points_per_job = max_circuits_per_job // circuits_per_point
    parameters = np.array([iterate for iterate, _ in trajectory])

    # Measure the parameter sets in as few jobs as the circuit limit allows
    energies = []
    for start in range(0, len(parameters), points_per_job):
        chunk = parameters[start:start + points_per_job]
        chunk_energies = evaluate_energy(
            chunk, groups, const, backend, shots, report_per_job_progress, is_simulation
        )
        energies.extend(np.atleast_1d(chunk_energies).tolist())

    # Return the re-measured energies
    return np.array(energies)


def save_trajectory(
        path: str,
        trajectory: list[tuple[np.ndarray, float]],
        replay_energies: np.ndarray
        ) -> None:
    '''
    Saves an optimization trajectory and its re-measured energies as a csv file.

    One row is written per iteration. The columns are the iteration number, the noisy
    energy that was recorded while the optimizer ran, the re-measured energy from
    replay_trajectory, and the parameters of that iterate.

    Args:
        path: The path of the csv file to write
        trajectory: A list of (parameters, energy) pairs as returned by run_vqe
        replay_energies: The re-measured energies as returned by replay_trajectory
    '''
    if len(replay_energies) != len(trajectory):
        raise ValueError(
            f'Got {len(trajectory)} iterations but {len(replay_energies)} replayed energies.'
        )

    # Build the header from the number of parameters of the first iterate
    num_params = len(trajectory[0][0]) if trajectory else 0
    header = ['iteration', 'live_energy', 'replay_energy']
    header += [f'parameter_{i}' for i in range(num_params)]

    # Write one row per iteration
    with open(path, 'w') as csv_file:
        csv_file.write(','.join(header) + chr(10))
        for index, ((iterate, live_energy), replay_energy) in enumerate(
                zip(trajectory, replay_energies), start=1):
            values = [str(index), repr(float(live_energy)), repr(float(replay_energy))]
            values += [repr(float(value)) for value in iterate]
            csv_file.write(','.join(values) + chr(10))


def load_trajectory(
        path: str
        ) -> list[tuple[np.ndarray, float]]:
    '''
    Reads back a trajectory that was written by save_trajectory.

    Args:
        path: The path of the csv file to read
    Returns:
        trajectory: A list of (parameters, energy) pairs in the same form as the one
            returned by run_vqe. The energy is the live energy column of the file.
    '''
    with open(path) as csv_file:
        rows = [line.strip() for line in csv_file if line.strip()]

    if len(rows) < 2:
        raise ValueError(f'The file {path} contains no trajectory rows.')

    header = rows[0].split(',')
    parameter_columns = [i for i, name in enumerate(header) if name.startswith('parameter_')]
    if not parameter_columns:
        raise ValueError(f'The file {path} has no parameter columns.')
    live_energy_column = header.index('live_energy') if 'live_energy' in header else None

    trajectory = []
    for row in rows[1:]:
        values = row.split(',')
        iterate = np.array([float(values[i]) for i in parameter_columns])
        live_energy = float(values[live_energy_column]) if live_energy_column is not None else float('nan')
        trajectory.append((iterate, live_energy))
    return trajectory


def get_ground_state_circuit(
        ansatz: QuantumCircuit, 
        optimal_parameters: np.ndarray
        ) -> QuantumCircuit:
    '''
    Builds the ground state circuit by binding the optimal parameters from VQE to the ansatz circuit.

    Args:
        ansatz: The parameterized quantum circuit
        optimal_parameters: The optimal parameters found by VQE
    Returns:
        ground_state_circuit: A quantum circuit for creating the ground state
    '''

    # Create a quantum circuit with the optimal parameters
    ground_state_circuit = ansatz.assign_parameters(optimal_parameters)

    # Return the quantum circuit
    return ground_state_circuit


def estimate_energy(
        classical_shadow: list[np.ndarray], 
        pauli_hamiltonian: SparsePauliOp, 
        k: int
        ) -> float:
    '''
    Estimates the ground state energy from a classical shadow. 
    This is done by calculating the expectation value of each Pauli term in the provided Hamiltonian.

    Args:
        classical_shadow: The classical shadow
        pauli_hamiltonian: The Hamiltonian expressed as a sum of Pauli operators
        k: Number of groups for the median of means
    Returns:
        energy_estimate: The estimated ground state energy
    '''
    # Initialize the energy to be zero
    energy_estimate = 0.0

    # Loop over every Pauli term
    for pauli, coeff in zip(pauli_hamiltonian.paulis, pauli_hamiltonian.coeffs):
        # Skip identity terms as they contribute a constant
        if all(p == 'I' for p in pauli.to_label()):
            energy_estimate += np.real(coeff)
            continue
        # Build the matrix representation of the Pauli operator
        pauli_matrix = pauli.to_matrix()
        # Calculate the expectation value using the classical shadow
        exp_val = calculate_expectation_value(pauli_matrix, classical_shadow, k)
        # Add the contribution of this Pauli term to the energy
        energy_estimate += np.real(coeff * exp_val)

    # Return the estimated ground state energy
    return float(energy_estimate)
